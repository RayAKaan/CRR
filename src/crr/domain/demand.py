"""Canonical Demand semantics for Phase 2."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity


class DemandStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    FULFILLED = "FULFILLED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    DISPUTED = "DISPUTED"


_ALLOWED_TRANSITIONS: dict[DemandStatus, frozenset[DemandStatus]] = {
    DemandStatus.DRAFT: frozenset({DemandStatus.ACTIVE, DemandStatus.CANCELLED}),
    DemandStatus.ACTIVE: frozenset(
        {
            DemandStatus.PAUSED,
            DemandStatus.FULFILLED,
            DemandStatus.EXPIRED,
            DemandStatus.CANCELLED,
            DemandStatus.DISPUTED,
        }
    ),
    DemandStatus.PAUSED: frozenset(
        {DemandStatus.ACTIVE, DemandStatus.CANCELLED, DemandStatus.DISPUTED}
    ),
    DemandStatus.FULFILLED: frozenset(),
    DemandStatus.EXPIRED: frozenset(),
    DemandStatus.CANCELLED: frozenset(),
    DemandStatus.DISPUTED: frozenset({DemandStatus.ACTIVE, DemandStatus.CANCELLED}),
}


@dataclass(frozen=True, slots=True)
class Demand:
    """A tenant-scoped requirement; never a representation of physical inventory."""

    id: str
    organization_id: str
    required_state: str
    quantity_min: Quantity
    quantity_target: Quantity
    quantity_max: Quantity
    remaining_quantity: Quantity
    status: DemandStatus
    location_constraints: Mapping[str, Any]
    timing_start: datetime
    timing_end: datetime
    quality_requirements: Mapping[str, Any]
    pricing_constraints: Mapping[str, Any]
    certifications: tuple[str, ...]
    regulatory_constraints: Mapping[str, Any]
    substitutions: tuple[str, ...]
    recurrence: Mapping[str, Any]
    version: int
    created_by: str
    provenance: Mapping[str, Any]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not (
            self.id
            and self.organization_id
            and self.required_state
            and self.created_by
        ):
            raise DomainError(
                "Demand identity, organization, required state and creator are required."
            )
        if self.version < 1:
            raise DomainError("Demand version must be positive.")
        units = {
            self.quantity_min.unit,
            self.quantity_target.unit,
            self.quantity_max.unit,
            self.remaining_quantity.unit,
        }
        if len(units) != 1:
            raise DomainError("Demand quantity bounds and remaining quantity must use one unit.")
        registry_versions = {
            self.quantity_min.unit_registry_version,
            self.quantity_target.unit_registry_version,
            self.quantity_max.unit_registry_version,
            self.remaining_quantity.unit_registry_version,
        }
        if len(registry_versions) != 1:
            raise DomainError("Demand quantities must use one unit-registry version.")
        if not self.quantity_min.value <= self.quantity_target.value <= self.quantity_max.value:
            raise DomainError("Demand quantity bounds must satisfy min <= target <= max.")
        if not self.quantity_min.value <= self.remaining_quantity.value <= self.quantity_max.value:
            raise DomainError("Remaining demand must remain within its declared bounds.")
        if self.timing_start.tzinfo is None or self.timing_start.utcoffset() is None:
            raise DomainError("Demand timing_start must include a timezone.")
        if self.timing_end.tzinfo is None or self.timing_end.utcoffset() is None:
            raise DomainError("Demand timing_end must include a timezone.")
        if self.timing_start >= self.timing_end:
            raise DomainError("Demand timing window must have start before end.")
        if not self.provenance:
            raise DomainError("Demand provenance is required.")
        object.__setattr__(self, "timing_start", self.timing_start.astimezone(UTC))
        object.__setattr__(self, "timing_end", self.timing_end.astimezone(UTC))
        object.__setattr__(self, "created_at", self.created_at.astimezone(UTC))
        object.__setattr__(self, "updated_at", self.updated_at.astimezone(UTC))

    def transition(self, target: DemandStatus, *, at: datetime | None = None) -> Demand:
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise DomainError(f"Illegal Demand lifecycle transition: {self.status} -> {target}.")
        updated_at = at or datetime.now(UTC)
        if updated_at.tzinfo is None or updated_at.utcoffset() is None:
            raise DomainError("Demand transition timestamp must include a timezone.")
        return replace(self, status=target, version=self.version + 1, updated_at=updated_at)


def validate_demand_tenant(demand: Demand, organization_id: str) -> None:
    if demand.organization_id != organization_id:
        raise TenantBoundaryError("Demand belongs to another organization.")
