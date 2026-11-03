from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from crr.domain.errors import DomainError
from crr.domain.execution import Execution
from crr.domain.execution_operations import (
    ExecutionException,
    ExecutionExceptionResolution,
    ExecutionOperation,
    ExecutionOperationType,
    OperationMode,
    validate_correction,
    validate_reported_operation,
)
from crr.domain.quantity import Quantity
from crr.domain.transaction import Transaction, TransactionStatus

NOW = datetime(2026, 11, 3, 12, tzinfo=UTC)


def make_execution() -> Execution:
    terms = (
        '{"quantity":{"value":"10.0","unit":"t",'
        '"unit_registry_version":"CRR-UNITS-0.1"},"price":"1","currency":"SAR",'
        '"valid_from":"2026-11-01T00:00:00+00:00",'
        '"valid_until":"2026-12-01T00:00:00+00:00"}'
    )
    transaction = Transaction(
        id="txn_1",
        organization_id="org_1",
        agreement_id="agr_1",
        offer_id="off_1",
        offer_version=1,
        opportunity_id="opp_1",
        opportunity_version=1,
        route_candidate_id="route_1",
        resource_id="res_1",
        resource_state_id="rst_1",
        resource_version=1,
        proposer_actor_id="seller",
        recipient_actor_id="buyer",
        quantity=Quantity(Decimal("10.0"), "t", "CRR-UNITS-0.1"),
        price=Decimal("1"),
        currency="SAR",
        terms_snapshot=terms,
        reservation_ids=("rsv_1",),
        status=TransactionStatus.SCHEDULED,
        version=2,
        created_by="buyer",
        created_at=NOW,
        updated_at=NOW,
        provenance={"source": "test"},
        scheduled_for=NOW + timedelta(days=1),
    )
    return Execution.from_transaction(
        transaction, execution_id="exe_1", actor_id="buyer", at=NOW
    )


def operation(
    operation_id: str,
    operation_type: ExecutionOperationType,
    mode: OperationMode,
    sequence: int,
    **overrides,
) -> ExecutionOperation:
    values = {
        "id": operation_id,
        "organization_id": "org_1",
        "execution_id": "exe_1",
        "operation_type": operation_type,
        "mode": mode,
        "sequence": sequence,
        "actor_id": "operator",
        "created_at": NOW + timedelta(minutes=sequence),
        "planned_for": NOW + timedelta(hours=sequence) if mode is OperationMode.PLANNED else None,
        "occurred_at": NOW + timedelta(hours=sequence) if mode is OperationMode.REPORTED else None,
        "planned_operation_id": None,
        "provenance": {"source": "test"},
    }
    values.update(overrides)
    return ExecutionOperation(**values)


def test_planned_and_reported_operations_are_distinct_and_linked():
    execution = make_execution()
    plan = operation("op_plan", ExecutionOperationType.PICKUP, OperationMode.PLANNED, 1)
    actual = operation(
        "op_actual",
        ExecutionOperationType.PICKUP,
        OperationMode.REPORTED,
        2,
        planned_operation_id=plan.id,
        quantity=execution.quantity,
    )
    validate_reported_operation(
        execution=execution,
        planned_operation=plan,
        reported_operation=actual,
        authorization_scopes=frozenset({"execution:operate"}),
    )


def test_actual_operation_requires_plan_matching_type_and_authorization():
    execution = make_execution()
    plan = operation("op_plan", ExecutionOperationType.PICKUP, OperationMode.PLANNED, 1)
    actual = operation(
        "op_actual",
        ExecutionOperationType.PICKUP,
        OperationMode.REPORTED,
        2,
        planned_operation_id=plan.id,
    )
    with pytest.raises(DomainError):
        validate_reported_operation(
            execution=execution,
            planned_operation=plan,
            reported_operation=actual,
            authorization_scopes=frozenset(),
        )
    wrong_type = operation(
        "op_shipment",
        ExecutionOperationType.SHIPMENT,
        OperationMode.REPORTED,
        2,
        planned_operation_id=plan.id,
    )
    with pytest.raises(DomainError):
        validate_reported_operation(
            execution=execution,
            planned_operation=plan,
            reported_operation=wrong_type,
            authorization_scopes=frozenset({"execution:operate"}),
        )


def test_operation_dependencies_reject_out_of_order_shipment():
    execution = make_execution()
    plan = operation("shipment_plan", ExecutionOperationType.SHIPMENT, OperationMode.PLANNED, 1)
    actual = operation(
        "shipment_actual",
        ExecutionOperationType.SHIPMENT,
        OperationMode.REPORTED,
        2,
        planned_operation_id=plan.id,
    )
    with pytest.raises(DomainError):
        validate_reported_operation(
            execution=execution,
            planned_operation=plan,
            reported_operation=actual,
            prior_reported_operations=(),
            authorization_scopes=frozenset({"execution:operate"}),
        )


def test_duplicate_sequences_and_incompatible_units_are_rejected():
    execution = make_execution()
    plan = operation("pickup_plan", ExecutionOperationType.PICKUP, OperationMode.PLANNED, 1)
    actual = operation(
        "pickup_actual",
        ExecutionOperationType.PICKUP,
        OperationMode.REPORTED,
        2,
        planned_operation_id=plan.id,
        quantity=Quantity(Decimal("1"), "kg", "CRR-UNITS-0.1"),
    )
    with pytest.raises(DomainError):
        validate_reported_operation(
            execution=execution,
            planned_operation=plan,
            reported_operation=actual,
            authorization_scopes=frozenset({"execution:operate"}),
        )
    with pytest.raises(DomainError):
        validate_reported_operation(
            execution=execution,
            planned_operation=plan,
            reported_operation=actual,
            prior_reported_operations=(actual,),
            authorization_scopes=frozenset({"execution:operate"}),
        )


def test_corrections_are_compensating_records_with_reason_and_scope():
    original = operation(
        "original",
        ExecutionOperationType.PICKUP,
        OperationMode.REPORTED,
        2,
        planned_operation_id="plan",
    )
    correction = operation(
        "correction",
        ExecutionOperationType.PICKUP,
        OperationMode.REPORTED,
        3,
        planned_operation_id="plan",
        supersedes_operation_id="original",
        correction_reason="Corrected quantity from signed scale ticket",
    )
    with pytest.raises(DomainError):
        validate_correction(
            original=original,
            correction=correction,
            authorization_scopes=frozenset(),
        )
    validate_correction(
        original=original,
        correction=correction,
        authorization_scopes=frozenset({"execution:correct"}),
    )


def test_exceptions_and_resolutions_are_separate_append_only_records():
    exception = ExecutionException(
        id="exc_1",
        organization_id="org_1",
        execution_id="exe_1",
        code="VEHICLE_DELAY",
        reason="Vehicle delayed at source facility",
        actor_id="operator",
        occurred_at=NOW,
        provenance={"source": "test"},
    )
    resolution = ExecutionExceptionResolution(
        id="exr_1",
        organization_id="org_1",
        execution_id="exe_1",
        exception_id=exception.id,
        actor_id="supervisor",
        reason="Replacement vehicle assigned",
        resolved_at=NOW + timedelta(minutes=30),
        provenance={"source": "test"},
    )
    assert exception.id == resolution.exception_id
