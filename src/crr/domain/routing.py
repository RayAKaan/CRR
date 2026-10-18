"""Deterministic routing candidates and hard-constraint evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity, UnitRegistry


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
        rejections.append(
            _reject("DEMAND_EXPIRED", demand_id, "Demand is not ACTIVE.")
        )
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
