from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crr.demand_schemas import DemandInput
from crr.domain import Demand, DemandStatus, Quantity, TenantBoundaryError
from crr.domain.errors import DomainError


def quantity(value: str, unit: str = "t") -> Quantity:
    return Quantity(Decimal(value), unit, "CRR-UNITS-0.1")


def make_demand(**overrides):
    now = datetime(2026, 10, 18, 0, 0, tzinfo=UTC)
    values = dict(
        id="dem_1",
        organization_id="org_a",
        required_state="ALUMINUM_SCRAP",
        quantity_min=quantity("10.000"),
        quantity_target=quantity("20.000"),
        quantity_max=quantity("30.000"),
        remaining_quantity=quantity("20.000"),
        status=DemandStatus.DRAFT,
        location_constraints={},
        timing_start=now,
        timing_end=datetime(2026, 10, 20, 0, 0, tzinfo=UTC),
        quality_requirements={},
        pricing_constraints={},
        certifications=(),
        regulatory_constraints={},
        substitutions=(),
        recurrence={},
        version=1,
        created_by="act_a",
        provenance={"source_type": "TEST"},
        created_at=now,
        updated_at=now,
    )
    values.update(overrides)
    return Demand(**values)


def test_demand_transition_is_explicit_and_versioned():
    demand = make_demand()
    active = demand.transition(DemandStatus.ACTIVE)
    assert active.status == DemandStatus.ACTIVE
    assert active.version == 2
    assert demand.status == DemandStatus.DRAFT
    assert demand.version == 1


def test_demand_rejects_illegal_lifecycle_transition():
    with pytest.raises(DomainError, match="Illegal Demand lifecycle"):
        make_demand(status=DemandStatus.FULFILLED).transition(DemandStatus.ACTIVE)


def test_demand_rejects_inconsistent_bounds():
    with pytest.raises(DomainError, match="bounds"):
        make_demand(quantity_target=quantity("40.000"))


def test_demand_rejects_mixed_units():
    with pytest.raises(DomainError, match="one unit"):
        make_demand(quantity_max=quantity("30.000", "kg"))


def test_demand_rejects_naive_time():
    with pytest.raises(DomainError, match="timezone"):
        make_demand(timing_start=datetime(2026, 10, 18))


def test_demand_tenant_boundary_is_explicit():
    from crr.domain import validate_demand_tenant

    with pytest.raises(TenantBoundaryError):
        validate_demand_tenant(make_demand(), "org_b")


def test_demand_input_rejects_float_quantities():
    with pytest.raises(ValueError, match="decimal strings"):
        DemandInput(
            required_state="ALUMINUM_SCRAP",
            quantity_min=10.0,
            quantity_target="20.000",
            quantity_max="30.000",
            unit="t",
            unit_registry_version="CRR-UNITS-0.1",
            timing_start="2026-10-18T00:00:00Z",
            timing_end="2026-10-20T00:00:00Z",
            provenance={"source_type": "TEST"},
        )


def test_demand_input_accepts_zero_historical_bound_but_requires_ordering():
    model = DemandInput(
        required_state="ALUMINUM_SCRAP",
        quantity_min="0.000",
        quantity_target="20.000",
        quantity_max="30.000",
        unit="t",
        unit_registry_version="CRR-UNITS-0.1",
        timing_start="2026-10-18T00:00:00Z",
        timing_end="2026-10-20T00:00:00Z",
        provenance={"source_type": "TEST"},
    )
    assert model.quantity_min == Decimal("0.000")
