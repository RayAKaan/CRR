"""Tenant-isolated EconomicModel API."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from crr.domain.economics import (
    EconomicComponent,
    EconomicComponentKind,
    EconomicModelStatus,
    EconomicPerspective,
    Money,
    RoundingPolicy,
)
from crr.domain.economics import EconomicModel as DomainEconomicModel
from crr.domain.errors import DomainError
from crr.economic_model import EconomicModel
from crr.economic_schemas import EconomicModelInput
from crr.models import IdempotencyRecord, OutboxEvent

router = APIRouter()


def _api():
    from crr import api

    return api


def _fail(request: Request, status: int, code: str, category: str, message: str):
    _api()._fail(request, status, code, category, message)


def _envelope(request: Request, data: Any):
    return _api()._envelope(request, data)


def _collection(
    request: Request,
    data: list[dict[str, Any]],
    cursor: str | None,
    has_more: bool,
    limit: int,
):
    return _api()._collection(request, data, cursor, has_more, limit)


def _body_hash(payload: dict[str, Any]) -> str:
    return _api()._body_hash(payload)


def _session_dependency():
    return _api().db_session


def _scope_dependency(scope: str):
    return _api().scope_required(scope)


def _domain(item: EconomicModel) -> DomainEconomicModel:
    components = tuple(
        EconomicComponent(
            perspective=EconomicPerspective(component["perspective"]),
            kind=EconomicComponentKind(component["kind"]),
            label=component["label"],
            amount=Money(Decimal(component["amount"]), component["currency"]),
            source=component["source"],
        )
        for component in item.components
    )
    return DomainEconomicModel(
        id=item.id,
        model_key=item.model_key,
        organization_id=item.organization_id,
        version=item.version,
        currency=item.currency,
        valid_from=item.valid_from,
        valid_until=item.valid_until,
        calculation_version=item.calculation_version,
        rounding=RoundingPolicy(item.rounding_mode, item.rounding_scale),
        components=components,
        status=EconomicModelStatus(item.status),
        created_by=item.created_by,
        provenance=item.provenance,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _data(item: EconomicModel) -> dict[str, Any]:
    return {
        "id": item.id,
        "model_key": item.model_key,
        "organization_id": item.organization_id,
        "version": item.version,
        "currency": item.currency,
        "valid_from": item.valid_from.isoformat(),
        "valid_until": item.valid_until.isoformat() if item.valid_until is not None else None,
        "calculation_version": item.calculation_version,
        "rounding": {"mode": item.rounding_mode, "scale": item.rounding_scale},
        "components": item.components,
        "status": item.status,
        "created_by": item.created_by,
        "provenance": item.provenance,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _find(session: Session, model_id: str, organization_id: str):
    return session.scalar(
        select(EconomicModel).where(
            EconomicModel.id == model_id,
            EconomicModel.organization_id == organization_id,
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
    return session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.organization_id == organization_id,
            IdempotencyRecord.idempotency_key == key,
        )
    )


def _check_reuse(prior, digest: str, request: Request):
    if prior and (prior.request_hash != digest or prior.object_type != "EconomicModel"):
        _fail(
            request,
            409,
            "IDEMPOTENCY_CONFLICT",
            "DOMAIN_CONFLICT",
            "Idempotency key was reused with a different request.",
        )


def _remember(
    session: Session,
    organization_id: str,
    key: str,
    digest: str,
    model_id: str,
):
    session.add(
        IdempotencyRecord(
            organization_id=organization_id,
            idempotency_key=key,
            request_hash=digest,
            object_type="EconomicModel",
            object_id=model_id,
            created_at=datetime.now(UTC),
        )
    )


def _event(
    session: Session,
    request: Request,
    organization_id: str,
    actor_id: str,
    item: EconomicModel,
    key: str,
):
    session.add(
        OutboxEvent(
            id=f"evt_{uuid4().hex}",
            event_type="economic_model.created",
            event_version=1,
            aggregate_type="EconomicModel",
            aggregate_id=item.id,
            aggregate_version=item.version,
            organization_id=organization_id,
            actor_id=actor_id,
            occurred_at=datetime.now(UTC),
            published_at=None,
            correlation_id=request.state.request_id,
            causation_id=None,
            idempotency_key=key,
            payload={
                "economic_model_id": item.id,
                "version": item.version,
                "status": item.status,
            },
            provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
            schema_version="0.1",
        )
    )


def _replay(
    session: Session,
    response: Response,
    request: Request,
    prior,
    organization_id: str,
):
    item = _find(session, prior.object_id, organization_id)
    if item is None:
        _fail(
            request,
            409,
            "IDEMPOTENCY_STATE_MISSING",
            "DOMAIN_CONFLICT",
            "Idempotent EconomicModel result is unavailable.",
        )
    response.status_code = 200
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


def _database_error(request: Request):
    _fail(
        request,
        503,
        "DATABASE_UNAVAILABLE",
        "DATABASE_FAILURE",
        "Database operation failed.",
    )


@router.get("/v1/economic-models")
def list_economic_models(
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("economic_models:read"))],
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
    status: str | None = None,
    model_key: str | None = None,
):
    statement = select(EconomicModel).where(
        EconomicModel.organization_id == principal.organization_id
    )
    if cursor:
        statement = statement.where(EconomicModel.id > cursor)
    if status is not None:
        if status not in {item.value for item in EconomicModelStatus}:
            _fail(
                request,
                422,
                "INVALID_STATUS",
                "VALIDATION_FAILURE",
                "Unknown EconomicModel status.",
            )
        statement = statement.where(EconomicModel.status == status)
    if model_key is not None:
        statement = statement.where(EconomicModel.model_key == model_key)
    rows = session.scalars(statement.order_by(EconomicModel.id).limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].id if has_more and rows else None
    return _collection(request, [_data(row) for row in rows], next_cursor, has_more, limit)


@router.post("/v1/economic-models", status_code=201)
def create_economic_model(
    body: EconomicModelInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("economic_models:write"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    payload = body.model_dump(mode="json")
    digest = _body_hash(payload)
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    _check_reuse(prior, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)

    now = datetime.now(UTC)
    try:
        components = tuple(
            EconomicComponent(
                perspective=item.perspective,
                kind=item.kind,
                label=item.label,
                amount=Money(item.amount, body.currency),
                source=item.source,
            )
            for item in body.components
        )
        domain_item = DomainEconomicModel(
            id=body.id or f"eco_{uuid4().hex}",
            model_key=body.model_key,
            organization_id=principal.organization_id,
            version=body.version,
            currency=body.currency,
            valid_from=body.valid_from,
            valid_until=body.valid_until,
            calculation_version=body.calculation_version,
            rounding=RoundingPolicy(body.rounding.mode, body.rounding.scale),
            components=components,
            status=EconomicModelStatus(body.status),
            created_by=principal.actor_id,
            provenance=body.provenance,
            created_at=now,
            updated_at=now,
        )
    except DomainError as exc:
        _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))

    item = EconomicModel(
        id=domain_item.id,
        model_key=domain_item.model_key,
        organization_id=domain_item.organization_id,
        version=domain_item.version,
        currency=domain_item.currency,
        valid_from=domain_item.valid_from,
        valid_until=domain_item.valid_until,
        calculation_version=domain_item.calculation_version,
        rounding_mode=domain_item.rounding.mode,
        rounding_scale=domain_item.rounding.scale,
        components=[
            {
                "perspective": component.perspective.value,
                "kind": component.kind.value,
                "label": component.label,
                "amount": str(component.amount.amount),
                "currency": component.amount.currency,
                "source": component.source,
            }
            for component in domain_item.components
        ],
        status=domain_item.status.value,
        created_by=domain_item.created_by,
        provenance=domain_item.provenance,
        created_at=domain_item.created_at,
        updated_at=domain_item.updated_at,
    )
    session.add(item)
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _event(
        session,
        request,
        principal.organization_id,
        principal.actor_id,
        item,
        idempotency_key,
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
        _check_reuse(prior, digest, request)
        if prior:
            return _replay(session, response, request, prior, principal.organization_id)
        _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "EconomicModel creation conflicted.")
    except SQLAlchemyError:
        session.rollback()
        _database_error(request)
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


@router.get("/v1/economic-models/{model_id}")
def get_economic_model(
    model_id: str,
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("economic_models:read"))],
):
    item = _find(session, model_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "EconomicModel not found.")
    return _envelope(request, _data(item))
