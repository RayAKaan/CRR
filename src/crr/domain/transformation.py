"""Canonical Transformation domain semantics for Phase 2C."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity


class TransformationStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


_ALLOWED_TRANSITIONS: dict[TransformationStatus, frozenset[TransformationStatus]] = {
    TransformationStatus.DRAFT: frozenset({TransformationStatus.ACTIVE}),
    TransformationStatus.ACTIVE: frozenset(
        {TransformationStatus.SUSPENDED, TransformationStatus.EXPIRED, TransformationStatus.REVOKED}
    ),
    TransformationStatus.SUSPENDED: frozenset(),
    TransformationStatus.EXPIRED: frozenset(),
    TransformationStatus.REVOKED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class Transformation:
    """Reusable input/output process definition, never an execution record."""

    id: str
    organization_id: str
    input_specifications: tuple[dict[str, Any], ...]
    output_specifications: tuple[dict[str, Any], ...]
    yield_min: Decimal
    yield_target: Decimal
    yield_max: Decimal
    loss_residuals: tuple[dict[str, Any], ...]
    duration_seconds: int
    capacity: Quantity
    cost_metadata: dict[str, Any]
    quality_effects: dict[str, Any]
    regulatory_requirements: dict[str, Any]
    eligible_capability_ids: tuple[str, ...]
    eligible_location_ids: tuple[str, ...]
    status: TransformationStatus
    version: int
    created_by: str
    provenance: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.id or not self.organization_id or not self.created_by:
            raise DomainError("Transformation identity, organization, and creator are required.")
        if not self.input_specifications:
            raise DomainError("At least one input specification is required.")
        if not self.output_specifications:
            raise DomainError("At least one output specification is required.")
        if self.version < 1:
            raise DomainError("Transformation version must be positive.")
        if self.duration_seconds <= 0:
            raise DomainError("Transformation duration must be positive.")
        for value, name in (
            (self.yield_min, "yield_min"),
            (self.yield_target, "yield_target"),
            (self.yield_max, "yield_max"),
        ):
            if not isinstance(value, Decimal):
                raise DomainError(f"Transformation {name} must be an exact decimal.")
            if value < 0 or value > 1:
                raise DomainError(f"Transformation {name} must be between 0 and 1.")
        if not (self.yield_min <= self.yield_target <= self.yield_max):
            raise DomainError("Transformation yield bounds must satisfy min <= target <= max.")
        if not self.provenance:
            raise DomainError("Transformation provenance is required.")
        object.__setattr__(self, "created_at", self.created_at.astimezone(UTC))
        object.__setattr__(self, "updated_at", self.updated_at.astimezone(UTC))

    def transition(
        self, target: TransformationStatus, at: datetime | None = None
    ) -> Transformation:
        if target not in _ALLOWED_TRANSITIONS[self.status]:
            raise DomainError(f"Illegal Transformation transition: {self.status} -> {target}.")
        changed_at = (at or datetime.now(UTC)).astimezone(UTC)
        return replace(self, status=target, version=self.version + 1, updated_at=changed_at)


def validate_transformation_tenant(
    transformation: Transformation, organization_id: str
) -> None:
    if transformation.organization_id != organization_id:
        raise TenantBoundaryError("Transformation belongs to a different organization.")
