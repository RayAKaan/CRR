from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity
from crr.domain.reservation import Reservation, ReservationStatus
from crr.domain.transaction import (
    Transaction,
    TransactionStatus,
    validate_transaction_reservation_coverage,
)

NOW = datetime(2026, 11, 3, 12, tzinfo=UTC)


def make_transaction(**overrides) -> Transaction:
    values = {
        "id": "txn_1",
        "organization_id": "org_1",
        "agreement_id": "agr_1",
        "opportunity_id": "opp_1",
        "route_candidate_id": "route_1",
        "resource_id": "res_1",
        "resource_state_id": "rst_1",
        "resource_version": 3,
        "proposer_actor_id": "act_seller",
        "recipient_actor_id": "act_buyer",
        "quantity": Quantity(Decimal("10.250"), "t", "CRR-UNITS-0.1"),
        "price": Decimal("125.50"),
        "currency": "SAR",
        "terms_snapshot": '{"quantity":{"value":"10.250","unit":"t"}}',
        "reservation_ids": ("rsv_1", "rsv_2"),
        "status": TransactionStatus.AGREED,
        "version": 1,
        "created_by": "act_buyer",
        "created_at": NOW,
        "updated_at": NOW,
        "provenance": {"source_type": "CRR_API"},
    }
    values.update(overrides)
    return Transaction(**values)


def test_transaction_preserves_exact_commercial_terms_and_reservation_links():
    transaction = make_transaction()
    assert transaction.status is TransactionStatus.AGREED
    assert transaction.quantity.value == Decimal("10.250")
    assert transaction.price == Decimal("125.50")
    assert transaction.reservation_ids == ("rsv_1", "rsv_2")


def test_transaction_requires_distinct_parties_and_positive_versions():
    with pytest.raises(DomainError):
        make_transaction(recipient_actor_id="act_seller")
    with pytest.raises(DomainError):
        make_transaction(resource_version=0)
    with pytest.raises(DomainError):
        make_transaction(version=0)


def test_transaction_requires_exact_positive_quantity_and_nonnegative_price():
    with pytest.raises(DomainError):
        make_transaction(quantity=Quantity(Decimal("0"), "t", "CRR-UNITS-0.1"))
    with pytest.raises(DomainError):
        make_transaction(price=Decimal("-0.01"))


def test_transaction_requires_unique_reservation_references():
    with pytest.raises(DomainError):
        make_transaction(reservation_ids=("rsv_1", "rsv_1"))
    with pytest.raises(DomainError):
        make_transaction(reservation_ids=())


def test_transaction_requires_valid_currency_terms_and_aware_timestamps():
    with pytest.raises(DomainError):
        make_transaction(currency="sar")
    with pytest.raises(DomainError):
        make_transaction(terms_snapshot="not-json")
    with pytest.raises(DomainError):
        make_transaction(created_at=NOW.replace(tzinfo=None))
    with pytest.raises(DomainError):
        make_transaction(updated_at=NOW.replace(tzinfo=None))
    with pytest.raises(DomainError):
        make_transaction(updated_at=NOW.replace(day=2))


def test_transaction_enforces_tenant_boundary():
    with pytest.raises(TenantBoundaryError):
        make_transaction().validate_tenant("org_other")



def make_reservation(
    reservation_id: str,
    quantity: str,
    **overrides,
) -> Reservation:
    values = {
        "id": reservation_id,
        "organization_id": "org_1",
        "agreement_id": "agr_1",
        "resource_id": "res_1",
        "resource_state_id": "rst_1",
        "resource_version": 3,
        "quantity": Quantity(Decimal(quantity), "t", "CRR-UNITS-0.1"),
        "status": ReservationStatus.ACTIVE,
        "expires_at": NOW + timedelta(days=1),
        "version": 1,
        "created_by": "act_buyer",
        "created_at": NOW,
        "updated_at": NOW,
        "provenance": {"source_type": "TEST"},
    }
    values.update(overrides)
    return Reservation(**values)


