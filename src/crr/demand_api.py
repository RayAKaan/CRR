"""Demand v1 API adapter for the Phase 2 canonical Demand model."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from crr.demand_model import Demand
from crr.demand_schemas import DemandInput, DemandPatch
from crr.domain.demand import Demand as DomainDemand
from crr.domain.demand import DemandStatus
from crr.domain.errors import DomainError
from crr.domain.quantity import Quantity
from crr.models import IdempotencyRecord, OutboxEvent

router = APIRouter()


def _api():
    from crr import api

    return api


def _fail(request: Request, status: int, code: str, category: str, message: str):
    _api()._fail(request, status, code, category, message)


def _envelope(request: Request, data: dict[str, Any]):
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


def _principal_type():
    return _api().Principal


def _quantity(value: Decimal, unit: str, registry_version: str) -> Quantity:
    return Quantity(value, unit, registry_version)


def _domain_from_model(item: Demand) -> DomainDemand:
    return DomainDemand(
        id=item.id,
        organization_id=item.organization_id,
        required_state=item.required_state,
        quantity_min=_quantity(
            item.quantity_min_value, item.unit, item.unit_registry_version
        ),
        quantity_target=_quantity(
            item.quantity_target_value, item.unit, item.unit_registry_version
        ),
        quantity_max=_quantity(
            item.quantity_max_value, item.unit, item.unit_registry_version
        ),
        remaining_quantity=_quantity(
            item.remaining_quantity_value, item.unit, item.unit_registry_version
        ),
        status=DemandStatus(item.status),
        location_constraints=item.location_constraints,
        timing_start=item.timing_start,
        timing_end=item.timing_end,
        quality_requirements=item.quality_requirements,
        pricing_constraints=item.pricing_constraints,
        certifications=tuple(item.certifications),
        regulatory_constraints=item.regulatory_constraints,
        substitutions=tuple(item.substitutions),
        recurrence=item.recurrence,
        version=item.version,
        created_by=item.created_by,
        provenance=item.provenance,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _data(item: Demand) -> dict[str, Any]:
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "required_state": item.required_state,
        "quantity_min": {"value": str(item.quantity_min_value), "unit": item.unit},
        "quantity_target": {"value": str(item.quantity_target_value), "unit": item.unit},
        "quantity_max": {"value": str(item.quantity_max_value), "unit": item.unit},
        "remaining_quantity": {
            "value": str(item.remaining_quantity_value),
            "unit": item.unit,
        },
        "unit_registry_version": item.unit_registry_version,
        "status": item.status,
        "location_constraints": item.location_constraints,
        "timing_start": item.timing_start.isoformat(),
        "timing_end": item.timing_end.isoformat(),
        "quality_requirements": item.quality_requirements,
        "pricing_constraints": item.pricing_constraints,
        "certifications": item.certifications,
        "regulatory_constraints": item.regulatory_constraints,
        "substitutions": item.substitutions,
        "recurrence": item.recurrence,
        "version": item.version,
        "created_by": item.created_by,
        "provenance": item.provenance,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _check_idempotency(
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
    if prior and (prior.request_hash != digest or prior.object_type != "Demand"):
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
    object_id: str,
):
    session.add(
        IdempotencyRecord(
            organization_id=organization_id,
            idempotency_key=key,
            request_hash=digest,
            object_type="Demand",
            object_id=object_id,
            created_at=datetime.now(UTC),
        )
    )


def _emit(
    session: Session,
    request: Request,
    organization_id: str,
    actor_id: str,
    event_type: str,
    aggregate_id: str,
    aggregate_version: int,
    payload: dict[str, Any],
    idempotency_key: str,
):
    session.add(
        OutboxEvent(
            id=f"evt_{uuid4().hex}",
            event_type=event_type,
            event_version=1,
            aggregate_type="Demand",
            aggregate_id=aggregate_id,
            aggregate_version=aggregate_version,
            organization_id=organization_id,
            actor_id=actor_id,
            occurred_at=datetime.now(UTC),
            published_at=None,
            correlation_id=request.state.request_id,
            causation_id=None,
            idempotency_key=idempotency_key,
            payload=payload,
            provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
            schema_version="0.1",
        )
    )


def _parse_if_match(request: Request, value: str | None) -> int:
    if value is None:
        _fail(request, 400, "PRECONDITION_REQUIRED", "CONCURRENCY", "If-Match is required.")
    token = value.strip('"')
    if token.startswith("version-"):
        token = token.removeprefix("version-")
    try:
        version = int(token)
    except ValueError:
        _fail(
            request,
            400,
            "INVALID_PRECONDITION",
            "CONCURRENCY",
            "If-Match must contain a positive version.",
        )
    if version < 1:
        _fail(
            request,
            400,
            "INVALID_PRECONDITION",
            "CONCURRENCY",
            "If-Match must contain a positive version.",
        )
    return version


def _validate_registry(request: Request, app, quantities: list[Quantity]):
    try:
        for quantity in quantities:
            app.state.unit_registry.validate(quantity)
    except DomainError as exc:
        _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))


def _validate_patch_against_current(
    request: Request,
    body: DemandPatch,
    current: DomainDemand,
    app,
):
    values = {
        "required_state": body.required_state if body.required_state is not None else current.required_state,
        "quantity_min": body.quantity_min
        if body.quantity_min is not None
        else current.quantity_min.value,
        "quantity_target": body.quantity_target
        if body.quantity_target is not None
        else current.quantity_target.value,
        "quantity_max": body.quantity_max
        if body.quantity_max is not None
        else current.quantity_max.value,
        "unit": body.unit if body.unit is not None else current.quantity_min.unit,
        "unit_registry_version": body.unit_registry_version
        if body.unit_registry_version is not None
        else current.quantity_min.unit_registry_version,
        "timing_start": body.timing_start if body.timing_start is not None else current.timing_start,
        "timing_end": body.timing_end if body.timing_end is not None else current.timing_end,
    }
    if values["unit"] != current.quantity_min.unit or values["unit_registry_version"] != current.quantity_min.unit_registry_version:
        _fail(
            request,
            422,
            "UNIT_CHANGE_REQUIRES_REQUANTIFICATION",
            "VALIDATION_FAILURE",
            "Demand quantity units are immutable; create a new quantified demand instead.",
        )
    quantities = [
        _quantity(values["quantity_min"], values["unit"], values["unit_registry_version"]),
        _quantity(values["quantity_target"], values["unit"], values["unit_registry_version"]),
        _quantity(values["quantity_max"], values["unit"], values["unit_registry_version"]),
    ]
    _validate_registry(request, app, quantities)
    if not quantities[0].value <= quantities[1].value <= quantities[2].value:
        _fail(
            request,
            422,
            "INVALID_QUANTITY_BOUNDS",
            "VALIDATION_FAILURE",
            "Demand quantities must satisfy min <= target <= max.",
        )
    if values["timing_start"] >= values["timing_end"]:
        _fail(
            request,
            422,
            "INVALID_TIMING_WINDOW",
            "VALIDATION_FAILURE",
            "Demand timing_start must be before timing_end.",
        )
    if not quantities[0].value <= current.remaining_quantity.value <= quantities[2].value:
        _fail(
            request,
            422,
            "INVALID_REMAINING_QUANTITY",
            "VALIDATION_FAILURE",
            "Remaining demand must remain within the declared bounds.",
        )
    return values


@router.get("/v1/demands")
def list_demands(
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("demands:read"))],
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
    status: str | None = None,
    required_state: str | None = None,
):
    statement = select(Demand).where(Demand.organization_id == principal.organization_id)
    if cursor:
        statement = statement.where(Demand.id > cursor)
    if status is not None:
        if status not in {item.value for item in DemandStatus}:
            _fail(request, 422, "INVALID_STATUS", "VALIDATION_FAILURE", "Unknown Demand status.")
        statement = statement.where(Demand.status == status)
    if required_state is not None:
        statement = statement.where(Demand.required_state == required_state)
    rows = session.scalars(statement.order_by(Demand.id).limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].id if has_more and rows else None
    return _collection(request, [_data(row) for row in rows], next_cursor, has_more, limit)


@router.post("/v1/demands", status_code=201)
def create_demand(
    body: DemandInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("demands:write"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    payload = body.model_dump(mode="json")
    digest = _body_hash(payload)
    prior = _check_idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        item = session.scalar(
            select(Demand).where(
                Demand.id == prior.object_id,
                Demand.organization_id == principal.organization_id,
            )
        )
        if item is None:
            _fail(request, 409, "IDEMPOTENCY_STATE_MISSING", "DOMAIN_CONFLICT", "Idempotent Demand result is unavailable.")
        response.status_code = 200
        response.headers["ETag"] = f'"version-{item.version}"'
        return _envelope(request, _data(item))
    now = datetime.now(UTC)
    unit_min = _quantity(body.quantity_min, body.unit, body.unit_registry_version)
    unit_target = _quantity(body.quantity_target, body.unit, body.unit_registry_version)
    unit_max = _quantity(body.quantity_max, body.unit, body.unit_registry_version)
    _validate_registry(request, request.app, [unit_min, unit_target, unit_max])
    remaining = unit_target
    item = Demand(
        id=body.id or f"dem_{uuid4().hex}",
        organization_id=principal.organization_id,
        required_state=body.required_state,
        quantity_min_value=unit_min.value,
        quantity_target_value=unit_target.value,
        quantity_max_value=unit_max.value,
        remaining_quantity_value=remaining.value,
        unit=body.unit,
        unit_registry_version=body.unit_registry_version,
        status=body.status,
        location_constraints=body.location_constraints,
        timing_start=body.timing_start.astimezone(UTC),
        timing_end=body.timing_end.astimezone(UTC),
        quality_requirements=body.quality_requirements,
        pricing_constraints=body.pricing_constraints,
        certifications=body.certifications,
        regulatory_constraints=body.regulatory_constraints,
        substitutions=body.substitutions,
        recurrence=body.recurrence,
        version=1,
        created_by=principal.actor_id,
        provenance=body.provenance,
        created_at=now,
        updated_at=now,
    )
    domain = _domain_from_model(item)
    session.add(item)
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _emit(
        session,
        request,
        principal.organization_id,
        principal.actor_id,
        "demand.created",
        item.id,
        domain.version,
        {"demand_id": item.id, "status": item.status},
        idempotency_key,
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        prior = session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.organization_id == principal.organization_id,
                IdempotencyRecord.idempotency_key == idempotency_key,
            )
        )
        if prior and prior.object_type == "Demand" and prior.request_hash == digest:
            item = session.scalar(
                select(Demand).where(
                    Demand.id == prior.object_id,
                    Demand.organization_id == principal.organization_id,
                )
            )
            if item is not None:
                response.status_code = 200
                response.headers["ETag"] = f'"version-{item.version}"'
                return _envelope(request, _data(item))
        _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "Demand creation conflicted.")
    except SQLAlchemyError:
        session.rollback()
        _fail(request, 503, "DATABASE_UNAVAILABLE", "DATABASE_FAILURE", "Database operation failed.")
    response.headers["ETag"] = '"version-1"'
    return _envelope(request, _data(item))


@router.get("/v1/demands/{demand_id}")
def get_demand(
    demand_id: str,
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("demands:read"))],
):
    item = session.scalar(
        select(Demand).where(
            Demand.id == demand_id,
            Demand.organization_id == principal.organization_id,
        )
    )
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Demand not found.")
    response = _envelope(request, _data(item))
    return response


@router.patch("/v1/demands/{demand_id}")
def patch_demand(
    demand_id: str,
    body: DemandPatch,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("demands:write"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    expected = _parse_if_match(request, if_match)
    payload = body.model_dump(mode="json", exclude_unset=True)
    digest = _body_hash(payload | {"expected_version": expected, "demand_id": demand_id})
    prior = _check_idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        item = session.scalar(
            select(Demand).where(
                Demand.id == prior.object_id,
                Demand.organization_id == principal.organization_id,
            )
        )
        if item is None:
            _fail(request, 409, "IDEMPOTENCY_STATE_MISSING", "DOMAIN_CONFLICT", "Idempotent Demand result is unavailable.")
        response.status_code = 200
        response.headers["ETag"] = f'"version-{item.version}"'
        return _envelope(request, _data(item))
    item = session.scalar(
        select(Demand).where(
            Demand.id == demand_id,
            Demand.organization_id == principal.organization_id,
        )
    )
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Demand not found.")
    if item.version != expected:
        _fail(request, 412, "STALE_VERSION", "CONCURRENCY", "Demand version is stale.")
    current = _domain_from_model(item)
    values = _validate_patch_against_current(request, body, current, request.app)
    target_status = DemandStatus(body.status) if body.status is not None else current.status
    if target_status != current.status:
        try:
            transitioned = current.transition(target_status)
        except DomainError as exc:
            _fail(request, 409, "INVALID_LIFECYCLE_TRANSITION", "DOMAIN_CONFLICT", str(exc))
        next_version = transitioned.version
        updated_at = transitioned.updated_at
    else:
        next_version = current.version + 1
        updated_at = datetime.now(UTC)
    values_to_update: dict[str, Any] = {
        "required_state": values["required_state"],
        "quantity_min_value": values["quantity_min"],
        "quantity_target_value": values["quantity_target"],
        "quantity_max_value": values["quantity_max"],
        "status": target_status.value,
        "timing_start": values["timing_start"].astimezone(UTC),
        "timing_end": values["timing_end"].astimezone(UTC),
        "version": next_version,
        "updated_at": updated_at,
    }
    mutable_json_fields = (
        "location_constraints",
        "quality_requirements",
        "pricing_constraints",
        "certifications",
        "regulatory_constraints",
        "substitutions",
        "recurrence",
        "provenance",
    )
    for field in mutable_json_fields:
        value = getattr(body, field)
        if value is not None:
            values_to_update[field] = value
    result = session.execute(
        update(Demand)
        .where(
            Demand.id == demand_id,
            Demand.organization_id == principal.organization_id,
            Demand.version == expected,
        )
        .values(**values_to_update)
    )
    if result.rowcount != 1:
        session.rollback()
        _fail(request, 412, "STALE_VERSION", "CONCURRENCY", "Demand version is stale.")
    _remember(session, principal.organization_id, idempotency_key, digest, demand_id)
    _emit(
        session,
        request,
        principal.organization_id,
        principal.actor_id,
        "demand.updated",
        demand_id,
        next_version,
        {"demand_id": demand_id, "status": target_status.value, "version": next_version},
        idempotency_key,
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        prior = session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.organization_id == principal.organization_id,
                IdempotencyRecord.idempotency_key == idempotency_key,
            )
        )
        if prior and prior.object_type == "Demand" and prior.request_hash == digest:
            item = session.scalar(
                select(Demand).where(
                    Demand.id == demand_id,
                    Demand.organization_id == principal.organization_id,
                )
            )
            if item is not None:
                response.status_code = 200
                response.headers["ETag"] = f'"version-{item.version}"'
                return _envelope(request, _data(item))
        _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "Demand mutation conflicted.")
    except SQLAlchemyError:
        session.rollback()
        _fail(request, 503, "DATABASE_UNAVAILABLE", "DATABASE_FAILURE", "Database operation failed.")
    item = session.scalar(
        select(Demand).where(
            Demand.id == demand_id,
            Demand.organization_id == principal.organization_id,
        )
    )
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))
