"""Immutable ResourceState snapshots and explicit, attributable transitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from crr.domain.errors import DomainError, StaleVersionError, TenantBoundaryError
from crr.domain.quantity import Quantity


class TransitionKind(StrEnum):
    PHYSICAL_CHANGE = "PHYSICAL_CHANGE"
    CORRECTION = "CORRECTION"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError("Authoritative timestamps must include a timezone.")
    return value.astimezone(UTC)


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item) for item in value)
    return value


@dataclass(frozen=True, slots=True)
class ResourceState:
    """Accepted physical snapshot. Lifecycle, availability and epistemic states are separate."""

    id: str
    resource_id: str
    organization_id: str
    version: int
    state_type: str
    quantity: Quantity
    location_id: str
    effective_at: datetime
    recorded_at: datetime
    created_by: str
    provenance: Mapping[str, Any]
    quality: Mapping[str, Any] = field(default_factory=dict)
    physical_properties: Mapping[str, Any] = field(default_factory=dict)
    predecessor_state_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in (
            "id",
            "resource_id",
            "organization_id",
            "state_type",
            "location_id",
            "created_by",
        ):
            if not getattr(self, name):
                raise DomainError(f"{name} is required.")
        if self.version < 1:
            raise DomainError("ResourceState version must be positive.")
        if not self.provenance:
            raise DomainError("Canonical ResourceState requires provenance.")
        if len(set(self.predecessor_state_ids)) != len(self.predecessor_state_ids):
            raise DomainError("A ResourceState cannot repeat a predecessor.")
        object.__setattr__(self, "effective_at", _utc(self.effective_at))
        object.__setattr__(self, "recorded_at", _utc(self.recorded_at))
        object.__setattr__(self, "provenance", _freeze(self.provenance))
        object.__setattr__(self, "quality", _freeze(self.quality))
        object.__setattr__(self, "physical_properties", _freeze(self.physical_properties))

    @classmethod
    def initial(
        cls,
        *,
        resource_id: str,
        organization_id: str,
        state_type: str,
        quantity: Quantity,
        location_id: str,
        effective_at: datetime,
        created_by: str,
        provenance: Mapping[str, Any],
        quality: Mapping[str, Any] | None = None,
        physical_properties: Mapping[str, Any] | None = None,
        state_id: str | None = None,
        recorded_at: datetime | None = None,
    ) -> ResourceState:
        return cls(
            id=state_id or f"rst_{uuid4().hex}",
            resource_id=resource_id,
            organization_id=organization_id,
            version=1,
            state_type=state_type,
            quantity=quantity,
            location_id=location_id,
            effective_at=effective_at,
            recorded_at=recorded_at or datetime.now(UTC),
            created_by=created_by,
            provenance=provenance,
            quality=quality or {},
            physical_properties=physical_properties or {},
        )


@dataclass(frozen=True, slots=True)
class StateTransition:
    """Immutable event linking a predecessor to its successor snapshot."""

    id: str
    organization_id: str
    resource_id: str
    predecessor_state_id: str
    successor_state_id: str
    aggregate_version: int
    kind: TransitionKind
    occurred_at: datetime
    actor_id: str
    reason: str
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        if self.aggregate_version < 2:
            raise DomainError("A successor transition must advance the aggregate version.")
        if not self.actor_id or not self.reason.strip() or not self.provenance:
            raise DomainError("Transition actor, reason and provenance are required.")
        object.__setattr__(self, "occurred_at", _utc(self.occurred_at))
        object.__setattr__(self, "provenance", _freeze(self.provenance))


def transition_state(
    predecessor: ResourceState,
    *,
    expected_version: int,
    organization_id: str,
    actor_id: str,
    kind: TransitionKind,
    reason: str,
    occurred_at: datetime,
    state_type: str,
    quantity: Quantity,
    location_id: str,
    provenance: Mapping[str, Any],
    quality: Mapping[str, Any] | None = None,
    physical_properties: Mapping[str, Any] | None = None,
    successor_id: str | None = None,
) -> tuple[ResourceState, StateTransition]:
    """Create a successor snapshot without mutating the predecessor."""
    if organization_id != predecessor.organization_id:
        raise TenantBoundaryError("Transition must remain within its owning organization.")
    if expected_version != predecessor.version:
        raise StaleVersionError(
            f"Expected ResourceState version {expected_version}; "
            f"current version is {predecessor.version}."
        )
    if not actor_id or not reason.strip():
        raise DomainError("Transition actor and reason are required.")
    if kind == TransitionKind.PHYSICAL_CHANGE and (
        quantity.value != predecessor.quantity.value
        or quantity.unit != predecessor.quantity.unit
        or quantity.unit_registry_version != predecessor.quantity.unit_registry_version
        or state_type != predecessor.state_type
    ):
        raise DomainError(
            "Quantity or classification changes require a versioned Transformation and yield model."
        )
    when = _utc(occurred_at)
    successor = ResourceState(
        id=successor_id or f"rst_{uuid4().hex}",
        resource_id=predecessor.resource_id,
        organization_id=organization_id,
        version=predecessor.version + 1,
        state_type=state_type,
        quantity=quantity,
        location_id=location_id,
        effective_at=when,
        recorded_at=datetime.now(UTC),
        created_by=actor_id,
        provenance=provenance,
        quality=quality or {},
        physical_properties=physical_properties or {},
        predecessor_state_ids=(predecessor.id,),
    )
    event = StateTransition(
        id=f"evt_{uuid4().hex}",
        organization_id=organization_id,
        resource_id=predecessor.resource_id,
        predecessor_state_id=predecessor.id,
        successor_state_id=successor.id,
        aggregate_version=successor.version,
        kind=kind,
        occurred_at=when,
        actor_id=actor_id,
        reason=reason,
        provenance=provenance,
    )
    return successor, event
