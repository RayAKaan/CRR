"""Canonical Capability domain semantics for Phase 2B."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity


class CapabilityStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


_ALLOWED_TRANSITIONS: dict[CapabilityStatus, frozenset[CapabilityStatus]] = {
    CapabilityStatus.DRAFT: frozenset({CapabilityStatus.ACTIVE}),
    CapabilityStatus.ACTIVE: frozenset(
        {CapabilityStatus.SUSPENDED, CapabilityStatus.EXPIRED, CapabilityStatus.REVOKED}
    ),
    CapabilityStatus.SUSPENDED: frozenset(),
    CapabilityStatus.EXPIRED: frozenset(),
    CapabilityStatus.REVOKED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class Capability:
    """An organization's declared physical ability, not an execution record."""

    id: str
    organization_id: str
    accepted_inputs: tuple[dict[str, Any], ...]
    output_specifications: dict[str, Any]
    transformation_ids: tuple[str, ...]
    capacity: Quantity
    minimum_batch: Quantity | None
    location_id: str
    operating_window_start: datetime
    operating_window_end: datetime
    processing_cost: dict[str, Any]
    certifications: tuple[str, ...]
    regulatory_constraints: dict[str, Any]
    status: CapabilityStatus
    version: int
    created_by: str
    provenance: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.id or not self.organization_id or not self.location_id or not self.created_by:
            raise DomainError(
                "Capability identity, organization, location, and creator are required."
            )
        if not self.accepted_inputs:
            raise DomainError("At least one accepted input specification is required.")
        if not self.output_specifications:
            raise DomainError("Output specifications are required.")
        if self.version < 1:
            raise DomainError("Capability version must be positive.")
        if self.minimum_batch is not None:
            if self.minimum_batch.unit != self.capacity.unit:
                raise DomainError("Minimum batch and capacity must use the same unit.")
            if self.minimum_batch.unit_registry_version != self.capacity.unit_registry_version:
                raise DomainError(
                    "Minimum batch and capacity must use the same unit registry version."
                )
            if self.minimum_batch.value > self.capacity.value:
                raise DomainError("Minimum batch cannot exceed capability capacity.")
        if (
            self.operating_window_start.tzinfo is None
            or self.operating_window_start.utcoffset() is None
        ):
            raise DomainError("Capability operating window start must include a timezone.")
        if (
            self.operating_window_end.tzinfo is None
            or self.operating_window_end.utcoffset() is None
        ):
            raise DomainError("Capability operating window end must include a timezone.")
        if self.operating_window_start >= self.operating_window_end:
            raise DomainError("Capability operating window start must be before end.")
        if not self.provenance:
            raise DomainError("Capability provenance is required.")
        object.__setattr__(
            self,
            "operating_window_start",
            self.operating_window_start.astimezone(UTC),
        )
        object.__setattr__(
            self,
            "operating_window_end",
            self.operating_window_end.astimezone(UTC),
        )
        object.__setattr__(self, "created_at", self.created_at.astimezone(UTC))
        object.__setattr__(self, "updated_at", self.updated_at.astimezone(UTC))

    def transition(self, target: CapabilityStatus, at: datetime | None = None) -> Capability:
        """Return a new version after an explicitly allowed lifecycle transition."""
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise DomainError(f"Illegal Capability transition: {self.status} -> {target}.")
        changed_at = (at or datetime.now(UTC)).astimezone(UTC)
        return replace(self, status=target, version=self.version + 1, updated_at=changed_at)


def validate_capability_tenant(capability: Capability, organization_id: str) -> None:
    if capability.organization_id != organization_id:
        raise TenantBoundaryError("Capability belongs to a different organization.")
