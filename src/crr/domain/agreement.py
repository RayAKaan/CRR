"""Canonical Agreement domain contract.

An Agreement is the immutable commercial record produced after an Offer is accepted.
It is not a reservation, transaction, payment, or execution record.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
import json

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.offer import Offer, OfferStatus


class AgreementStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"


@dataclass(frozen=True, slots=True)
class Agreement:
    """Immutable-at-creation snapshot of accepted Offer terms."""

    id: str
    organization_id: str
    offer_id: str
    offer_version: int
    proposer_actor_id: str
    recipient_actor_id: str
    accepted_by: str
    accepted_at: datetime
    terms_snapshot: str
    status: AgreementStatus
    version: int
    created_at: datetime
    updated_at: datetime
    provenance: str

    def __post_init__(self) -> None:
        required = (
            self.id,
            self.organization_id,
            self.offer_id,
            self.proposer_actor_id,
            self.recipient_actor_id,
            self.accepted_by,
            self.terms_snapshot,
            self.provenance,
        )
        if any(not value for value in required):
            raise DomainError("Agreement identity, parties, terms, and provenance are required.")
        if self.offer_version < 1 or self.version < 1:
            raise DomainError("Agreement Offer and object versions must be positive.")
        if self.proposer_actor_id == self.recipient_actor_id:
            raise DomainError("Agreement parties must be distinct actors.")
        if self.accepted_by != self.recipient_actor_id:
            raise DomainError("Only the Offer recipient may accept the Offer.")
        for value in (self.accepted_at, self.created_at, self.updated_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise DomainError("Agreement timestamps must be timezone-aware.")
        try:
            decoded = json.loads(self.terms_snapshot)
        except (TypeError, ValueError) as exc:
            raise DomainError("Agreement terms snapshot must be valid JSON.") from exc
        if not isinstance(decoded, dict) or not decoded:
            raise DomainError("Agreement terms snapshot must be a non-empty JSON object.")

    @classmethod
    def from_accepted_offer(
        cls,
        offer: Offer,
        *,
        agreement_id: str,
        accepted_by: str,
        accepted_at: datetime,
        provenance: str,
    ) -> Agreement:
        """Capture the exact accepted Offer terms without mutating the Offer."""
        if offer.status is not OfferStatus.ACCEPTED:
            raise DomainError("An Agreement can only be created from an accepted Offer.")
        if accepted_by != offer.recipient_actor_id:
            raise DomainError("Only the Offer recipient may accept the Offer.")
        if accepted_at.tzinfo is None or accepted_at.utcoffset() is None:
            raise DomainError("Agreement acceptance time must be timezone-aware.")
        terms = {
            "quantity": {
                "value": str(offer.quantity.value),
                "unit": offer.quantity.unit,
                "unit_registry_version": offer.quantity.unit_registry_version,
            },
            "price": str(offer.price),
            "currency": offer.currency,
            "delivery_terms": offer.delivery_terms,
            "timing_terms": offer.timing_terms,
            "route_assumptions": offer.route_assumptions,
            "conditions": offer.conditions,
            "valid_from": offer.valid_from.isoformat(),
            "valid_until": offer.valid_until.isoformat(),
        }
        snapshot = json.dumps(terms, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return cls(
            id=agreement_id,
            organization_id=offer.organization_id,
            offer_id=offer.id,
            offer_version=offer.version,
            proposer_actor_id=offer.proposer_actor_id,
            recipient_actor_id=offer.recipient_actor_id,
            accepted_by=accepted_by,
            accepted_at=accepted_at,
            terms_snapshot=snapshot,
            status=AgreementStatus.ACTIVE,
            version=1,
            created_at=accepted_at,
            updated_at=accepted_at,
            provenance=provenance,
        )

    def validate_tenant(self, organization_id: str) -> None:
        if self.organization_id != organization_id:
            raise TenantBoundaryError("Agreement belongs to another organization.")

    def cancel(self, *, actor_id: str, at: datetime) -> Agreement:
        if self.status is not AgreementStatus.ACTIVE:
            raise DomainError("Only an active Agreement can be cancelled.")
        if actor_id not in {self.proposer_actor_id, self.recipient_actor_id}:
            raise DomainError("Agreement cancellation requires a participating actor.")
        if at.tzinfo is None or at.utcoffset() is None:
            raise DomainError("Agreement cancellation time must be timezone-aware.")
        from dataclasses import replace

        return replace(self, status=AgreementStatus.CANCELLED, version=self.version + 1, updated_at=at)
