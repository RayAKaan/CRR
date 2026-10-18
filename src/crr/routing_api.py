"""Deterministic routing API over canonical Phase 1/2 objects."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from crr.capability_model import Capability
from crr.demand_model import Demand
from crr.domain.errors import DomainError
from crr.domain.quantity import Quantity
from crr.domain.routing import RouteCandidate, RouteLeg, RouteStatus, Rejection, evaluate_direct_route
from crr.models import ResourceState
from crr.routing_schemas import RoutingRequest
from crr.transformation_model import Transformation

router = APIRouter()


def _api():
    from crr import api

    return api


def _fail(request: Request, status: int, code: str, category: str, message: str):
    _api()._fail(request, status, code, category, message)


def _envelope(request: Request, data: Any):
    return _api()._envelope(request, data)


def _session_dependency():
    return _api().db_session


def _scope_dependency(scope: str):
    return _api().scope_required(scope)


def _state_spec_matches(spec: dict[str, Any], state_type: str) -> bool:
    value = spec.get("state_type") or spec.get("required_state") or spec.get("output_state")
    return value == state_type


def _candidate_data(candidate: RouteCandidate) -> dict[str, Any]:
    return {
        "id": candidate.id,
        "organization_id": candidate.organization_id,
        "source_resource_state_id": candidate.source_resource_state_id,
        "target_demand_id": candidate.target_demand_id,
        "legs": [
            {
                "kind": leg.kind,
                "object_id": leg.object_id,
                "input_state_type": leg.input_state_type,
                "output_state_type": leg.output_state_type,
            }
            for leg in candidate.legs
        ],
        "status": candidate.status.value,
        "rejections": [
            {"code": item.code, "object_id": item.object_id, "message": item.message}
            for item in candidate.rejections
        ],
        "source_version": candidate.source_version,
        "target_version": candidate.target_version,
        "evaluated_at": candidate.evaluated_at.isoformat(),
        "provenance": candidate.provenance,
    }


def _rejected_candidate(
    *,
    source: ResourceState,
    demand: Demand,
    code: str,
    object_id: str,
    message: str,
    evaluated_at: datetime,
    transformation: Transformation | None = None,
) -> RouteCandidate:
    legs = (
        RouteLeg(
            "TRANSFORMATION",
            transformation.id,
            source.state_type,
            demand.required_state,
        ),
    ) if transformation else (
        RouteLeg("DIRECT", source.id, source.state_type, demand.required_state),
    )
    return RouteCandidate(
        id=f"route_{source.id}_{demand.id}_{transformation.id if transformation else 'direct'}",
        organization_id=source.organization_id,
        source_resource_state_id=source.id,
        target_demand_id=demand.id,
        legs=legs,
        status=RouteStatus.INFEASIBLE,
        rejections=(Rejection(code, object_id, message),),
        source_version=source.resource_version,
        target_version=demand.version,
        evaluated_at=evaluated_at,
        provenance={"source": "CRR_DETERMINISTIC_ROUTER"},
    )


def _transformation_candidate(
    source: ResourceState,
    demand: Demand,
    transformation: Transformation,
    capabilities: list[Capability],
    registry,
    evaluated_at: datetime,
) -> RouteCandidate:
    rejection: Rejection | None = None
    if demand.status != "ACTIVE":
        rejection = Rejection("DEMAND_EXPIRED", demand.id, "Demand is not ACTIVE.")
    elif source.quantity_value <= 0:
        rejection = Rejection("INSUFFICIENT_QUANTITY", source.id, "Zero quantity is not routing supply.")
    elif transformation.status != "ACTIVE":
        rejection = Rejection("TRANSFORMATION_UNAVAILABLE", transformation.id, "Transformation is not ACTIVE.")
    elif transformation.eligible_location_ids and source.location_id not in transformation.eligible_location_ids:
        rejection = Rejection("LOCATION_INFEASIBLE", source.location_id, "Source location is not eligible for the transformation.")
    else:
        matching_capabilities = [
            item
            for item in capabilities
            if item.status == "ACTIVE"
            and item.location_id in ({source.location_id} | set(transformation.eligible_location_ids))
            and (not transformation.eligible_capability_ids or item.id in transformation.eligible_capability_ids)
            and item.location_id in (set(transformation.eligible_location_ids) or {item.location_id})
        ]
        if not matching_capabilities:
            rejection = Rejection("CAPABILITY_INACTIVE", transformation.id, "No active eligible capability is available.")
        else:
            try:
                source_quantity = Quantity(source.quantity_value, source.unit, source.unit_registry_version)
                capacity = Quantity(transformation.capacity_value, transformation.unit, transformation.unit_registry_version)
                source_in_capacity_units = registry.convert(source_quantity, capacity.unit)
                if source_in_capacity_units.value > capacity.value:
                    rejection = Rejection("CAPACITY_INSUFFICIENT", transformation.id, "Transformation capacity is insufficient.")
                output = source_in_capacity_units.value * transformation.yield_min_value
                demand_min = registry.convert(
                    Quantity(demand.quantity_min_value, demand.unit, demand.unit_registry_version),
                    transformation.unit,
                )
                if output < demand_min.value:
                    rejection = Rejection("YIELD_INVALID", transformation.id, "Minimum declared yield cannot satisfy demand minimum.")
            except DomainError as exc:
                rejection = Rejection("UNIT_INCOMPATIBLE", transformation.id, str(exc))
            if rejection is None:
                if not any(
                    _state_spec_matches(spec, source.state_type)
                    for spec in transformation.input_specifications
                ):
                    rejection = Rejection("STATE_MISMATCH", transformation.id, "Transformation input does not accept source state.")
                elif not any(
                    _state_spec_matches(spec, demand.required_state)
                    for spec in transformation.output_specifications
                ):
                    rejection = Rejection("STATE_MISMATCH", transformation.id, "Transformation output does not satisfy demand state.")
    legs = (RouteLeg("TRANSFORMATION", transformation.id, source.state_type, demand.required_state),)
    return RouteCandidate(
        id=f"route_{source.id}_{demand.id}_{transformation.id}",
        organization_id=source.organization_id,
        source_resource_state_id=source.id,
        target_demand_id=demand.id,
        legs=legs,
        status=RouteStatus.INFEASIBLE if rejection else RouteStatus.FEASIBLE,
        rejections=(rejection,) if rejection else (),
        source_version=source.resource_version,
        target_version=demand.version,
        evaluated_at=evaluated_at,
        provenance={"source": "CRR_DETERMINISTIC_ROUTER", "transformation_version": transformation.version},
    )


@router.post("/v1/routes/evaluate")
def evaluate_routes(
    body: RoutingRequest,
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("routes:read"))],
):
    source = session.scalar(
        select(ResourceState).where(
            ResourceState.id == body.source_resource_state_id,
            ResourceState.organization_id == principal.organization_id,
        )
    )
    demand = session.scalar(
        select(Demand).where(
            Demand.id == body.target_demand_id,
            Demand.organization_id == principal.organization_id,
        )
    )
    if source is None or demand is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Source ResourceState or target Demand not found.")
    now = datetime.now(UTC)
    if body.valid_until is not None and body.valid_until.astimezone(UTC) <= now:
        _fail(request, 422, "INVALID_VALIDITY_WINDOW", "VALIDATION_FAILURE", "valid_until must be in the future.")
    registry = request.app.state.unit_registry
    direct = evaluate_direct_route(
        source_id=source.id,
        source_version=source.resource_version,
        source_organization_id=source.organization_id,
        source_state_type=source.state_type,
        source_quantity=Quantity(source.quantity_value, source.unit, source.unit_registry_version),
        demand_id=demand.id,
        demand_version=demand.version,
        demand_organization_id=demand.organization_id,
        demand_state_type=demand.required_state,
        demand_min=Quantity(demand.quantity_min_value, demand.unit, demand.unit_registry_version),
        demand_max=Quantity(demand.quantity_max_value, demand.unit, demand.unit_registry_version),
        demand_active=demand.status == "ACTIVE",
        unit_registry=registry,
        evaluated_at=now,
    )
    candidates = [direct]
    transformations = session.scalars(
        select(Transformation).where(Transformation.organization_id == principal.organization_id)
    ).all()
    capabilities = session.scalars(
        select(Capability).where(Capability.organization_id == principal.organization_id)
    ).all()
    for transformation in transformations:
        if transformation.status != "ACTIVE":
            continue
        candidates.append(
            _transformation_candidate(source, demand, transformation, capabilities, registry, now)
        )
    feasible = [candidate for candidate in candidates if candidate.status == RouteStatus.FEASIBLE]
    return _envelope(
        request,
        {
            "source_resource_state_id": source.id,
            "target_demand_id": demand.id,
            "evaluated_at": now.isoformat(),
            "candidates": [_candidate_data(candidate) for candidate in candidates],
            "feasible_candidates": [_candidate_data(candidate) for candidate in feasible],
            "optimization": None,
            "decision": None,
        },
    )