def test_transaction_schedule_dispute_resolve_and_cancel_are_versioned():
    transaction = make_transaction()
    scheduled_for = NOW + timedelta(days=2)
    scheduled = transaction.schedule(
        actor_id="act_buyer",
        at=NOW + timedelta(minutes=1),
        scheduled_for=scheduled_for,
    )
    assert scheduled.status is TransactionStatus.SCHEDULED
    assert scheduled.scheduled_for == scheduled_for
    assert scheduled.version == 2

    disputed = scheduled.dispute(
        actor_id="act_seller",
        at=NOW + timedelta(minutes=2),
        reason="Delivery window needs confirmation",
    )
    assert disputed.status is TransactionStatus.DISPUTED
    assert disputed.provenance["dispute_reason"] == "Delivery window needs confirmation"

    resolved = disputed.resolve(
        actor_id="act_operator",
        at=NOW + timedelta(minutes=3),
        scheduled_for=NOW + timedelta(days=3),
        resolution_note="Both parties confirmed the revised window",
    )
    assert resolved.status is TransactionStatus.SCHEDULED
    assert resolved.version == 4
    assert resolved.provenance["resolution_note"] == "Both parties confirmed the revised window"

    cancelled = resolved.cancel(
        actor_id="act_buyer",
        at=NOW + timedelta(minutes=4),
        reason="Parties mutually cancelled",
    )
    assert cancelled.status is TransactionStatus.CANCELLED
    assert cancelled.version == 5
    with pytest.raises(DomainError):
        cancelled.cancel(
            actor_id="act_buyer",
            at=NOW + timedelta(minutes=5),
            reason="Duplicate cancellation",
        )


def test_transaction_lifecycle_rejects_invalid_actor_time_and_missing_reason():
    transaction = make_transaction()
    with pytest.raises(DomainError):
        transaction.schedule(
            actor_id="act_outsider",
            at=NOW + timedelta(minutes=1),
            scheduled_for=NOW + timedelta(days=1),
        )
    with pytest.raises(DomainError):
        transaction.schedule(
            actor_id="act_buyer",
            at=NOW,
            scheduled_for=NOW,
        )
    with pytest.raises(DomainError):
        transaction.dispute(
            actor_id="act_buyer",
            at=NOW + timedelta(minutes=1),
            reason=" ",
        )
    with pytest.raises(DomainError):
        transaction.cancel(
            actor_id="act_buyer",
            at=NOW + timedelta(minutes=1),
            reason=" ",
        )


def test_transaction_requires_schedule_in_scheduled_state():
    with pytest.raises(DomainError):
        make_transaction(status=TransactionStatus.SCHEDULED)


def test_transaction_requires_exact_active_reservation_coverage():
    reservations = [
        make_reservation("rsv_1", "4.000"),
        make_reservation("rsv_2", "6.250"),
    ]
    validate_transaction_reservation_coverage(
        organization_id="org_1",
        agreement_id="agr_1",
        resource_id="res_1",
        resource_state_id="rst_1",
        resource_version=3,
        agreement_status="ACTIVE",
        agreed_quantity=Quantity(Decimal("10.250"), "t", "CRR-UNITS-0.1"),
        reservations=reservations,
        now=NOW,
    )
    with pytest.raises(DomainError):
        validate_transaction_reservation_coverage(
            organization_id="org_1",
            agreement_id="agr_1",
            resource_id="res_1",
            resource_state_id="rst_1",
            resource_version=3,
            agreement_status="ACTIVE",
            agreed_quantity=Quantity(Decimal("10.251"), "t", "CRR-UNITS-0.1"),
            reservations=reservations,
            now=NOW,
        )


def test_transaction_allocation_rejects_stale_inactive_and_cross_tenant_reservations():
    invalid_reservations = [
        make_reservation("rsv_state", "10.250", resource_state_id="rst_old"),
        make_reservation("rsv_version", "10.250", resource_version=2),
        make_reservation("rsv_released", "10.250", status=ReservationStatus.RELEASED),
        make_reservation("rsv_tenant", "10.250", organization_id="org_other"),
    ]
    for reservation in invalid_reservations:
        with pytest.raises(DomainError):
            validate_transaction_reservation_coverage(
                organization_id="org_1",
                agreement_id="agr_1",
                resource_id="res_1",
                resource_state_id="rst_1",
                resource_version=3,
                agreement_status="ACTIVE",
                agreed_quantity=Quantity(Decimal("10.250"), "t", "CRR-UNITS-0.1"),
                reservations=[reservation],
                now=NOW,
            )
    with pytest.raises(DomainError):
        validate_transaction_reservation_coverage(
            organization_id="org_1",
            agreement_id="agr_1",
            resource_id="res_1",
            resource_state_id="rst_1",
            resource_version=3,
            agreement_status="CANCELLED",
            agreed_quantity=Quantity(Decimal("10.250"), "t", "CRR-UNITS-0.1"),
            reservations=[make_reservation("rsv_2", "10.250")],
            now=NOW,
        )
