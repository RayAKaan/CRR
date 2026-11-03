"""Canonical reservation contract and exact allocation validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity


class ReservationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    RELEASED = "RELEASED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True, slots=True)
class Reservation:
    """A temporary, auditable hold against an immutable ResourceState quantity."""

    id: str
    organization_id: str
    agreement_id: str
    resource_id: str
    resource_state_id: str
    resource_version: int
    quantity: Quantity
    status: ReservationStatus
    expires_at: datetime
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    provenance: dict[str, str]

    def __post_init__(self) -> None:
        if any(
            not value
            for value in (
                self.id,
                self.organization_id,
                self.agreement_id,
                self.resource_id,
                self.resource_state_id,
                self.created_by,
            )
        ):
            raise DomainError("Reservation identity, agreement, resource, and actor are required.")
        if self.resource_version < 1 or self.version < 1:
            raise DomainError("Reservation resource and object versions must be positive.")
        if self.quantity.value <= Decimal("0"):
            raise DomainError("A reservation quantity must be greater than zero.")
        for value in (self.expires_at, self.created_at, self.updated_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise DomainError("Reservation timestamps must be timezone-aware.")
        if self.expires_at <= self.created_at:
            raise DomainError("Reservation expiry must be later than its creation.")
        if not self.provenance:
            raise DomainError("Reservation provenance is required.")

    def validate_tenant(self, organization_id: str) -> None:
        if self.organization_id != organization_id:
            raise TenantBoundaryError("Reservation belongs to another organization.")


def validate_reservation_capacity(
    *,
    requested: Quantity,
    agreement_quantity: Quantity,
    state_quantity: Quantity,
    already_reserved: Quantity,
) -> None:
    """Reject incompatible units and allocations exceeding either commercial or physical bounds."""
    quantities = (agreement_quantity, state_quantity, already_reserved)
    if any(
        (item.unit, item.unit_registry_version) != (requested.unit, requested.unit_registry_version)
        for item in quantities
    ):
        raise DomainError("Reservation quantities must use the same canonical unit and registry.")
    if requested.value <= Decimal("0"):
        raise DomainError("A reservation quantity must be greater than zero.")
    if requested.value > agreement_quantity.value:
        raise DomainError("Reservation quantity cannot exceed the agreed quantity.")
    if already_reserved.value < Decimal("0"):
        raise DomainError("Existing active reservations cannot be negative.")
    if already_reserved.value + requested.value > state_quantity.value:
        raise DomainError("Reservation would exceed the unreserved ResourceState quantity.")
