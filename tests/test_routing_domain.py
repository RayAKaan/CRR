from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crr.domain import Quantity, UnitDefinition, UnitRegistry, evaluate_direct_route
from crr.domain.errors import TenantBoundaryError


@pytest.fixture
def registry() -> UnitRegistry:
    return UnitRegistry(
        version="CRR-UNITS-0.1",
        units={
            "kg": UnitDefinition("kg", "MASS", Decimal("1000")),
            "t": UnitDefinition("t", "MASS", Decimal("1000000")),
        },
    )


def evaluate(registry, **overrides):
    values = {
        "source_id": "rst_1",
        "source_version": 1,
        "source_organization_id": "org_1",
        "source_state_type": "PET_BALE",
        "source_quantity": Quantity(Decimal("10"), "t", registry.version),
        "demand_id": "dem_1",
        "demand_version": 1,
        "demand_organization_id": "org_1",
        "demand_state_type": "PET_BALE",
        "demand_min": Quantity(Decimal("5"), "t", registry.version),
        "demand_max": Quantity(Decimal("12"), "t", registry.version),
        "demand_active": True,
        "unit_registry": registry,
        "evaluated_at": datetime(2026, 10, 18, tzinfo=UTC),
    }
    values.update(overrides)
    return evaluate_direct_route(**values)


def test_direct_route_is_feasible(registry):
    candidate = evaluate(registry)
    assert candidate.status == "FEASIBLE"
    assert candidate.rejections == ()


def test_zero_quantity_is_not_routing_supply(registry):
    candidate = evaluate(registry, source_quantity=Quantity(Decimal("0"), "t", registry.version))
    assert candidate.status == "INFEASIBLE"
    assert candidate.rejections[0].code == "INSUFFICIENT_QUANTITY"


def test_inactive_demand_is_infeasible(registry):
    candidate = evaluate(registry, demand_active=False)
    assert candidate.status == "INFEASIBLE"
    assert candidate.rejections[0].code == "DEMAND_EXPIRED"


def test_state_mismatch_is_infeasible(registry):
    candidate = evaluate(registry, demand_state_type="ALUMINIUM_INGOT")
    assert candidate.status == "INFEASIBLE"
    assert any(item.code == "STATE_MISMATCH" for item in candidate.rejections)


def test_unit_incompatibility_is_infeasible(registry):
    candidate = evaluate(
        registry,
        demand_min=Quantity(Decimal("1"), "m3", registry.version),
        demand_max=Quantity(Decimal("2"), "m3", registry.version),
    )
    assert candidate.status == "INFEASIBLE"
    assert any(item.code == "UNIT_INCOMPATIBLE" for item in candidate.rejections)


def test_tenant_boundary_is_rejected(registry):
    with pytest.raises(TenantBoundaryError):
        evaluate(registry, demand_organization_id="org_2")


def test_routing_evaluation_is_deterministic(registry):
    first = evaluate(registry)
    second = evaluate(registry)
    assert first.status == second.status
    assert first.legs == second.legs
    assert first.rejections == second.rejections
    assert first.source_version == second.source_version
    assert first.target_version == second.target_version
