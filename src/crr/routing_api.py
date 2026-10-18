"""Computation-only routing API over canonical Phase 1/2 state."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from crr.capability_model import Capability
from crr.demand_model import Demand
from crr.domain.capability import Capability as DomainCapability
from crr.domain.capability import CapabilityStatus
from crr.domain.demand import Demand as DomainDemand
from crr.domain.demand import DemandStatus
from crr.domain.errors import DomainError
from crr.domain.quantity import Quantity
from crr.domain.regulatory import evaluate_regulatory_eligibility
from crr.domain.resource_state import ResourceState as DomainResourceState
from crr.domain.routing import (
    Rejection,
    RouteCandidate,
    RouteLeg,
    RouteStatus,
    evaluate_direct_route,
    evaluate_transformation_route,
)
from crr.domain.transformation import Transformation as DomainTransformation
from crr.domain.transformation import TransformationStatus
from crr.models import ResourceState
from crr.routing_schemas import RoutingComputeInput
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


def _quantity(value: Decimal, unit: str, registry_version: str) -> Quantity:
    return Quantity(value, unit, registry_version)


def _domain_state(item: ResourceState) -> DomainResourceState:
    return DomainResourceState(
        id=item.id,
        resource_id=item.resource_id,
        organization_id=item.organization_id,
        version=item.resource_version,
        state_type=item.state_type,
        quantity=_quantity(item.quantity_value, item.unit, item.unit_registry_version),
        location_id=item.location_id,
        effective_at=item.effective_at,
        recorded_at=item.recorded_at,
        created_by=item.created_by,
        provenance=item.provenance,
        quality=item.quality,
        physical_properties=item.physical_properties,
        predecessor_state_ids=tuple(item.predecessor_state_ids),
    )


def _domain_demand(item: Demand) -> DomainDemand:
    return DomainDemand(
        id=item.id,
        organization_id=item.organization_id,
        required_state=item.required_state,
        quantity_min=_quantity(item.quantity_min_value, item.unit, item.unit_registry_version),
        quantity_target=_quantity(
            item.quantity_target_value, item.unit, item.unit_registry_version
        ),
        quantity_max=_quantity(item.quantity_max_value, item.unit, item.unit_registry_version),
        remaining_quantity=_quantity(
            item.remaining_quantity_value, item.unit, item.unit_registry_version
        ),
        status=DemandStatus(item.status),
        location_constraints=item.location_constraints,
        timing_start=item.timing_start,
        timing_end=item.timing_end,
        quality_requirements=item.quality_requirements,
        pricing_constraints=item.pricing_constraints,
        certifications=tuple(item.certifications),
        regulatory_constraints=item.regulatory_constraints,
        substitutions=tuple(item.substitutions),
        recurrence=item.recurrence,
        version=item.version,
        created_by=item.created_by,
        provenance=item.provenance,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _domain_capability(item: Capability) -> DomainCapability:
    minimum_batch = (
        _quantity(item.minimum_batch_value, item.unit, item.unit_registry_version)
        if item.minimum_batch_value is not None
        else None
    )
    return DomainCapability(
        id=item.id,
        organization_id=item.organization_id,
        accepted_inputs=tuple(item.accepted_inputs),
        output_specifications=item.output_specifications,
        transformation_ids=tuple(item.transformation_ids),
        capacity=_quantity(item.capacity_value, item.unit, item.unit_registry_version),
        minimum_batch=minimum_batch,
        location_id=item.location_id,
        operating_window_start=item.operating_window_start,
        operating_window_end=item.operating_window_end,
        processing_cost=item.processing_cost,
        certifications=tuple(item.certifications),
        regulatory_constraints=item.regulatory_constraints,
        status=CapabilityStatus(item.status),
        version=item.version,
        created_by=item.created_by,
        provenance=item.provenance,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _domain_transformation(item: Transformation) -> DomainTransformation:
    return DomainTransformation(
        id=item.id,
        organization_id=item.organization_id,
        input_specifications=tuple(item.input_specifications),
        output_specifications=tuple(item.output_specifications),
        yield_min=item.yield_min_value,
        yield_target=item.yield_target_value,
        yield_max=item.yield_max_value,
        loss_residuals=tuple(item.loss_residuals),
        duration_seconds=item.duration_seconds,
        capacity=_quantity(item.capacity_value, item.unit, item.unit_registry_version),
        cost_metadata=item.cost_metadata,
        quality_effects=item.quality_effects,
        regulatory_requirements=item.regulatory_requirements,
        eligible_capability_ids=tuple(item.eligible_capability_ids),
        eligible_location_ids=tuple(item.eligible_location_ids),
        status=TransformationStatus(item.status),
        version=item.version,
        created_by=item.created_by,
        provenance=item.provenance,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _rejection_data(item: Rejection) -> dict[str, str]:
    return {"code": item.code, "object_id": item.object_id, "message": item.message}


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
        "status": candidate.status,
        "rejections": [_rejection_data(item) for item in candidate.rejections],
        "source_version": candidate.source_version,
        "target_version": candidate.target_version,
        "evaluated_at": candidate.evaluated_at.isoformat(),
        "provenance": candidate.provenance,
    }


def _with_rejections(
    candidate: RouteCandidate, rejections: tuple[Rejection, ...]
) -> RouteCandidate:
    if not rejections:
        return candidate
    return replace(
        candidate,
        status=RouteStatus.INFEASIBLE,
        rejections=candidate.rejections + rejections,
    )


def _deterministic_start(demand: DomainDemand, source: DomainResourceState) -> datetime:
    return max(demand.timing_start, source.effective_at).astimezone(UTC)


def _location_constraint(demand: DomainDemand) -> str | None:
    value = demand.location_constraints.get("location_id")
    return value if isinstance(value, str) and value else None


def _location_rejected_candidate(
    source: DomainResourceState, demand: DomainDemand
) -> RouteCandidate:
    return RouteCandidate(
        id=f"route_{source.id}_{demand.id}",
        organization_id=source.organization_id,
        source_resource_state_id=source.id,
        target_demand_id=demand.id,
        legs=(RouteLeg("DIRECT", source.id, source.state_type, demand.required_state),),
        status=RouteStatus.INFEASIBLE,
        rejections=(
            Rejection(
                "LOCATION_INFEASIBLE",
                source.location_id,
                "Source location does not satisfy demand location.",
            ),
        ),
        source_version=source.version,
        target_version=demand.version,
        evaluated_at=datetime.now(UTC),
        provenance={"source": "CRR_DETERMINISTIC_ROUTER"},
    )


@router.post("/v1/routes/compute")
def compute_routes(
    body: RoutingComputeInput,
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("routes:compute"))],
):
    source_row = session.scalar(
        select(ResourceState).where(
            ResourceState.id == body.source_resource_state_id,
            ResourceState.organization_id == principal.organization_id,
        )
    )
    if source_row is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "ResourceState not found.")
    demand_row = session.scalar(
        select(Demand).where(
            Demand.id == body.target_demand_id,
            Demand.organization_id == principal.organization_id,
        )
    )
    if demand_row is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Demand not found.")

    source = _domain_state(source_row)
    demand = _domain_demand(demand_row)
    registry = request.app.state.unit_registry
    try:
        registry.validate(source.quantity)
        registry.validate(demand.quantity_min)
        registry.validate(demand.quantity_max)
    except DomainError as exc:
        _fail(request, 422, "UNIT_VALIDATION_FAILED", "VALIDATION_FAILURE", str(exc))

    if body.valid_until is not None and body.valid_until.astimezone(UTC) < datetime.now(UTC):
        _fail(
            request,
            422,
            "ROUTE_REQUEST_EXPIRED",
            "VALIDATION_FAILURE",
            "valid_until is in the past.",
        )

    location_id = _location_constraint(demand)
    if location_id is not None and location_id != source.location_id:
        candidates = [_location_rejected_candidate(source, demand)]
    else:
        candidates = [
            evaluate_direct_route(
                source_id=source.id,
                source_version=source.version,
                source_organization_id=source.organization_id,
                source_state_type=source.state_type,
                source_quantity=source.quantity,
                demand_id=demand.id,
                demand_version=demand.version,
                demand_organization_id=demand.organization_id,
                demand_state_type=demand.required_state,
                demand_min=demand.quantity_min,
                demand_max=demand.quantity_max,
                demand_active=demand.status is DemandStatus.ACTIVE,
                unit_registry=registry,
                evaluated_at=datetime.now(UTC),
            )
        ]

    capabilities = session.scalars(
        select(Capability).where(Capability.organization_id == principal.organization_id)
    ).all()
    transformations = session.scalars(
        select(Transformation).where(Transformation.organization_id == principal.organization_id)
    ).all()
    capability_by_id = {item.id: item for item in capabilities}

    for transformation_row in sorted(transformations, key=lambda item: item.id):
        transformation = _domain_transformation(transformation_row)
        for capability_id in sorted(transformation.eligible_capability_ids):
            capability_row = capability_by_id.get(capability_id)
            if capability_row is None:
                continue
            capability = _domain_capability(capability_row)
            if not any(
                isinstance(spec, dict) and spec.get("state_type") == source.state_type
                for spec in transformation.input_specifications
            ):
                continue
            candidate = evaluate_transformation_route(
                source=source,
                demand=demand,
                capability=capability,
                transformation=transformation,
                unit_registry=registry,
                start_at=_deterministic_start(demand, source),
            )
            regulatory_rejections = evaluate_regulatory_eligibility(
                demand=demand,
                capability=capability,
                transformation=transformation,
            )
            candidates.append(_with_rejections(candidate, regulatory_rejections))

    candidates.sort(key=lambda item: item.id)
    return _envelope(
        request,
        {
            "source_resource_state_id": source.id,
            "target_demand_id": demand.id,
            "candidates": [_candidate_data(item) for item in candidates],
            "computed_at": datetime.now(UTC).isoformat(),
        },
    )
