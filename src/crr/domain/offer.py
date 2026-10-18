"""Commercial Offer domain contracts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity


class OfferStatus(StrEnum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    WITHDRAWN = "WITHDRAWN"


_ALLOWED_TRANSITIONS: dict[OfferStatus, frozenset[OfferStatus]] = {
    OfferStatus.DRAFT: frozenset({OfferStatus.OPEN, OfferStatus.WITHDRAWN}),
    OfferStatus.OPEN: frozenset(
        {
            OfferStatus.ACCEPTED,
            OfferStatus.REJECTED,
            OfferStatus.EXPIRED,
            OfferStatus.WITHDRAWN,
        }
    ),
    OfferStatus.ACCEPTED: frozenset(),
    OfferStatus.REJECTED: frozenset(),
    OfferStatus.EXPIRED: frozenset(),
    OfferStatus.WITHDRAWN: frozenset(),
}


@dataclass(frozen=True, slots=True)
class Offer:
    """A proposed commercial term set; never acceptance or execution truth."""

    id: str
    organization_id: str
    opportunity_id: str
    opportunity_version: int
    proposer_actor_id: str
    recipient_actor_id: str
    quantity: Quantity
    price: Decimal
    currency: str
    delivery_terms: dict[str, Any]
    timing_terms: dict[str, Any]
    route_assumptions: dict[str, Any]
    conditions: dict[str, Any]
    valid_from: datetime
    valid_until: datetime
    status: OfferStatus
    version: int
    created_by: str
    provenance: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.id or not self.organization_id or not self.opportunity_id:
            raise DomainError("Offer identity, organization, and Opportunity are required.")
        if self.opportunity_version < 1:
            raise DomainError("Offer Opportunity version must be positive.")
        if not self.proposer_actor_id or not self.recipient_actor_id:
            raise DomainError("Offer proposer and recipient are required.")
        if self.price < Decimal("0"):
            raise DomainError("Offer price cannot be negative.")
        if len(self.currency) != 3 or self.currency.upper() != self.currency:
            raise DomainError("Offer currency must be a three-letter uppercase code.")
        if self.valid_from.tzinfo is None or self.valid_from.utcoffset() is None:
            raise DomainError("Offer valid_from must be timezone-aware.")
        if self.valid_until.tzinfo is None or self.valid_until.utcoffset() is None:
            raise DomainError("Offer valid_until must be timezone-aware.")
        if self.valid_from >= self.valid_until:
            raise DomainError("Offer validity window must have valid_from before valid_until.")
        if self.version < 1:
            raise DomainError("Offer version must be positive.")
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise DomainError("Offer timestamps must be timezone-aware.")
        if not self.delivery_terms or not self.timing_terms:
            raise DomainError("Offer delivery and timing terms are required.")
        if not self.route_assumptions:
            raise DomainError("Offer route assumptions are required.")
        if not self.provenance:
            raise DomainError("Offer provenance is required.")

    def transition(self, new_status: OfferStatus) -> Offer:
        if new_status not in _ALLOWED_TRANSITIONS[self.status]:
            raise DomainError(
                f"Invalid Offer transition: {self.status.value} -> {new_status.value}."
            )
        return replace(
            self,
            status=new_status,
            version=self.version + 1,
            updated_at=datetime.now(self.updated_at.tzinfo),
        )

    def validate_tenant(self, organization_id: str) -> None:
        if self.organization_id != organization_id:
            raise TenantBoundaryError("Offer belongs to another organization.")

    def assert_not_expired(self, now: datetime) -> None:
        if now.tzinfo is None or now.utcoffset() is None:
            raise DomainError("Offer freshness checks require timezone-aware time.")
        if now >= self.valid_until:
            raise DomainError("Offer validity window has expired.")
