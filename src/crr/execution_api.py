"""Tenant-isolated Execution API with idempotent, append-only operational history."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from crr.domain.errors import DomainError
from crr.domain.execution import Execution as DomainExecution
from crr.domain.execution import ExecutionStatus
from crr.domain.execution_operations import ExecutionException as DomainException
from crr.domain.execution_operations import (
    ExecutionExceptionResolution as DomainResolution,
    ExecutionOperation as DomainOperation,
    ExecutionOperationType,
    OperationMode,
    validate_correction,
    validate_reported_operation,
)
from crr.domain.quantity import Quantity
from crr.domain.transaction import Transaction as DomainTransaction
from crr.domain.transaction import TransactionStatus
from crr.execution_model import Execution as ExecutionRecord
from crr.execution_operation_model import (
    ExecutionException as ExceptionRecord,
    ExecutionExceptionResolution as ResolutionRecord,
    ExecutionOperation as OperationRecord,
)
from crr.execution_schemas import (
    ExecutionCorrectionInput,
    ExecutionCreate,
    ExecutionExceptionInput,
    ExecutionExceptionResolutionInput,
    ExecutionPlanInput,
    ExecutionReportInput,
)
from crr.models import IdempotencyRecord, OutboxEvent
from crr.transaction_model import Transaction as TransactionRecord

router = APIRouter()


def _api():
    from crr import api

    return api


def _fail(request: Request, status: int, code: str, category: str, message: str):
    _api()._fail(request, status, code, category, message)


def _envelope(request: Request, data: Any):
    return _api()._envelope(request, data)


def _collection(request: Request, data, cursor, has_more, limit):
    return _api()._collection(request, data, cursor, has_more, limit)


def _session_dependency():
    return _api().db_session


def _scope_dependency(scope: str):
    return _api().scope_required(scope)


def _body_hash(payload: dict[str, Any]) -> str:
    return _api()._body_hash(payload)


def _transaction_domain(session: Session, item: TransactionRecord) -> DomainTransaction:
    from crr.transaction_api import _transaction_domain as convert

    return convert(session, item)


def _execution_domain(item: ExecutionRecord) -> DomainExecution:
    return DomainExecution(
        id=item.id,
        organization_id=item.organization_id,
        transaction_id=item.transaction_id,
        agreement_id=item.agreement_id,
        resource_id=item.resource_id,
        resource_state_id=item.resource_state_id,
        resource_version=item.resource_version,
        route_candidate_id=item.route_candidate_id,
        quantity=Quantity(item.quantity_value, item.quantity_unit, item.unit_registry_version),
        scheduled_for=item.scheduled_for,
        status=ExecutionStatus(item.status),
        version=item.version,
        created_by=item.created_by,
        created_at=item.created_at,
        updated_at=item.updated_at,
        provenance=item.provenance,
    )


def _operation_domain(item: OperationRecord) -> DomainOperation:
    quantity = (
        Quantity(item.quantity_value, item.quantity_unit, item.unit_registry_version)
        if item.quantity_value is not None
        else None
    )
    return DomainOperation(
        id=item.id,
        organization_id=item.organization_id,
        execution_id=item.execution_id,
        operation_type=ExecutionOperationType(item.operation_type),
        mode=OperationMode(item.mode),
        sequence=item.sequence,
        actor_id=item.actor_id,
        created_at=item.created_at,
        planned_for=item.planned_for,
        occurred_at=item.occurred_at,
        location_id=item.location_id,
        quantity=quantity,
        planned_operation_id=item.planned_operation_id,
        supersedes_operation_id=item.supersedes_operation_id,
        correction_reason=item.correction_reason,
        provenance=item.provenance,
    )


def _operation_data(item: OperationRecord) -> dict[str, Any]:
    return {
        "id": item.id,
        "execution_id": item.execution_id,
        "operation_type": item.operation_type,
        "mode": item.mode,
        "sequence": item.sequence,
        "planned_for": item.planned_for.isoformat() if item.planned_for else None,
        "occurred_at": item.occurred_at.isoformat() if item.occurred_at else None,
        "planned_operation_id": item.planned_operation_id,
        "supersedes_operation_id": item.supersedes_operation_id,
        "correction_reason": item.correction_reason,
        "location_id": item.location_id,
        "quantity": (
            {
                "value": str(item.quantity_value),
                "unit": item.quantity_unit,
                "unit_registry_version": item.unit_registry_version,
            }
            if item.quantity_value is not None
            else None
        ),
        "actor_id": item.actor_id,
        "created_at": item.created_at.isoformat(),
        "provenance": item.provenance,
    }


def _data(session: Session, item: ExecutionRecord) -> dict[str, Any]:
    operations = session.scalars(
        select(OperationRecord)
        .where(
            OperationRecord.organization_id == item.organization_id,
            OperationRecord.execution_id == item.id,
        )
        .order_by(OperationRecord.sequence)
    ).all()
    exceptions = session.scalars(
        select(ExceptionRecord)
        .where(
            ExceptionRecord.organization_id == item.organization_id,
            ExceptionRecord.execution_id == item.id,
        )
        .order_by(ExceptionRecord.occurred_at, ExceptionRecord.id)
    ).all()
    resolutions = session.scalars(
        select(ResolutionRecord)
        .where(
            ResolutionRecord.organization_id == item.organization_id,
            ResolutionRecord.execution_id == item.id,
        )
        .order_by(ResolutionRecord.resolved_at, ResolutionRecord.id)
    ).all()
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "transaction_id": item.transaction_id,
        "agreement_id": item.agreement_id,
        "resource_id": item.resource_id,
        "resource_state_id": item.resource_state_id,
        "resource_state_version": item.resource_version,
        "route_candidate_id": item.route_candidate_id,
        "quantity": {
            "value": str(item.quantity_value),
            "unit": item.quantity_unit,
            "unit_registry_version": item.unit_registry_version,
        },
        "scheduled_for": item.scheduled_for.isoformat(),
        "status": item.status,
        "version": item.version,
        "created_by": item.created_by,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
        "provenance": item.provenance,
        "operations": [_operation_data(operation) for operation in operations],
        "exceptions": [
            {
                "id": exception.id,
                "code": exception.code,
                "reason": exception.reason,
                "actor_id": exception.actor_id,
                "occurred_at": exception.occurred_at.isoformat(),
                "provenance": exception.provenance,
                "resolution": next(
                    (
                        {
                            "id": resolution.id,
                            "actor_id": resolution.actor_id,
                            "reason": resolution.reason,
                            "resolved_at": resolution.resolved_at.isoformat(),
                        }
                        for resolution in resolutions
                        if resolution.exception_id == exception.id
                    ),
                    None,
                ),
            }
            for exception in exceptions
        ],
    }


def _find(session: Session, execution_id: str, organization_id: str):
    return session.scalar(
        select(ExecutionRecord).where(
            ExecutionRecord.id == execution_id,
            ExecutionRecord.organization_id == organization_id,
        )
    )


def _idempotency(
    session: Session,
    organization_id: str,
    key: str | None,
    digest: str,
    request: Request,
):
    if not key or not key.strip() or len(key) > 255:
        _fail(
            request,
            400,
            "IDEMPOTENCY_KEY_REQUIRED",
            "VALIDATION_FAILURE",
            "A valid Idempotency-Key is required.",
        )
    prior = session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.organization_id == organization_id,
            IdempotencyRecord.idempotency_key == key,
        )
    )
    if prior and (prior.request_hash != digest or prior.object_type != "Execution"):
        _fail(
            request,
            409,
            "IDEMPOTENCY_CONFLICT",
            "DOMAIN_CONFLICT",
            "Idempotency key was reused with a different request.",
        )
    return prior


def _remember(
    session: Session,
    organization_id: str,
    key: str,
    digest: str,
    execution_id: str,
) -> None:
    session.add(
        IdempotencyRecord(
            organization_id=organization_id,
            idempotency_key=key,
            request_hash=digest,
            object_type="Execution",
            object_id=execution_id,
            created_at=datetime.now(UTC),
        )
    )


def _emit(
    session: Session,
    request: Request,
    principal: Any,
    item: ExecutionRecord,
    key: str,
    event_type: str,
    payload: dict[str, Any],
) -> None:
    session.add(
        OutboxEvent(
            id=f"evt_{uuid4().hex}",
            event_type=event_type,
            event_version=1,
            aggregate_type="Execution",
            aggregate_id=item.id,
            aggregate_version=item.version,
            organization_id=principal.organization_id,
            actor_id=principal.actor_id,
            occurred_at=datetime.now(UTC),
            published_at=None,
            correlation_id=request.state.request_id,
            causation_id=item.transaction_id,
            idempotency_key=key,
            payload={
                "execution_id": item.id,
                "transaction_id": item.transaction_id,
                "status": item.status,
                "version": item.version,
                **payload,
            },
            provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
            schema_version="0.1",
        )
    )


def _replay(session: Session, response: Response, request: Request, prior, organization_id: str):
    item = _find(session, prior.object_id, organization_id)
    if item is None:
        _fail(
            request,
            409,
            "IDEMPOTENCY_STATE_MISSING",
            "DOMAIN_CONFLICT",
            "Idempotent Execution result is unavailable.",
        )
    response.status_code = 200
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(session, item))


def _locked_execution(
    session: Session,
    execution_id: str,
    organization_id: str,
    request: Request,
    if_match: str | None,
):
    if not if_match:
        _fail(request, 428, "IF_MATCH_REQUIRED", "CONCURRENCY_FAILURE", "If-Match is required.")
    item = session.scalar(
        select(ExecutionRecord)
        .where(
            ExecutionRecord.id == execution_id,
            ExecutionRecord.organization_id == organization_id,
        )
        .with_for_update()
    )
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Execution not found.")
    if if_match != f'"version-{item.version}"':
        _fail(request, 409, "STALE_VERSION", "CONCURRENCY_FAILURE", "Execution version is stale.")
    return item


def _commit(
    session: Session,
    request: Request,
    response: Response,
    item: ExecutionRecord,
):
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        _fail(request, 409, "EXECUTION_CONFLICT", "DOMAIN_CONFLICT", "Execution write conflicted.")
    except SQLAlchemyError:
        session.rollback()
        _fail(
            request,
            503,
            "DATABASE_UNAVAILABLE",
            "DATABASE_FAILURE",
            "Execution write failed.",
        )
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(session, item))


def _next_sequence(session: Session, item: ExecutionRecord) -> int:
    current = session.scalar(
        select(func.max(OperationRecord.sequence)).where(
            OperationRecord.organization_id == item.organization_id,
            OperationRecord.execution_id == item.id,
        )
    )
    return (current or 0) + 1


def _quantity_fields(body: Any, request: Request):
    if body.quantity_value is None:
        return None, None, None
    if not body.quantity_unit or not body.unit_registry_version:
        _fail(
            request,
            422,
            "OPERATION_QUANTITY_INCOMPLETE",
            "VALIDATION_FAILURE",
            "Quantity value, unit and registry version must be supplied together.",
        )
    return body.quantity_value, body.quantity_unit, body.unit_registry_version


@router.post("/v1/executions", status_code=201)
def create_execution(
    body: ExecutionCreate,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("executions:write"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(body.model_dump(mode="json"))
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    transaction = session.scalar(
        select(TransactionRecord)
        .where(
            TransactionRecord.id == body.transaction_id,
            TransactionRecord.organization_id == principal.organization_id,
        )
        .with_for_update()
    )
    if transaction is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Transaction not found.")
    if transaction.status != TransactionStatus.SCHEDULED.value:
        _fail(
            request,
            409,
            "TRANSACTION_NOT_SCHEDULED",
            "DOMAIN_CONFLICT",
            "Execution requires a SCHEDULED Transaction.",
        )
    if principal.actor_id not in {transaction.proposer_actor_id, transaction.recipient_actor_id}:
        _fail(
            request,
            403,
            "TRANSACTION_PARTICIPANT_REQUIRED",
            "AUTHORIZATION_FAILURE",
            "Only a Transaction participant may create its Execution.",
        )
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    now = datetime.now(UTC)
    domain_transaction = _transaction_domain(session, transaction)
    try:
        domain = DomainExecution.from_transaction(
            domain_transaction,
            execution_id=f"exe_{uuid4().hex}",
            actor_id=principal.actor_id,
            at=now,
        )
    except DomainError as exc:
        _fail(request, 409, exc.code, "DOMAIN_CONFLICT", str(exc))
    item = ExecutionRecord(
        id=domain.id,
        organization_id=domain.organization_id,
        transaction_id=domain.transaction_id,
        agreement_id=domain.agreement_id,
        resource_id=domain.resource_id,
        resource_state_id=domain.resource_state_id,
        resource_version=domain.resource_version,
        route_candidate_id=domain.route_candidate_id,
        quantity_value=domain.quantity.value,
        quantity_unit=domain.quantity.unit,
        unit_registry_version=domain.quantity.unit_registry_version,
        scheduled_for=domain.scheduled_for,
        status=domain.status.value,
        version=domain.version,
        created_by=domain.created_by,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
        provenance=domain.provenance,
    )
    session.add(item)
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _emit(session, request, principal, item, idempotency_key, "execution.created", {})
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        _fail(
            request,
            409,
            "EXECUTION_ALREADY_EXISTS",
            "DOMAIN_CONFLICT",
            "This Transaction already has an Execution or the request conflicted.",
        )
    except SQLAlchemyError:
        session.rollback()
        _fail(
            request,
            503,
            "DATABASE_UNAVAILABLE",
            "DATABASE_FAILURE",
            "Execution creation failed.",
        )
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(session, item))


@router.get("/v1/executions")
def list_executions(
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("executions:read"))],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query(max_length=80)] = None,
):
    statement = select(ExecutionRecord).where(
        ExecutionRecord.organization_id == principal.organization_id
    )
    if cursor:
        statement = statement.where(ExecutionRecord.id > cursor)
    rows = session.scalars(statement.order_by(ExecutionRecord.id).limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].id if has_more and rows else None
    return _collection(
        request,
        [_data(session, item) for item in rows],
        next_cursor,
        has_more,
        limit,
    )


@router.get("/v1/executions/{execution_id}")
def get_execution(
    execution_id: str,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("executions:read"))],
):
    item = _find(session, execution_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Execution not found.")
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(session, item))


@router.post("/v1/executions/{execution_id}/operations/planned", status_code=201)
def plan_execution_operation(
    execution_id: str,
    body: ExecutionPlanInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("executions:plan"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(
        body.model_dump(mode="json") | {"execution_id": execution_id, "if_match": if_match}
    )
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    item = _locked_execution(session, execution_id, principal.organization_id, request, if_match)
    if item.status not in {ExecutionStatus.PLANNED.value, ExecutionStatus.IN_PROGRESS.value}:
        _fail(
            request,
            409,
            "EXECUTION_NOT_PLANNABLE",
            "DOMAIN_CONFLICT",
            "Execution cannot accept plans.",
        )
    now = datetime.now(UTC)
    quantity_value, quantity_unit, registry = _quantity_fields(body, request)
    domain = DomainOperation(
        id=f"op_{uuid4().hex}",
        organization_id=item.organization_id,
        execution_id=item.id,
        operation_type=body.operation_type,
        mode=OperationMode.PLANNED,
        sequence=_next_sequence(session, item),
        actor_id=principal.actor_id,
        created_at=now,
        planned_for=body.planned_for,
        location_id=body.location_id,
        quantity=(
            Quantity(quantity_value, quantity_unit, registry)
            if quantity_value is not None
            else None
        ),
        provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
    )
    domain.validate_against_execution(_execution_domain(item))
    operation = OperationRecord(
        id=domain.id,
        organization_id=domain.organization_id,
        execution_id=domain.execution_id,
        operation_type=domain.operation_type.value,
        mode=domain.mode.value,
        sequence=domain.sequence,
        actor_id=domain.actor_id,
        created_at=domain.created_at,
        planned_for=domain.planned_for,
        occurred_at=None,
        location_id=domain.location_id,
        quantity_value=quantity_value,
        quantity_unit=quantity_unit,
        unit_registry_version=registry,
        planned_operation_id=None,
        supersedes_operation_id=None,
        correction_reason=None,
        provenance=domain.provenance,
    )
    session.add(operation)
    item.version += 1
    item.updated_at = now
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _emit(
        session,
        request,
        principal,
        item,
        idempotency_key,
        "execution.operation.planned",
        {"operation_id": operation.id, "operation_type": operation.operation_type},
    )
    return _commit(session, request, response, item)


@router.post("/v1/executions/{execution_id}/operations/reported", status_code=201)
def report_execution_operation(
    execution_id: str,
    body: ExecutionReportInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("execution:operate"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(
        body.model_dump(mode="json") | {"execution_id": execution_id, "if_match": if_match}
    )
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    item = _locked_execution(session, execution_id, principal.organization_id, request, if_match)
    if item.status not in {ExecutionStatus.PLANNED.value, ExecutionStatus.IN_PROGRESS.value}:
        _fail(
            request,
            409,
            "EXECUTION_NOT_REPORTABLE",
            "DOMAIN_CONFLICT",
            "Execution cannot accept reports.",
        )
    planned = session.scalar(
        select(OperationRecord).where(
            OperationRecord.id == body.planned_operation_id,
            OperationRecord.organization_id == principal.organization_id,
            OperationRecord.execution_id == item.id,
            OperationRecord.mode == OperationMode.PLANNED.value,
        )
    )
    if planned is None:
        _fail(
            request,
            404,
            "PLANNED_OPERATION_NOT_FOUND",
            "NOT_FOUND",
            "Planned operation not found.",
        )
    quantity_value, quantity_unit, registry = _quantity_fields(body, request)
    now = datetime.now(UTC)
    reported = DomainOperation(
        id=f"op_{uuid4().hex}",
        organization_id=item.organization_id,
        execution_id=item.id,
        operation_type=ExecutionOperationType(planned.operation_type),
        mode=OperationMode.REPORTED,
        sequence=_next_sequence(session, item),
        actor_id=principal.actor_id,
        created_at=now,
        occurred_at=body.occurred_at,
        location_id=body.location_id,
        quantity=(
            Quantity(quantity_value, quantity_unit, registry)
            if quantity_value is not None
            else None
        ),
        planned_operation_id=planned.id,
        provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
    )
    prior_rows = session.scalars(
        select(OperationRecord).where(
            OperationRecord.organization_id == principal.organization_id,
            OperationRecord.execution_id == item.id,
            OperationRecord.mode == OperationMode.REPORTED.value,
        )
    ).all()
    try:
        validate_reported_operation(
            execution=_execution_domain(item),
            planned_operation=_operation_domain(planned),
            reported_operation=reported,
            prior_reported_operations=tuple(_operation_domain(row) for row in prior_rows),
            authorization_scopes=principal.scopes,
        )
    except DomainError as exc:
        _fail(request, 409, exc.code, "DOMAIN_CONFLICT", str(exc))
    operation = OperationRecord(
        id=reported.id,
        organization_id=reported.organization_id,
        execution_id=reported.execution_id,
        operation_type=reported.operation_type.value,
        mode=reported.mode.value,
        sequence=reported.sequence,
        actor_id=reported.actor_id,
        created_at=reported.created_at,
        planned_for=None,
        occurred_at=reported.occurred_at,
        location_id=reported.location_id,
        quantity_value=quantity_value,
        quantity_unit=quantity_unit,
        unit_registry_version=registry,
        planned_operation_id=reported.planned_operation_id,
        supersedes_operation_id=None,
        correction_reason=None,
        provenance=reported.provenance or {},
    )
    session.add(operation)
    item.status = ExecutionStatus.IN_PROGRESS.value
    item.version += 1
    item.updated_at = now
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _emit(
        session,
        request,
        principal,
        item,
        idempotency_key,
        "execution.operation.reported",
        {"operation_id": operation.id, "operation_type": operation.operation_type},
    )
    return _commit(session, request, response, item)


@router.post("/v1/executions/{execution_id}/exceptions", status_code=201)
def create_execution_exception(
    execution_id: str,
    body: ExecutionExceptionInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("executions:exceptions:write"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(
        body.model_dump(mode="json") | {"execution_id": execution_id, "if_match": if_match}
    )
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    item = _locked_execution(session, execution_id, principal.organization_id, request, if_match)
    if item.status in {ExecutionStatus.CLOSED.value, ExecutionStatus.CANCELLED.value}:
        _fail(
            request,
            409,
            "EXECUTION_TERMINAL",
            "DOMAIN_CONFLICT",
            "Terminal Execution cannot accept exceptions.",
        )
    now = datetime.now(UTC)
    exception = DomainException(
        id=f"exc_{uuid4().hex}",
        organization_id=item.organization_id,
        execution_id=item.id,
        code=body.code,
        reason=body.reason,
        actor_id=principal.actor_id,
        occurred_at=now,
        provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
    )
    session.add(
        ExceptionRecord(
            id=exception.id,
            organization_id=exception.organization_id,
            execution_id=exception.execution_id,
            code=exception.code,
            reason=exception.reason,
            actor_id=exception.actor_id,
            occurred_at=exception.occurred_at,
            provenance=exception.provenance,
        )
    )
    item.status = ExecutionStatus.EXCEPTION.value
    item.version += 1
    item.updated_at = now
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _emit(
        session,
        request,
        principal,
        item,
        idempotency_key,
        "execution.exception.raised",
        {"exception_id": exception.id, "code": exception.code},
    )
    return _commit(session, request, response, item)


@router.post("/v1/executions/{execution_id}/exceptions/{exception_id}/resolution", status_code=201)
def resolve_execution_exception(
    execution_id: str,
    exception_id: str,
    body: ExecutionExceptionResolutionInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("executions:exceptions:resolve"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(
        body.model_dump(mode="json")
        | {"execution_id": execution_id, "exception_id": exception_id, "if_match": if_match}
    )
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    item = _locked_execution(session, execution_id, principal.organization_id, request, if_match)
    exception = session.scalar(
        select(ExceptionRecord).where(
            ExceptionRecord.id == exception_id,
            ExceptionRecord.organization_id == principal.organization_id,
            ExceptionRecord.execution_id == item.id,
        )
    )
    if exception is None:
        _fail(request, 404, "EXCEPTION_NOT_FOUND", "NOT_FOUND", "Execution exception not found.")
    existing = session.scalar(
        select(ResolutionRecord.id).where(
            ResolutionRecord.organization_id == principal.organization_id,
            ResolutionRecord.exception_id == exception.id,
        )
    )
    if existing is not None:
        _fail(
            request,
            409,
            "EXCEPTION_ALREADY_RESOLVED",
            "DOMAIN_CONFLICT",
            "Exception already has a resolution.",
        )
    now = datetime.now(UTC)
    resolution = DomainResolution(
        id=f"exr_{uuid4().hex}",
        organization_id=item.organization_id,
        execution_id=item.id,
        exception_id=exception.id,
        actor_id=principal.actor_id,
        reason=body.reason,
        resolved_at=now,
        provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
    )
    session.add(
        ResolutionRecord(
            id=resolution.id,
            organization_id=resolution.organization_id,
            execution_id=resolution.execution_id,
            exception_id=resolution.exception_id,
            actor_id=resolution.actor_id,
            reason=resolution.reason,
            resolved_at=resolution.resolved_at,
            provenance=resolution.provenance,
        )
    )
    unresolved = session.scalar(
        select(func.count(ExceptionRecord.id))
        .outerjoin(
            ResolutionRecord,
            (ResolutionRecord.organization_id == ExceptionRecord.organization_id)
            & (ResolutionRecord.exception_id == ExceptionRecord.id),
        )
        .where(
            ExceptionRecord.organization_id == principal.organization_id,
            ExceptionRecord.execution_id == item.id,
            ResolutionRecord.id.is_(None),
        )
    )
    if unresolved == 0 and item.status == ExecutionStatus.EXCEPTION.value:
        actual_count = session.scalar(
            select(func.count(OperationRecord.id)).where(
                OperationRecord.organization_id == principal.organization_id,
                OperationRecord.execution_id == item.id,
                OperationRecord.mode == OperationMode.REPORTED.value,
            )
        )
        item.status = (
            ExecutionStatus.IN_PROGRESS.value if actual_count else ExecutionStatus.PLANNED.value
        )
    item.version += 1
    item.updated_at = now
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _emit(
        session,
        request,
        principal,
        item,
        idempotency_key,
        "execution.exception.resolved",
        {"exception_id": exception.id, "resolution_id": resolution.id},
    )
    return _commit(session, request, response, item)


@router.post("/v1/executions/{execution_id}/corrections", status_code=201)
def correct_execution_operation(
    execution_id: str,
    body: ExecutionCorrectionInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("execution:correct"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(
        body.model_dump(mode="json") | {"execution_id": execution_id, "if_match": if_match}
    )
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    item = _locked_execution(session, execution_id, principal.organization_id, request, if_match)
    original = session.scalar(
        select(OperationRecord).where(
            OperationRecord.id == body.original_operation_id,
            OperationRecord.organization_id == principal.organization_id,
            OperationRecord.execution_id == item.id,
            OperationRecord.mode == OperationMode.REPORTED.value,
        )
    )
    if original is None:
        _fail(
            request,
            404,
            "REPORTED_OPERATION_NOT_FOUND",
            "NOT_FOUND",
            "Reported operation not found.",
        )
    quantity_value, quantity_unit, registry = _quantity_fields(body, request)
    now = datetime.now(UTC)
    correction = DomainOperation(
        id=f"op_{uuid4().hex}",
        organization_id=item.organization_id,
        execution_id=item.id,
        operation_type=ExecutionOperationType(original.operation_type),
        mode=OperationMode.REPORTED,
        sequence=_next_sequence(session, item),
        actor_id=principal.actor_id,
        created_at=now,
        occurred_at=body.occurred_at,
        location_id=body.location_id,
        quantity=(
            Quantity(quantity_value, quantity_unit, registry)
            if quantity_value is not None
            else None
        ),
        planned_operation_id=original.planned_operation_id,
        supersedes_operation_id=original.id,
        correction_reason=body.reason,
        provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
    )
    try:
        validate_correction(
            original=_operation_domain(original),
            correction=correction,
            authorization_scopes=principal.scopes,
        )
        correction.validate_against_execution(_execution_domain(item))
    except DomainError as exc:
        _fail(request, 409, exc.code, "DOMAIN_CONFLICT", str(exc))
    session.add(
        OperationRecord(
            id=correction.id,
            organization_id=correction.organization_id,
            execution_id=correction.execution_id,
            operation_type=correction.operation_type.value,
            mode=correction.mode.value,
            sequence=correction.sequence,
            actor_id=correction.actor_id,
            created_at=correction.created_at,
            planned_for=None,
            occurred_at=correction.occurred_at,
            location_id=correction.location_id,
            quantity_value=quantity_value,
            quantity_unit=quantity_unit,
            unit_registry_version=registry,
            planned_operation_id=correction.planned_operation_id,
            supersedes_operation_id=correction.supersedes_operation_id,
            correction_reason=correction.correction_reason,
            provenance=correction.provenance or {},
        )
    )
    item.version += 1
    item.updated_at = now
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _emit(
        session,
        request,
        principal,
        item,
        idempotency_key,
        "execution.operation.corrected",
        {"operation_id": correction.id, "supersedes_operation_id": original.id},
    )
    return _commit(session, request, response, item)
