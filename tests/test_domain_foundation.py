from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crr.domain import (
    DomainError,
    Quantity,
    ResourceState,
    StaleVersionError,
    TenantBoundaryError,
    TransitionKind,
    UnitDefinition,
    UnitRegistry,
    transition_state,
)

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)
UNITS = UnitRegistry(
    "units-1",
    {
        "kg": UnitDefinition("kg", "mass", Decimal("1")),
        "t": UnitDefinition("t", "mass", Decimal("1000")),
        "L": UnitDefinition("L", "volume", Decimal("1")),
    },
)


def initial_state(quantity: str = "100.000") -> ResourceState:
    return ResourceState.initial(
        resource_id="res_1",
        organization_id="org_1",
        state_type="MIXED_ALUMINUM_SCRAP",
        quantity=Quantity(quantity, "t", "units-1"),
        location_id="loc_1",
        effective_at=NOW,
        recorded_at=NOW,
        created_by="act_1",
        provenance={"source_type": "MANUAL", "captured_at": NOW.isoformat()},
        state_id="rst_1",
    )


def test_exact_quantity_accepts_decimal_strings_and_historical_zero() -> None:
    assert Quantity("100.001", "t", "units-1").value == Decimal("100.001")
    assert Quantity("0", "t", "units-1").value == Decimal("0")


@pytest.mark.parametrize("value", ["-0.001", "NaN", "Infinity", "abc"])
def test_quantity_rejects_negative_or_non_finite_values(value: str) -> None:
    with pytest.raises(DomainError):
        Quantity(value, "t", "units-1")


@pytest.mark.parametrize("value", [100.0, True])
def test_quantity_rejects_float_and_boolean(value: object) -> None:
    with pytest.raises(DomainError):
        Quantity(value, "t", "units-1")  # type: ignore[arg-type]


def test_versioned_unit_conversion_is_exact_and_dimension_safe() -> None:
    assert UNITS.convert(Quantity("1.25", "t", "units-1"), "kg").value == Decimal("1250.00")
    with pytest.raises(DomainError):
        UNITS.convert(Quantity("1", "t", "units-2"), "kg")
    with pytest.raises(DomainError):
        UNITS.convert(Quantity("1", "t", "units-1"), "L")
    assert UNITS.convert(Quantity("1", "kg", "units-1"), "t").value == Decimal("0.001")


def test_transition_preserves_predecessor_and_lineage() -> None:
    prior = initial_state()
    successor, event = transition_state(
        prior,
        expected_version=1,
        organization_id="org_1",
        actor_id="act_2",
        kind=TransitionKind.PHYSICAL_CHANGE,
        reason="Sorting and weighing at facility B",
        occurred_at=NOW,
        state_type="MIXED_ALUMINUM_SCRAP",
        quantity=Quantity("100.000", "t", "units-1"),
        location_id="loc_2",
        provenance={"source_type": "API", "record_id": "weighbridge-42"},
    )
    assert prior.quantity.value == Decimal("100.000")
    assert prior.location_id == "loc_1"
    assert successor.version == 2
    assert successor.predecessor_state_ids == (prior.id,)
    assert event.predecessor_state_id == prior.id
    assert event.successor_state_id == successor.id
    with pytest.raises(AttributeError):
        prior.location_id = "loc_2"  # type: ignore[misc]


def test_physical_change_requires_transformation_for_quantity_or_classification_change() -> None:
    prior = initial_state()
    with pytest.raises(DomainError, match="versioned Transformation"):
        transition_state(
            prior,
            expected_version=1,
            organization_id="org_1",
            actor_id="act_2",
            kind=TransitionKind.PHYSICAL_CHANGE,
            reason="Sorting",
            occurred_at=NOW,
            state_type="SORTED_ALUMINUM",
            quantity=Quantity("92", "t", "units-1"),
            location_id="loc_1",
            provenance={"source_type": "MANUAL"},
        )


def test_stale_and_cross_tenant_transitions_are_blocked() -> None:
    prior = initial_state()
    args = dict(
        expected_version=1,
        organization_id="org_1",
        actor_id="act_2",
        kind=TransitionKind.CORRECTION,
        reason="Corrected scale reading",
        occurred_at=NOW,
        state_type=prior.state_type,
        quantity=prior.quantity,
        location_id=prior.location_id,
        provenance={"source_type": "MANUAL"},
    )
    with pytest.raises(StaleVersionError):
        transition_state(prior, **(args | {"expected_version": 0}))
    with pytest.raises(TenantBoundaryError):
        transition_state(prior, **(args | {"organization_id": "org_2"}))


def test_canonical_nested_metadata_is_immutable() -> None:
    incoming = {"source": {"system": "scale-1"}, "tags": ["manual"]}
    state = ResourceState.initial(
        resource_id="res_2",
        organization_id="org_1",
        state_type="ALUMINUM",
        quantity=Quantity("5", "kg", "units-1"),
        location_id="loc_1",
        effective_at=NOW,
        created_by="act_1",
        provenance=incoming,
    )
    incoming["source"]["system"] = "forged"
    assert state.provenance["source"]["system"] == "scale-1"
    with pytest.raises(TypeError):
        state.provenance["source"]["system"] = "forged"  # type: ignore[index]
