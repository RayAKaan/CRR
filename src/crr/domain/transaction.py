"""Canonical Transaction domain contract.

A Transaction binds an active Agreement to fully allocated Reservations.
It records commercial commitment only; it is not an execution or verification record.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity
from crr.domain.reservation import Reservation, ReservationStatus


class TransactionStatus(StrEnum):
    AGREED = "AGREED"
    SCHEDULED = "SCHEDULED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class Transaction:
    """Immutable-at-creation snapshot binding an Agreement to its allocations."""

    id: str
    organization_id: str
    agreement_id: str
    opportunity_id: str
    route_candidate_id: str
    resource_id: str
    resource_state_id: str
    resource_version: int
    proposer_actor_id: str
    recipient_actor_id: str
    quantity: Quantity
    price: Decimal
    currency: str
    terms_snapshot: str
    reservation_ids: tuple[str, ...]
    status: TransactionStatus
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    provenance: dict[str, str]
    scheduled_for: datetime | None = None

    def __post_init__(self) -> None:
        required = (
            self.id,
            self.organization_id,
            self.agreement_id,
            self.opportunity_id,
            self.route_candidate_id,
            self.resource_id,
            self.resource_state_id,
            self.proposer_actor_id,
            self.recipient_actor_id,
            self.created_by,
        )
        if any(not value for value in required):
            raise DomainError("Transaction identity, parties, and source references are required.")
        if self.proposer_actor_id == self.recipient_actor_id:
            raise DomainError("Transaction parties must be distinct.")
        if self.resource_version < 1 or self.version < 1:
            raise DomainError("Transaction resource and object versions must be positive.")
        if self.quantity.value <= Decimal("0"):
            raise DomainError("Transaction quantity must be greater than zero.")
        if self.price < Decimal("0"):
            raise DomainError("Transaction price cannot be negative.")
        if len(self.currency) != 3 or self.currency.upper() != self.currency:
            raise DomainError("Transaction currency must be a three-letter uppercase code.")
        if not self.reservation_ids or any(not item for item in self.reservation_ids):
            raise DomainError("Transaction requires at least one Reservation.")
        if len(set(self.reservation_ids)) != len(self.reservation_ids):
            raise DomainError("Transaction Reservation references must be unique.")
        if not self.terms_snapshot or not self.provenance:
            raise DomainError("Transaction terms snapshot and provenance are required.")
        try:
            terms = json.loads(self.terms_snapshot)
        except (TypeError, ValueError) as exc:
            raise DomainError("Transaction terms snapshot must be valid JSON.") from exc
        if not isinstance(terms, dict) or not terms:
            raise DomainError("Transaction terms snapshot must be a non-empty JSON object.")
        for value in (self.created_at, self.updated_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise DomainError("Transaction timestamps must be timezone-aware.")
        if self.updated_at < self.created_at:
            raise DomainError("Transaction update time cannot precede creation.")
        if self.scheduled_for is not None and (
            self.scheduled_for.tzinfo is None or self.scheduled_for.utcoffset() is None
        ):
            raise DomainError("Transaction scheduled_for must be timezone-aware.")
        if self.status is TransactionStatus.SCHEDULED and self.scheduled_for is None:
            raise DomainError("A scheduled Transaction requires a planned schedule instant.")

    def validate_tenant(self, organization_id: str) -> None:
        if self.organization_id != organization_id:
            raise TenantBoundaryError("Transaction belongs to another organization.")


    def schedule(
        self,
        *,
        actor_id: str,
        at: datetime,
        scheduled_for: datetime,
    ) -> Transaction:
        self._require_participant(actor_id)
        self._require_transition_time(at)
        if self.status is not TransactionStatus.AGREED:
            raise DomainError("Only an AGREED Transaction can be scheduled.")
        if scheduled_for.tzinfo is None or scheduled_for.utcoffset() is None:
            raise DomainError("Transaction schedule time must be timezone-aware.")
        if scheduled_for <= at:
            raise DomainError("Transaction must be scheduled for a future instant.")
        return self._changed(
            TransactionStatus.SCHEDULED,
            actor_id=actor_id,
            at=at,
            details={"scheduled_for": scheduled_for.isoformat()},
            scheduled_for=scheduled_for,
        )

    def dispute(self, *, actor_id: str, at: datetime, reason: str) -> Transaction:
        self._require_participant(actor_id)
        self._require_transition_time(at)
        if self.status not in {TransactionStatus.AGREED, TransactionStatus.SCHEDULED}:
            raise DomainError("Only an AGREED or SCHEDULED Transaction can be disputed.")
        if not reason.strip():
            raise DomainError("A dispute reason is required.")
        return self._changed(
            TransactionStatus.DISPUTED,
            actor_id=actor_id,
            at=at,
            details={"dispute_reason": reason.strip()},
        )

    def resolve(
        self,
        *,
        actor_id: str,
        at: datetime,
        scheduled_for: datetime,
        resolution_note: str,
    ) -> Transaction:
        self._require_transition_time(at)
        if self.status is not TransactionStatus.DISPUTED:
            raise DomainError("Only a DISPUTED Transaction can be resolved.")
        if not actor_id or not resolution_note.strip():
            raise DomainError("Transaction resolution requires an actor and resolution note.")
        if scheduled_for.tzinfo is None or scheduled_for.utcoffset() is None:
            raise DomainError("Resolved Transaction schedule must be timezone-aware.")
        if scheduled_for <= at:
            raise DomainError("Resolved Transaction must be scheduled for a future instant.")
        return self._changed(
            TransactionStatus.SCHEDULED,
            actor_id=actor_id,
            at=at,
            details={"resolution_note": resolution_note.strip()},
            scheduled_for=scheduled_for,
        )

    def cancel(self, *, actor_id: str, at: datetime, reason: str) -> Transaction:
        self._require_participant(actor_id)
        self._require_transition_time(at)
        if self.status not in {
            TransactionStatus.AGREED,
            TransactionStatus.SCHEDULED,
            TransactionStatus.DISPUTED,
        }:
            raise DomainError("Transaction is already in a terminal state.")
        if not reason.strip():
            raise DomainError("A cancellation reason is required.")
        return self._changed(
            TransactionStatus.CANCELLED,
            actor_id=actor_id,
            at=at,
            details={"cancellation_reason": reason.strip()},
        )

    def _require_participant(self, actor_id: str) -> None:
        if actor_id not in {self.proposer_actor_id, self.recipient_actor_id}:
            raise DomainError("Transaction lifecycle changes require a participating actor.")

    def _require_transition_time(self, at: datetime) -> None:
        if at.tzinfo is None or at.utcoffset() is None:
            raise DomainError("Transaction lifecycle timestamps must be timezone-aware.")
        if at < self.updated_at:
            raise DomainError("Transaction transition time cannot precede its previous update.")

    def _changed(
        self,
        status: TransactionStatus,
        *,
        actor_id: str,
        at: datetime,
        details: dict[str, str],
        scheduled_for: datetime | None = None,
    ) -> Transaction:
        return replace(
            self,
            status=status,
            version=self.version + 1,
            updated_at=at,
            scheduled_for=scheduled_for if scheduled_for is not None else self.scheduled_for,
            provenance={
                **self.provenance,
                "last_transition": status.value,
                "last_transition_actor_id": actor_id,
                "last_transition_at": at.isoformat(),
                **details,
            },
        )


def validate_transaction_reservation_coverage(
    *,
    organization_id: str,
    agreement_id: str,
    resource_id: str,
    resource_state_id: str,
    resource_version: int,
    agreement_status: str,
    agreed_quantity: Quantity,
    reservations: list[Reservation] | tuple[Reservation, ...],
    now: datetime,
) -> None:
    """Require complete, active and mutually consistent Reservation coverage."""
    if now.tzinfo is None or now.utcoffset() is None:
        raise DomainError("Transaction allocation checks require timezone-aware time.")
    if agreement_status != "ACTIVE":
        raise DomainError("Transaction creation requires an active Agreement.")
    if not reservations:
        raise DomainError("Transaction creation requires at least one Reservation.")
    total = Decimal("0")
    seen: set[str] = set()
    for reservation in reservations:
        if reservation.id in seen:
            raise DomainError("Transaction Reservation references must be unique.")
        seen.add(reservation.id)
        if (
            reservation.organization_id != organization_id
            or reservation.agreement_id != agreement_id
            or reservation.resource_id != resource_id
            or reservation.resource_state_id != resource_state_id
            or reservation.resource_version != resource_version
        ):
            raise DomainError("Transaction Reservations must share the same canonical source.")
        if (
            reservation.status is not ReservationStatus.ACTIVE
            or reservation.expires_at <= now
            or reservation.created_at > now
        ):
            raise DomainError("Every Transaction Reservation must be active and unexpired.")
        if (
            reservation.quantity.unit != agreed_quantity.unit
            or reservation.quantity.unit_registry_version != agreed_quantity.unit_registry_version
        ):
            raise DomainError("Transaction Reservations must use the agreed canonical unit.")
        total += reservation.quantity.value
    if total != agreed_quantity.value:
        raise DomainError("Active Reservation quantity must exactly cover the Agreement quantity.")
