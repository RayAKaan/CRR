from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.quantity import Quantity
from crr.domain.transaction import Transaction, TransactionStatus

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
    assert transaction.status is TransactionStatus.COMMITTED
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
