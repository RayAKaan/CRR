from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crr.domain import (  # noqa: I001
    Capability,
    CapabilityStatus,
    Demand,
    DemandStatus,
    Quantity,
    ResourceState,
    Transformation,
    TransformationStatus,
    UnitRegistry,
    evaluate_transformation_route,
)
from crr.domain.errors import TenantBoundaryError


START = datetime(2026, 10, 18, 10, 0, tzinfo=UTC)
END = datetime(2026, 10, 18, 18, 0, tzinfo=UTC)


def make_route_inputs(registry: UnitRegistry, **overrides):
    source = ResourceState.initial(
        resource_id="res_1",
        organization_id="org_1",
        state_type="PET_BALE",
        quantity=Quantity(Decimal("10"), "t", registry.version),
        location_id="loc_1",
        effective_at=START,
        created_by="actor_1",
        provenance={"source": "test"},
        state_id="rst_1",
    )
    demand = Demand(
        id="dem_1",
        organization_id="org_1",
        required_state="RECYCLED_PET",
        quantity_min=Quantity(Decimal("5"), "t", registry.version),
        quantity_target=Quantity(Decimal("7"), "t", registry.version),
        quantity_max=Quantity(Decimal("10"), "t", registry.version),
        remaining_quantity=Quantity(Decimal("10"), "t", registry.version),
        status=DemandStatus.ACTIVE,
        location_constraints={},
        timing_start=START,
        timing_end=END,
        quality_requirements={},
        pricing_constraints={},
        certifications=(),
        regulatory_constraints={},
        substitutions=(),
        recurrence={},
        version=1,
        created_by="actor_2",
        provenance={"source": "test"},
        created_at=START,
        updated_at=START,
    )
    capability = Capability(
        id="cap_1",
        organization_id="org_1",
        accepted_inputs=({"state_type": "PET_BALE"},),
        output_specifications={"state_type": "RECYCLED_PET"},
        transformation_ids=("tr_1",),
        capacity=Quantity(Decimal("10"), "t", registry.version),
        minimum_batch=None,
        location_id="loc_1",
        operating_window_start=START,
        operating_window_end=END,
        processing_cost={},
        certifications=(),
        regulatory_constraints={},
        status=CapabilityStatus.ACTIVE,
        version=1,
        created_by="actor_3",
        provenance={"source": "test"},
        created_at=START,
        updated_at=START,
    )
    transformation = Transformation(
        id="tr_1",
        organization_id="org_1",
        input_specifications=({"state_type": "PET_BALE"},),
        output_specifications=({"state_type": "RECYCLED_PET"},),
        yield_min=Decimal("0.80"),
        yield_target=Decimal("0.90"),
        yield_max=Decimal("0.95"),
        loss_residuals=(),
        duration_seconds=3600,
        capacity=Quantity(Decimal("10"), "t", registry.version),
        cost_metadata={},
        quality_effects={},
        regulatory_requirements={},
        eligible_capability_ids=("cap_1",),
        eligible_location_ids=("loc_1",),
        status=TransformationStatus.ACTIVE,
        version=1,
        created_by="actor_4",
        provenance={"source": "test"},
        created_at=START,
        updated_at=START,
    )
    values = {
        "source": source,
        "demand": demand,
        "capability": capability,
        "transformation": transformation,
        "unit_registry": registry,
        "start_at": START,
    }
    values.update(overrides)
    return values


def evaluate(registry, **overrides):
    return evaluate_transformation_route(**make_route_inputs(registry, **overrides))


def test_transformation_route_is_feasible(registry):
    candidate = evaluate(registry)
    assert candidate.status == "FEASIBLE"
    assert candidate.rejections == ()
    assert candidate.legs[0].kind == "TRANSFORMATION"
    assert candidate.provenance["capability_version"] == 1
    assert candidate.provenance["transformation_version"] == 1


def test_inactive_capability_is_blocked(registry):
    capability = make_route_inputs(registry)["capability"].transition(CapabilityStatus.SUSPENDED)
    candidate = evaluate(registry, capability=capability)
    assert candidate.status == "INFEASIBLE"
    assert any(item.code == "CAPABILITY_INACTIVE" for item in candidate.rejections)


