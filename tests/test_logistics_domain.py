from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from crr.domain import (
    DomainError,
    Quantity,
    TenantBoundaryError,
    TransportMode,
    UnitDefinition,
    UnitRegistry,
    evaluate_logistics_leg,
)


@pytest.fixture
def registry() -> UnitRegistry:
    return UnitRegistry(
        version="CRR-UNITS-0.1",
        units={
            "kg": UnitDefinition("kg", "MASS", Decimal("1")),
            "t": UnitDefinition("t", "MASS", Decimal("1000")),
            "l": UnitDefinition("l", "VOLUME", Decimal("1")),
        },
    )


def evaluate(registry: UnitRegistry, **overrides):
    values = {
        "organization_id": "org_1",
        "source_organization_id": "org_1",
        "destination_organization_id": "org_1",
        "source_location_id": "loc_source",
        "destination_location_id": "loc_destination",
        "expected_source_location_id": "loc_source",
        "expected_destination_location_id": "loc_destination",
        "source_quantity": Quantity(Decimal("10"), "t", registry.version),
        "transport_capacity": Quantity(Decimal("12"), "t", registry.version),
        "transport_mode": TransportMode.ROAD,
        "distance_km": Decimal("125.500"),
        "travel_duration_seconds": 3600,
        "start_at": datetime(2026, 10, 18, 8, tzinfo=UTC),
        "destination_window_start": datetime(2026, 10, 18, 9, tzinfo=UTC),
        "destination_window_end": datetime(2026, 10, 18, 12, tzinfo=UTC),
        "unit_registry": registry,
    }
    values.update(overrides)
    return evaluate_logistics_leg(**values)


def test_feasible_logistics_leg(registry):
    result = evaluate(registry)
    assert result.feasible is True
    assert result.rejections == ()
    assert result.arrival_at == datetime(2026, 10, 18, 9, tzinfo=UTC)


def test_location_mismatch_is_hard_failure(registry):
    result = evaluate(registry, destination_location_id="loc_other")
    assert result.feasible is False
    assert result.rejections[0].code == "LOCATION_INFEASIBLE"


def test_cross_tenant_endpoints_are_rejected(registry):
    with pytest.raises(TenantBoundaryError):
        evaluate(registry, destination_organization_id="org_2")


def test_wrong_request_tenant_is_rejected(registry):
    with pytest.raises(TenantBoundaryError):
        evaluate(registry, organization_id="org_2")


@pytest.mark.parametrize(
    ("field", "value"),
    [("distance_km", Decimal("-1")), ("travel_duration_seconds", -1)],
)
def test_negative_transport_assumptions_are_rejected(registry, field, value):
    with pytest.raises(DomainError):
        evaluate(registry, **{field: value})


def test_negative_max_distance_is_rejected(registry):
    with pytest.raises(DomainError):
        evaluate(registry, max_distance_km=Decimal("-0.1"))


def test_transport_capacity_is_enforced(registry):
    result = evaluate(
        registry,
        transport_capacity=Quantity(Decimal("9.999"), "t", registry.version),
    )
    assert result.feasible is False
    assert any(item.code == "CAPACITY_INSUFFICIENT" for item in result.rejections)


def test_unit_incompatibility_is_reported(registry):
    result = evaluate(
        registry,
        transport_capacity=Quantity(Decimal("100"), "l", registry.version),
    )
    assert result.feasible is False
    assert any(item.code == "UNIT_INCOMPATIBLE" for item in result.rejections)


def test_zero_quantity_is_not_routing_supply(registry):
    result = evaluate(
        registry,
        source_quantity=Quantity(Decimal("0"), "t", registry.version),
    )
    assert result.feasible is False
    assert any(item.code == "INSUFFICIENT_QUANTITY" for item in result.rejections)


def test_destination_window_conflict_is_hard_failure(registry):
    result = evaluate(
        registry,
        destination_window_start=datetime(2026, 10, 18, 10, tzinfo=UTC),
        destination_window_end=datetime(2026, 10, 18, 11, tzinfo=UTC),
    )
    assert result.feasible is False
    assert any(item.code == "TIME_WINDOW_CONFLICT" for item in result.rejections)


def test_max_distance_is_enforced(registry):
    result = evaluate(registry, max_distance_km=Decimal("100"))
    assert result.feasible is False
    assert any(item.code == "LOCATION_INFEASIBLE" for item in result.rejections)


def test_naive_datetimes_are_rejected(registry):
    with pytest.raises(DomainError):
        evaluate(registry, start_at=datetime(2026, 10, 18, 8))


def test_exact_distance_rejects_float(registry):
    with pytest.raises(DomainError):
        evaluate(registry, distance_km=125.5)


def test_repeated_evaluation_is_deterministic(registry):
    first = evaluate(registry)
    second = evaluate(registry)
    assert first.feasible == second.feasible
    assert first.rejections == second.rejections
    assert first.arrival_at == second.arrival_at
    assert first.provenance == second.provenance


def test_arrival_is_derived_from_duration(registry):
    result = evaluate(registry, travel_duration_seconds=5400)
    assert result.arrival_at == datetime(2026, 10, 18, 9, 30, tzinfo=UTC)


def test_destination_window_start_after_end_is_invalid(registry):
    with pytest.raises(DomainError):
        evaluate(
            registry,
            destination_window_start=datetime(2026, 10, 18, 12, tzinfo=UTC),
            destination_window_end=datetime(2026, 10, 18, 11, tzinfo=UTC),
        )


def test_distance_boundary_is_feasible(registry):
    result = evaluate(registry, max_distance_km=Decimal("125.500"))
    assert result.feasible is True


def test_arrival_after_window_is_rejected(registry):
    result = evaluate(
        registry,
        travel_duration_seconds=int(timedelta(hours=5).total_seconds()),
    )
    assert result.feasible is False
    assert any(item.code == "TIME_WINDOW_CONFLICT" for item in result.rejections)
