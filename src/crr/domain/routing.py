"""Deterministic routing candidates and hard-constraint evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from crr.domain.capability import Capability, CapabilityStatus
from crr.domain.demand import Demand, DemandStatus
from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity, UnitRegistry
from crr.domain.resource_state import ResourceState
from crr.domain.transformation import Transformation, TransformationStatus


class RouteStatus(StrEnum):
    FEASIBLE = "FEASIBLE"
    INFEASIBLE = "INFEASIBLE"


@dataclass(frozen=True, slots=True)
class RouteLeg:
    kind: str
    object_id: str
    input_state_type: str
    output_state_type: str


@dataclass(frozen=True, slots=True)
class Rejection:
    code: str
    object_id: str
    message: str


@dataclass(frozen=True, slots=True)
class RouteCandidate:
    id: str
    organization_id: str
    source_resource_state_id: str
    target_demand_id: str
    legs: tuple[RouteLeg, ...]
    status: RouteStatus
    rejections: tuple[Rejection, ...]
    source_version: int
    target_version: int
    evaluated_at: datetime
    provenance: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.id or not self.organization_id:
            raise DomainError("Route identity and organization are required.")
        if not self.source_resource_state_id or not self.target_demand_id:
            raise DomainError("Route source and target are required.")
        if not self.legs:
            raise DomainError("A route candidate requires at least one leg.")
        if self.status == RouteStatus.FEASIBLE and self.rejections:
            raise DomainError("A feasible route cannot contain hard-constraint rejections.")
        if self.status == RouteStatus.INFEASIBLE and not self.rejections:
            raise DomainError("An infeasible route must expose its rejection reasons.")
        if self.source_version < 1 or self.target_version < 1:
            raise DomainError("Route input versions must be positive.")
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise DomainError("Route evaluation time must include a timezone.")
        object.__setattr__(self, "evaluated_at", self.evaluated_at.astimezone(UTC))


def _reject(code: str, object_id: str, message: str) -> Rejection:
    return Rejection(code=code, object_id=object_id, message=message)


def evaluate_direct_route(
    *,
    source_id: str,
    source_version: int,
    source_organization_id: str,
    source_state_type: str,
    source_quantity: Quantity,
    demand_id: str,
    demand_version: int,
    demand_organization_id: str,
    demand_state_type: str,
    demand_min: Quantity,
    demand_max: Quantity,
    demand_active: bool,
    unit_registry: UnitRegistry,
    evaluated_at: datetime,
) -> RouteCandidate:
    """Evaluate a zero-transformation direct route using canonical facts."""
    if source_organization_id != demand_organization_id:
        raise TenantBoundaryError("Routing source and target must share an organization.")
    rejections: list[Rejection] = []
    if not demand_active:
        rejections.append(_reject("DEMAND_EXPIRED", demand_id, "Demand is not ACTIVE."))
    if source_quantity.value <= 0:
        rejections.append(
            _reject(
                "INSUFFICIENT_QUANTITY",
                source_id,
                "Zero quantity is not routing supply.",
            )
        )
    if source_state_type != demand_state_type:
        rejections.append(
            _reject(
                "STATE_MISMATCH",
                demand_id,
                "Source state does not satisfy demand state.",
            )
        )
    try:
        converted_min = unit_registry.convert(demand_min, source_quantity.unit)
        unit_registry.convert(demand_max, source_quantity.unit)
    except DomainError as exc:
        rejections.append(_reject("UNIT_INCOMPATIBLE", demand_id, str(exc)))
    else:
        if source_quantity.value < converted_min.value:
            rejections.append(
                _reject(
                    "INSUFFICIENT_QUANTITY",
                    source_id,
                    "Source quantity is below demand minimum.",
                )
            )
    status = RouteStatus.INFEASIBLE if rejections else RouteStatus.FEASIBLE
    return RouteCandidate(
        id=f"route_{source_id}_{demand_id}",
        organization_id=source_organization_id,
        source_resource_state_id=source_id,
        target_demand_id=demand_id,
        legs=(RouteLeg("DIRECT", source_id, source_state_type, demand_state_type),),
        status=status,
        rejections=tuple(rejections),
        source_version=source_version,
        target_version=demand_version,
        evaluated_at=evaluated_at,
        provenance={"source": "CRR_DETERMINISTIC_ROUTER"},
    )


def _spec_state_type(specification: dict[str, Any]) -> str | None:
    value = specification.get("state_type")
    return value if isinstance(value, str) and value else None


def _matches_state_type(
    state_type: str,
    specifications: tuple[dict[str, Any], ...],
) -> bool:
    return any(_spec_state_type(spec) == state_type for spec in specifications)


def _convert_quantity(
    quantity: Quantity,
    target_unit: str,
    unit_registry: UnitRegistry,
) -> Quantity:
    return unit_registry.convert(quantity, target_unit)


def evaluate_transformation_route(
    *,
    source: ResourceState,
    demand: Demand,
    capability: Capability,
    transformation: Transformation,
    unit_registry: UnitRegistry,
    start_at: datetime,
) -> RouteCandidate:
    """Evaluate one deterministic transformation-backed route without mutation."""
    if source.organization_id != demand.organization_id:
        raise TenantBoundaryError("Routing source and target must share an organization.")
    if source.organization_id != capability.organization_id:
        raise TenantBoundaryError("Capability belongs to another organization.")
    if source.organization_id != transformation.organization_id:
        raise TenantBoundaryError("Transformation belongs to another organization.")

    if start_at.tzinfo is None or start_at.utcoffset() is None:
        raise DomainError("Route start time must include a timezone.")
    start = start_at.astimezone(UTC)
    end = start + timedelta(seconds=transformation.duration_seconds)
    rejections: list[Rejection] = []

    if demand.status is not DemandStatus.ACTIVE:
        rejections.append(_reject("DEMAND_EXPIRED", demand.id, "Demand is not ACTIVE."))
    if source.quantity.value <= 0:
        rejections.append(
            _reject("INSUFFICIENT_QUANTITY", source.id, "Zero quantity is not routing supply.")
        )
    if transformation.status is not TransformationStatus.ACTIVE:
        rejections.append(
            _reject(
                "TRANSFORMATION_UNAVAILABLE",
                transformation.id,
                "Transformation is not ACTIVE.",
            )
        )
    if capability.status is not CapabilityStatus.ACTIVE:
        rejections.append(
            _reject("CAPABILITY_INACTIVE", capability.id, "Capability is not ACTIVE.")
        )
    if transformation.id not in capability.transformation_ids:
        rejections.append(
            _reject(
                "TRANSFORMATION_UNAVAILABLE",
                transformation.id,
                "Capability is not registered for this transformation.",
            )
        )
    if capability.id not in transformation.eligible_capability_ids:
        rejections.append(
            _reject(
                "CAPABILITY_INACTIVE",
                capability.id,
                "Capability is not eligible for this transformation.",
            )
        )
    if capability.location_id not in transformation.eligible_location_ids:
        rejections.append(
            _reject(
                "LOCATION_INFEASIBLE",
                capability.location_id,
                "Capability location is not eligible for the transformation.",
            )
        )
    if source.location_id != capability.location_id:
        rejections.append(
            _reject(
                "LOCATION_INFEASIBLE",
                source.location_id,
                "Source location does not match the transformation capability location.",
            )
        )
    if not _matches_state_type(source.state_type, transformation.input_specifications):
        rejections.append(
            _reject(
                "STATE_MISMATCH",
                transformation.id,
                "Source state does not satisfy transformation input specifications.",
            )
        )
    if not _matches_state_type(demand.required_state, transformation.output_specifications):
        rejections.append(
            _reject(
                "STATE_MISMATCH",
                demand.id,
                "Demand state does not satisfy transformation output specifications.",
            )
        )

    if not (
        capability.operating_window_start <= start
        and end <= capability.operating_window_end
    ):
        rejections.append(
            _reject(
                "TIME_WINDOW_CONFLICT",
                capability.id,
                "Transformation does not fit the capability operating window.",
            )
        )
    if start < demand.timing_start or end > demand.timing_end:
        rejections.append(
            _reject(
                "TIME_WINDOW_CONFLICT",
                demand.id,
                "Transformation does not fit the demand timing window.",
            )
        )

    try:
        source_capacity = _convert_quantity(source.quantity, capability.capacity.unit, unit_registry)
        source_transformation_capacity = _convert_quantity(
            source.quantity, transformation.capacity.unit, unit_registry
        )
        demand_min = _convert_quantity(demand.quantity_min, source.quantity.unit, unit_registry)
        guaranteed_output = source.quantity.value * transformation.yield_min
    except DomainError as exc:
        rejections.append(_reject("UNIT_INCOMPATIBLE", source.id, str(exc)))
    else:
        if source_capacity.value > capability.capacity.value:
            rejections.append(
                _reject(
                    "CAPACITY_INSUFFICIENT",
                    capability.id,
                    "Source quantity exceeds capability capacity.",
                )
            )
        if (
            capability.minimum_batch is not None
            and source_capacity.value < capability.minimum_batch.value
        ):
            rejections.append(
                _reject(
                    "CAPACITY_INSUFFICIENT",
                    capability.id,
                    "Source quantity is below the capability minimum batch.",
                )
            )
        if source_transformation_capacity.value > transformation.capacity.value:
            rejections.append(
                _reject(
                    "CAPACITY_INSUFFICIENT",
                    transformation.id,
                    "Source quantity exceeds transformation capacity.",
                )
            )
        if guaranteed_output < demand_min.value:
            rejections.append(
                _reject(
                    "INSUFFICIENT_QUANTITY",
                    transformation.id,
                    "Minimum guaranteed transformation output is below demand minimum.",
                )
            )

    if source.quantity.unit_registry_version != transformation.capacity.unit_registry_version:
        rejections.append(
            _reject(
                "UNIT_INCOMPATIBLE",
                transformation.id,
                "Source and transformation capacity use different unit registries.",
            )
        )

    status = RouteStatus.INFEASIBLE if rejections else RouteStatus.FEASIBLE
    return RouteCandidate(
        id=f"route_{source.id}_{transformation.id}_{demand.id}",
        organization_id=source.organization_id,
        source_resource_state_id=source.id,
        target_demand_id=demand.id,
        legs=(
            RouteLeg(
                "TRANSFORMATION",
                transformation.id,
                source.state_type,
                demand.required_state,
            ),
        ),
        status=status,
        rejections=tuple(rejections),
        source_version=source.version,
        target_version=demand.version,
        evaluated_at=start,
        provenance={
            "source": "CRR_DETERMINISTIC_ROUTER",
            "capability_version": capability.version,
            "transformation_version": transformation.version,
        },
    )