def test_insufficient_yield_is_blocked(registry):
    transformation = make_route_inputs(registry)["transformation"]
    transformation = Transformation(
        id=transformation.id,
        organization_id=transformation.organization_id,
        input_specifications=transformation.input_specifications,
        output_specifications=transformation.output_specifications,
        yield_min=Decimal("0.40"),
        yield_target=Decimal("0.60"),
        yield_max=Decimal("0.80"),
        loss_residuals=transformation.loss_residuals,
        duration_seconds=transformation.duration_seconds,
        capacity=transformation.capacity,
        cost_metadata=transformation.cost_metadata,
        quality_effects=transformation.quality_effects,
        regulatory_requirements=transformation.regulatory_requirements,
        eligible_capability_ids=transformation.eligible_capability_ids,
        eligible_location_ids=transformation.eligible_location_ids,
        status=transformation.status,
        version=transformation.version,
        created_by=transformation.created_by,
        provenance=transformation.provenance,
        created_at=transformation.created_at,
        updated_at=transformation.updated_at,
    )
    candidate = evaluate(registry, transformation=transformation)
    assert candidate.status == "INFEASIBLE"
    assert any(item.code == "INSUFFICIENT_QUANTITY" for item in candidate.rejections)


def test_capacity_is_blocked(registry):
    capability = make_route_inputs(registry)["capability"]
    capability = Capability(
        id=capability.id,
        organization_id=capability.organization_id,
        accepted_inputs=capability.accepted_inputs,
        output_specifications=capability.output_specifications,
        transformation_ids=capability.transformation_ids,
        capacity=Quantity(Decimal("5"), "t", registry.version),
        minimum_batch=capability.minimum_batch,
        location_id=capability.location_id,
        operating_window_start=capability.operating_window_start,
        operating_window_end=capability.operating_window_end,
        processing_cost=capability.processing_cost,
        certifications=capability.certifications,
        regulatory_constraints=capability.regulatory_constraints,
        status=capability.status,
        version=capability.version,
        created_by=capability.created_by,
        provenance=capability.provenance,
        created_at=capability.created_at,
        updated_at=capability.updated_at,
    )
    candidate = evaluate(registry, capability=capability)
    assert candidate.status == "INFEASIBLE"
    assert any(item.code == "CAPACITY_INSUFFICIENT" for item in candidate.rejections)


def test_time_window_conflict_is_blocked(registry):
    candidate = evaluate(registry, start_at=datetime(2026, 10, 18, 17, 30, tzinfo=UTC))
    assert candidate.status == "INFEASIBLE"
    assert any(item.code == "TIME_WINDOW_CONFLICT" for item in candidate.rejections)


def test_state_mismatch_is_blocked(registry):
    source = make_route_inputs(registry)["source"]
    source = ResourceState.initial(
        resource_id=source.resource_id,
        organization_id=source.organization_id,
        state_type="ALUMINIUM_INGOT",
        quantity=source.quantity,
        location_id=source.location_id,
        effective_at=source.effective_at,
        created_by=source.created_by,
        provenance=source.provenance,
        state_id=source.id,
    )
    candidate = evaluate(registry, source=source)
    assert candidate.status == "INFEASIBLE"
    assert any(item.code == "STATE_MISMATCH" for item in candidate.rejections)


def test_cross_tenant_reference_is_rejected(registry):
    capability = make_route_inputs(registry)["capability"]
    capability = Capability(
        id=capability.id,
        organization_id="org_2",
        accepted_inputs=capability.accepted_inputs,
        output_specifications=capability.output_specifications,
        transformation_ids=capability.transformation_ids,
        capacity=capability.capacity,
        minimum_batch=capability.minimum_batch,
        location_id=capability.location_id,
        operating_window_start=capability.operating_window_start,
        operating_window_end=capability.operating_window_end,
        processing_cost=capability.processing_cost,
        certifications=capability.certifications,
        regulatory_constraints=capability.regulatory_constraints,
        status=capability.status,
        version=capability.version,
        created_by=capability.created_by,
        provenance=capability.provenance,
        created_at=capability.created_at,
        updated_at=capability.updated_at,
    )
    with pytest.raises(TenantBoundaryError):
        evaluate(registry, capability=capability)


def test_routing_does_not_mutate_canonical_inputs(registry):
    values = make_route_inputs(registry)
    source_before = values["source"]
    demand_before = values["demand"]
    capability_before = values["capability"]
    transformation_before = values["transformation"]
    evaluate_transformation_route(**values)
    assert values["source"] == source_before
    assert values["demand"] == demand_before
    assert values["capability"] == capability_before
    assert values["transformation"] == transformation_before
