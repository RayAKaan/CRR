from datetime import UTC, datetime
from decimal import Decimal

from crr.domain import (
    Capability,
    CapabilityStatus,
    Demand,
    DemandStatus,
    Quantity,
    Transformation,
    TransformationStatus,
    evaluate_regulatory_eligibility,
)

NOW = datetime(2026, 10, 18, 12, tzinfo=UTC)


def capability(**overrides):
    values = {
        "id": "cap_a",
        "organization_id": "org_a",
        "accepted_inputs": ({"state_type": "SCRAP"},),
        "output_specifications": {"state_type": "BILLET"},
        "transformation_ids": ("trn_a",),
        "capacity": Quantity(Decimal("100.000"), "t", "CRR-UNITS-0.1"),
        "minimum_batch": None,
        "location_id": "loc_a",
        "operating_window_start": datetime(2026, 10, 18, 8, tzinfo=UTC),
        "operating_window_end": datetime(2026, 10, 18, 18, tzinfo=UTC),
        "processing_cost": {},
        "certifications": ("CERT-A",),
        "regulatory_constraints": {"eligible": True, "safety_controls": {"guarded": True}},
        "status": CapabilityStatus.ACTIVE,
        "version": 1,
        "created_by": "act_a",
        "provenance": {"source_type": "TEST"},
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return Capability(**values)


def demand(**overrides):
    values = {
        "id": "dem_a",
        "organization_id": "org_a",
        "required_state": "BILLET",
        "quantity_min": Quantity(Decimal("10.000"), "t", "CRR-UNITS-0.1"),
        "quantity_target": Quantity(Decimal("20.000"), "t", "CRR-UNITS-0.1"),
        "quantity_max": Quantity(Decimal("30.000"), "t", "CRR-UNITS-0.1"),
        "remaining_quantity": Quantity(Decimal("20.000"), "t", "CRR-UNITS-0.1"),
        "status": DemandStatus.ACTIVE,
        "location_constraints": {},
        "timing_start": datetime(2026, 10, 18, 8, tzinfo=UTC),
        "timing_end": datetime(2026, 10, 18, 18, tzinfo=UTC),
        "quality_requirements": {},
        "pricing_constraints": {},
        "certifications": (),
        "regulatory_constraints": {},
        "substitutions": (),
        "recurrence": {},
        "version": 1,
        "created_by": "act_a",
        "provenance": {"source_type": "TEST"},
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return Demand(**values)


def transformation(**overrides):
    values = {
        "id": "trn_a",
        "organization_id": "org_a",
        "input_specifications": ({"state_type": "SCRAP"},),
        "output_specifications": ({"state_type": "BILLET"},),
        "yield_min": Decimal("0.900"),
        "yield_target": Decimal("0.950"),
        "yield_max": Decimal("1.000"),
        "loss_residuals": (),
        "duration_seconds": 3600,
        "capacity": Quantity(Decimal("100.000"), "t", "CRR-UNITS-0.1"),
        "cost_metadata": {},
        "quality_effects": {},
        "regulatory_requirements": {},
        "eligible_capability_ids": ("cap_a",),
        "eligible_location_ids": ("loc_a",),
        "status": TransformationStatus.ACTIVE,
        "version": 1,
        "created_by": "act_a",
        "provenance": {"source_type": "TEST"},
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return Transformation(**values)


def test_required_certification_and_control_are_enforced():
    result = evaluate_regulatory_eligibility(
        demand=demand(),
        capability=capability(),
        transformation=transformation(
            regulatory_requirements={
                "required_certifications": ["CERT-B"],
                "required_controls": {"eligible": True},
            }
        ),
    )
    assert {item.code for item in result} == {"REGULATORY_BLOCK"}
    assert len(result) == 2


def test_safety_control_is_hard_blocking():
    result = evaluate_regulatory_eligibility(
        demand=demand(),
        capability=capability(
            regulatory_constraints={"eligible": True, "safety_controls": {}}
        ),
        transformation=transformation(
            regulatory_requirements={"required_safety_controls": ["guarded"]}
        ),
    )
    assert result[0].code == "SAFETY_BLOCK"


def test_unresolved_regulatory_uncertainty_is_not_inferred_as_permission():
    result = evaluate_regulatory_eligibility(
        demand=demand(),
        capability=capability(),
        transformation=transformation(
            regulatory_requirements={"regulatory_uncertainty": True}
        ),
    )
    assert result[0].code == "REGULATORY_BLOCK"
