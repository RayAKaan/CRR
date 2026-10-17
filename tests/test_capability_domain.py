from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crr.domain import Capability, CapabilityStatus, DomainError, Quantity, TenantBoundaryError


def make_capability(status: CapabilityStatus = CapabilityStatus.DRAFT) -> Capability:
    now = datetime(2026, 10, 18, 8, tzinfo=UTC)
    return Capability(
        id="cap_1",
        organization_id="org_a",
        accepted_inputs=({"state_type": "ALUMINUM_SCRAP"},),
        output_specifications={"state_type": "ALUMINUM_BILLET"},
        transformation_ids=("trn_future",),
        capacity=Quantity(Decimal("100.000"), "t", "CRR-UNITS-0.1"),
        minimum_batch=Quantity(Decimal("10.000"), "t", "CRR-UNITS-0.1"),
        location_id="loc_a",
        operating_window_start=now,
        operating_window_end=datetime(2026, 10, 18, 18, tzinfo=UTC),
        processing_cost={"currency": "SAR"},
        certifications=("CERT-A",),
        regulatory_constraints={"eligible": True},
        status=status,
        version=1,
        created_by="act_a",
        provenance={"source_type": "TEST"},
        created_at=now,
        updated_at=now,
    )


def test_capability_lifecycle_is_explicit_and_versioned() -> None:
    capability = make_capability()
    active = capability.transition(CapabilityStatus.ACTIVE)
    assert active.status is CapabilityStatus.ACTIVE
    assert active.version == 2
    suspended = active.transition(CapabilityStatus.SUSPENDED)
    assert suspended.version == 3
    with pytest.raises(DomainError):
        suspended.transition(CapabilityStatus.ACTIVE)


def test_capability_rejects_invalid_batch_and_window() -> None:
    capability = make_capability()
    with pytest.raises(DomainError):
        Capability(
            **{**capability.__dict__, "minimum_batch": Quantity(Decimal("101"), "t", "CRR-UNITS-0.1")}
        )


def test_capability_rejects_mixed_batch_unit() -> None:
    capability = make_capability()
    with pytest.raises(DomainError):
        Capability(
            id=capability.id,
            organization_id=capability.organization_id,
            accepted_inputs=capability.accepted_inputs,
            output_specifications=capability.output_specifications,
            transformation_ids=capability.transformation_ids,
            capacity=capability.capacity,
            minimum_batch=Quantity(Decimal("1"), "kg", "CRR-UNITS-0.1"),
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


def test_capability_requires_timezone_and_provenance() -> None:
    capability = make_capability()
    with pytest.raises(DomainError):
        Capability(
            id=capability.id,
            organization_id=capability.organization_id,
            accepted_inputs=capability.accepted_inputs,
            output_specifications=capability.output_specifications,
            transformation_ids=capability.transformation_ids,
            capacity=capability.capacity,
            minimum_batch=capability.minimum_batch,
            location_id=capability.location_id,
            operating_window_start=datetime(2026, 10, 18, 8),
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


def test_capability_tenant_boundary() -> None:
    capability = make_capability()
    with pytest.raises(TenantBoundaryError):
        from crr.domain import validate_capability_tenant

        validate_capability_tenant(capability, "org_b")
