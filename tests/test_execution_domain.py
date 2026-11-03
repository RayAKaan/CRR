from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.execution import Execution, ExecutionStatus
from crr.domain.quantity import Quantity
from crr.domain.transaction import Transaction, TransactionStatus

NOW = datetime(2026, 11, 3, 12, tzinfo=UTC)


def make_transaction(**overrides) -> Transaction:
    values = {
        "id": "txn_1",
        "organization_id": "org_1",
        "agreement_id": "agr_1",
        "offer_id": "off_1",
        "offer_version": 2,
        "opportunity_id": "opp_1",
        "opportunity_version": 4,
        "route_candidate_id": "route_1",
        "resource_id": "res_1",
        "resource_state_id": "rst_1",
        "resource_version": 3,
        "proposer_actor_id": "act_seller",
        "recipient_actor_id": "act_buyer",
        "quantity": Quantity(Decimal("10.250"), "t", "CRR-UNITS-0.1"),
        "price": Decimal("125.50"),
        "currency": "SAR",
        "terms_snapshot": (
            '{"quantity":{"value":"10.250","unit":"t",'
            '"unit_registry_version":"CRR-UNITS-0.1"},"price":"125.50","currency":"SAR",'
            '"valid_from":"2026-11-01T00:00:00+00:00",'
            '"valid_until":"2026-12-01T00:00:00+00:00"}'
        ),
        "reservation_ids": ("rsv_1",),
        "status": TransactionStatus.SCHEDULED,
        "version": 2,
        "created_by": "act_buyer",
        "created_at": NOW,
        "updated_at": NOW,
        "provenance": {"source_type": "CRR_API"},
        "scheduled_for": NOW + timedelta(days=2),
    }
    values.update(overrides)
    return Transaction(**values)


def test_execution_is_created_as_a_planned_snapshot_of_scheduled_transaction():
    transaction = make_transaction()
    execution = Execution.from_transaction(
        transaction,
        execution_id="exe_1",
        actor_id="act_buyer",
        at=NOW + timedelta(minutes=1),
    )
    assert execution.status is ExecutionStatus.PLANNED
    assert execution.version == 1
    assert execution.transaction_id == transaction.id
    assert execution.agreement_id == transaction.agreement_id
    assert execution.resource_state_id == transaction.resource_state_id
    assert execution.resource_version == transaction.resource_version
    assert execution.quantity.value == Decimal("10.250")
    assert execution.scheduled_for == transaction.scheduled_for
    assert execution.provenance["source_transaction_version"] == "2"


def test_execution_requires_scheduled_transaction_and_attributed_actor():
    transaction = make_transaction(status=TransactionStatus.AGREED, scheduled_for=None)
    with pytest.raises(DomainError):
        Execution.from_transaction(
            transaction,
            execution_id="exe_1",
            actor_id="act_buyer",
            at=NOW,
        )
    with pytest.raises(DomainError):
        Execution.from_transaction(
            make_transaction(),
            execution_id="exe_1",
            actor_id="",
            at=NOW,
        )
    with pytest.raises(DomainError):
        Execution.from_transaction(
            make_transaction(),
            execution_id="exe_1",
            actor_id="act_buyer",
            at=NOW.replace(tzinfo=None),
        )


def test_execution_enforces_tenant_and_valid_aggregate_invariants():
    execution = Execution.from_transaction(
        make_transaction(),
        execution_id="exe_1",
        actor_id="act_buyer",
        at=NOW,
    )
    with pytest.raises(TenantBoundaryError):
        execution.validate_tenant("org_other")
    with pytest.raises(DomainError):
        replace(
            execution,
            quantity=Quantity(Decimal("0"), "t", "CRR-UNITS-0.1"),
        )


def test_execution_closure_is_operational_not_verification_and_requires_reconciliation():
    execution = Execution.from_transaction(
        make_transaction(),
        execution_id="exe_1",
        actor_id="act_buyer",
        at=NOW,
    )
    in_progress = replace(execution, status=ExecutionStatus.IN_PROGRESS)
    with pytest.raises(DomainError):
        in_progress.close(
            actor_id="act_buyer",
            at=NOW + timedelta(minutes=1),
            reason="No operation reported",
            has_reported_operations=False,
            has_unresolved_exceptions=False,
        )
    with pytest.raises(DomainError):
        in_progress.close(
            actor_id="act_buyer",
            at=NOW + timedelta(minutes=1),
            reason="Unresolved exception",
            has_reported_operations=True,
            has_unresolved_exceptions=True,
        )
    closed = in_progress.close(
        actor_id="act_buyer",
        at=NOW + timedelta(minutes=1),
        reason="Operational record reconciled",
        has_reported_operations=True,
        has_unresolved_exceptions=False,
    )
    assert closed.status is ExecutionStatus.CLOSED
    assert closed.version == execution.version + 1
    assert closed.provenance["verification_status"] == "NOT_VERIFIED"
    assert closed.provenance["operational_closure_reason"] == "Operational record reconciled"


def test_execution_cancellation_is_pre_execution_only_and_attributed():
    execution = Execution.from_transaction(
        make_transaction(),
        execution_id="exe_1",
        actor_id="act_buyer",
        at=NOW,
    )
    cancelled = execution.cancel(
        actor_id="act_buyer",
        at=NOW + timedelta(minutes=1),
        reason="Withdrawn before physical work",
        has_reported_operations=False,
        has_unresolved_exceptions=False,
    )
    assert cancelled.status is ExecutionStatus.CANCELLED
    assert cancelled.provenance["cancelled_by"] == "act_buyer"
    with pytest.raises(DomainError):
        execution.cancel(
            actor_id="act_buyer",
            at=NOW + timedelta(minutes=1),
            reason="Work already reported",
            has_reported_operations=True,
            has_unresolved_exceptions=False,
        )
