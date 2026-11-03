from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity
from crr.domain.reservation import Reservation, ReservationStatus, validate_reservation_capacity

NOW = datetime(2026, 11, 3, 12, tzinfo=UTC)


def quantity(value: str, unit: str = "t") -> Quantity:
    return Quantity(Decimal(value), unit, "CRR-UNITS-0.1")


def make_reservation(**overrides) -> Reservation:
    values = {
        "id": "rsv_1",
        "organization_id": "org_1",
        "agreement_id": "agr_1",
        "resource_id": "res_1",
        "resource_state_id": "rst_1",
        "resource_version": 3,
        "quantity": quantity("10.250"),
        "status": ReservationStatus.ACTIVE,
        "expires_at": NOW + timedelta(days=2),
        "version": 1,
        "created_by": "act_1",
        "created_at": NOW,
        "updated_at": NOW,
        "provenance": {"source_type": "CRR_API"},
    }
    values.update(overrides)
    return Reservation(**values)


def test_reservation_requires_positive_exact_quantity_and_aware_expiry():
    with pytest.raises(DomainError):
        make_reservation(quantity=quantity("0"))
    with pytest.raises(DomainError):
        make_reservation(expires_at=NOW.replace(tzinfo=None))
    with pytest.raises(DomainError):
        make_reservation(expires_at=NOW)
    with pytest.raises(DomainError):
        make_reservation(resource_version=0)


def test_reservation_enforces_tenant_boundary():
    with pytest.raises(TenantBoundaryError):
        make_reservation().validate_tenant("org_other")


def test_capacity_allows_exact_fit_and_rejects_over_allocation():
    validate_reservation_capacity(
        requested=quantity("5"),
        agreement_quantity=quantity("10"),
        state_quantity=quantity("20"),
        already_reserved=quantity("15"),
    )
    with pytest.raises(DomainError):
        validate_reservation_capacity(
            requested=quantity("5.001"),
            agreement_quantity=quantity("10"),
            state_quantity=quantity("20"),
            already_reserved=quantity("15"),
        )


def test_capacity_rejects_quantity_above_agreement_or_incompatible_units():
    with pytest.raises(DomainError):
        validate_reservation_capacity(
            requested=quantity("11"),
            agreement_quantity=quantity("10"),
            state_quantity=quantity("20"),
            already_reserved=quantity("0"),
        )
    with pytest.raises(DomainError):
        validate_reservation_capacity(
            requested=quantity("1"),
            agreement_quantity=quantity("10", "kg"),
            state_quantity=quantity("20"),
            already_reserved=quantity("0"),
        )
