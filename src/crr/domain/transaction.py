"""Canonical Transaction domain contract.

A Transaction binds an active Agreement to fully allocated Reservations.
It records commercial commitment only; it is not an execution or verification record.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity


class TransactionStatus(StrEnum):
    COMMITTED = "COMMITTED"
    DISPUTED = "DISPUTED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True)
class Transaction:
    """Immutable-at-creation snapshot binding an Agreement to its allocations."""

    id: str
    organization_id: str
    agreement_id: str
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

    def __post_init__(self) -> None:
        required = (
            self.id,
            self.organization_id,
            self.agreement_id,
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

    def validate_tenant(self, organization_id: str) -> None:
        if self.organization_id != organization_id:
            raise TenantBoundaryError("Transaction belongs to another organization.")
