"""Commercial-intent Opportunity domain contracts."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity


class OpportunityStatus(StrEnum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    CLOSED = "CLOSED"


_ALLOWED_TRANSITIONS: dict[OpportunityStatus, frozenset[OpportunityStatus]] = {
    OpportunityStatus.DRAFT: frozenset({OpportunityStatus.OPEN, OpportunityStatus.CANCELLED}),
    OpportunityStatus.OPEN: frozenset(
        {OpportunityStatus.EXPIRED, OpportunityStatus.CANCELLED, OpportunityStatus.CLOSED}
    ),
    OpportunityStatus.EXPIRED: frozenset(),
    OpportunityStatus.CANCELLED: frozenset(),
    OpportunityStatus.CLOSED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class Opportunity:
    """Durable commercial intent derived from a validated route, never execution truth."""

    id: str
    organization_id: str
    route_candidate_id: str
    candidate_set_fingerprint: str
    source_resource_state_id: str
    source_resource_state_version: int
    target_demand_id: str
    target_demand_version: int
    route_provenance: dict[str, Any]
    advisory_provenance: dict[str, Any] | None
    economic_model_id: str | None
    economic_model_version: int | None
    commercial_perspective: str | None
    currency: str | None
    quantity: Quantity
    valid_from: datetime
    valid_until: datetime
    status: OpportunityStatus
    version: int
    created_by: str
    provenance: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        if not self.id or not self.organization_id or not self.route_candidate_id:
            raise DomainError("Opportunity identity and organization are required.")
        if not self.candidate_set_fingerprint:
            raise DomainError("Candidate-set fingerprint is required.")
        if not self.source_resource_state_id or self.source_resource_state_version < 1:
            raise DomainError("A valid source ResourceState reference is required.")
        if not self.target_demand_id or self.target_demand_version < 1:
            raise DomainError("A valid target Demand reference is required.")
        if self.economic_model_id is None and self.economic_model_version is not None:
            raise DomainError("Economic model version requires an economic model reference.")
        if self.economic_model_id is not None and (
            self.economic_model_version is None or self.economic_model_version < 1
        ):
            raise DomainError("Economic model reference requires a positive version.")
        if self.currency is not None and len(self.currency) != 3:
            raise DomainError("Opportunity currency must be a three-letter code.")
        if self.valid_from.tzinfo is None or self.valid_from.utcoffset() is None:
            raise DomainError("Opportunity valid_from must be timezone-aware.")
        if self.valid_until.tzinfo is None or self.valid_until.utcoffset() is None:
            raise DomainError("Opportunity valid_until must be timezone-aware.")
        if self.valid_from >= self.valid_until:
            raise DomainError("Opportunity validity window must have valid_from before valid_until.")
        if self.version < 1:
            raise DomainError("Opportunity version must be positive.")
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise DomainError("Opportunity timestamps must be timezone-aware.")
        if not self.route_provenance:
            raise DomainError("Route provenance is required.")
        if not self.provenance:
            raise DomainError("Opportunity provenance is required.")

    def transition(self, new_status: OpportunityStatus) -> Opportunity:
        if new_status not in _ALLOWED_TRANSITIONS[self.status]:
            raise DomainError(
                f"Invalid Opportunity transition: {self.status.value} -> {new_status.value}."
            )
        return replace(self, status=new_status, version=self.version + 1, updated_at=datetime.now(self.updated_at.tzinfo))

    def validate_tenant(self, organization_id: str) -> None:
        if self.organization_id != organization_id:
            raise TenantBoundaryError("Opportunity belongs to another organization.")

    def assert_not_expired(self, now: datetime) -> None:
        if now.tzinfo is None or now.utcoffset() is None:
            raise DomainError("Opportunity freshness checks require timezone-aware time.")
        if now >= self.valid_until:
            raise DomainError("Opportunity validity window has expired.")


@dataclass(frozen=True, slots=True)
class OpportunityQuantitySnapshot:
    value: Decimal
    unit: str
    unit_registry_version: str

    def to_quantity(self) -> Quantity:
        return Quantity(self.value, self.unit, self.unit_registry_version)
