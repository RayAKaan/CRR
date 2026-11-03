from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity
from crr.domain.reservation import (
    Reservation,
    ReservationStatus,
    active_reserved_quantity,
    validate_reservation_capacity,
)

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
        already_reserved_for_agreement=quantity("0"),
    )
    with pytest.raises(DomainError):
        validate_reservation_capacity(
            requested=quantity("5.001"),
            agreement_quantity=quantity("10"),
            state_quantity=quantity("20"),
            already_reserved=quantity("15"),
        already_reserved_for_agreement=quantity("0"),
        )


def test_capacity_rejects_quantity_above_agreement_or_incompatible_units():
    with pytest.raises(DomainError):
        validate_reservation_capacity(
            requested=quantity("11"),
            agreement_quantity=quantity("10"),
            state_quantity=quantity("20"),
            already_reserved=quantity("0"),
            already_reserved_for_agreement=quantity("0"),
        )
    with pytest.raises(DomainError):
        validate_reservation_capacity(
            requested=quantity("1"),
            agreement_quantity=quantity("10", "kg"),
            state_quantity=quantity("20"),
            already_reserved=quantity("0"),
            already_reserved_for_agreement=quantity("0"),
        )


def test_release_is_versioned_attributed_and_terminal():
    reservation = make_reservation()
    released = reservation.release(actor_id="act_2", at=NOW + timedelta(hours=1))
    assert released.status is ReservationStatus.RELEASED
    assert released.version == reservation.version + 1
    assert released.provenance["last_transition_actor_id"] == "act_2"
    with pytest.raises(DomainError):
        released.release(actor_id="act_2", at=NOW + timedelta(hours=2))


def test_expiry_requires_expiry_instant_and_is_terminal():
    reservation = make_reservation()
    with pytest.raises(DomainError):
        reservation.expire(at=NOW + timedelta(hours=1))
    expired = reservation.expire(at=reservation.expires_at)
    assert expired.status is ReservationStatus.EXPIRED
    assert expired.version == 2
    with pytest.raises(DomainError):
        expired.expire(at=reservation.expires_at + timedelta(seconds=1))


def test_active_allocation_ignores_released_and_expired_reservations():
    active = make_reservation(quantity=quantity("3"))
    released = make_reservation(
        id="rsv_2",
        quantity=quantity("5"),
        status=ReservationStatus.RELEASED,
    )
    expired = make_reservation(
        id="rsv_3",
        quantity=quantity("7"),
        created_at=NOW - timedelta(days=2),
        updated_at=NOW - timedelta(days=2),
        expires_at=NOW - timedelta(days=1),
    )
    total = active_reserved_quantity(
        [active, released, expired],
        now=NOW,
        unit="t",
        unit_registry_version="CRR-UNITS-0.1",
    )
    assert total.value == Decimal("3")


def test_active_allocation_rejects_incompatible_unit_and_naive_clock():
    incompatible = make_reservation(quantity=quantity("2", "kg"))
    with pytest.raises(DomainError):
        active_reserved_quantity(
            [incompatible],
            now=NOW,
            unit="t",
            unit_registry_version="CRR-UNITS-0.1",
        )
    with pytest.raises(DomainError):
        active_reserved_quantity(
            [],
            now=NOW.replace(tzinfo=None),
            unit="t",
            unit_registry_version="CRR-UNITS-0.1",
        )
