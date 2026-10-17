"""Capability v1 API adapter for the canonical Capability model."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from crr.capability_model import Capability
from crr.capability_schemas import CapabilityInput, CapabilityPatch
from crr.domain.capability import Capability as DomainCapability
from crr.domain.capability import CapabilityStatus
from crr.domain.errors import DomainError
from crr.domain.quantity import Quantity
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


def _quantity(value: Decimal, unit: str, registry_version: str) -> Quantity:
    return Quantity(value, unit, registry_version)


def _domain(item: Capability) -> DomainCapability:
    minimum_batch = (
        _quantity(item.minimum_batch_value, item.unit, item.unit_registry_version)
        if item.minimum_batch_value is not None
        else None
    )
    return DomainCapability(
        id=item.id,
        organization_id=item.organization_id,
        accepted_inputs=tuple(item.accepted_inputs),
        output_specifications=item.output_specifications,
        transformation_ids=tuple(item.transformation_ids),
        capacity=_quantity(item.capacity_value, item.unit, item.unit_registry_version),
        minimum_batch=minimum_batch,
        location_id=item.location_id,
        operating_window_start=item.operating_window_start,
        operating_window_end=item.operating_window_end,
        processing_cost=item.processing_cost,
        certifications=tuple(item.certifications),
        regulatory_constraints=item.regulatory_constraints,
        status=CapabilityStatus(item.status),
        version=item.version,
        created_by=item.created_by,
        provenance=item.provenance,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _data(item: Capability) -> dict[str, Any]:
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "accepted_inputs": item.accepted_inputs,
        "output_specifications": item.output_specifications,
        "transformation_ids": item.transformation_ids,
        "capacity": {"value": str(item.capacity_value), "unit": item.unit},
        "minimum_batch": (
            {"value": str(item.minimum_batch_value), "unit": item.unit}
            if item.minimum_batch_value is not None
            else None
        ),
        "unit_registry_version": item.unit_registry_version,
        "location_id": item.location_id,
        "operating_window_start": item.operating_window_start.isoformat(),
        "operating_window_end": item.operating_window_end.isoformat(),
        "processing_cost": item.processing_cost,
        "certifications": item.certifications,
        "regulatory_constraints": item.regulatory_constraints,
        "status": item.status,
        "version": item.version,
        "created_by": item.created_by,
        "provenance": item.provenance,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _find(session: Session, capability_id: str, organization_id: str):
    return session.scalar(
        select(Capability).where(
            Capability.id == capability_id,
            Capability.organization_id == organization_id,
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
    if prior and (prior.request_hash != digest or prior.object_type != "Capability"):
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
    capability_id: str,
):
    session.add(
        IdempotencyRecord(
            organization_id=organization_id,
            idempotency_key=key,
            request_hash=digest,
            object_type="Capability",
            object_id=capability_id,
            created_at=datetime.now(UTC),
        )
    )


def _event(
    session: Session,
    request: Request,
    organization_id: str,
    actor_id: str,
    event_type: str,
    item: Capability,
    key: str,
):
    session.add(
        OutboxEvent(
            id=f"evt_{uuid4().hex}",
            event_type=event_type,
            event_version=1,
            aggregate_type="Capability",
            aggregate_id=item.id,
            aggregate_version=item.version,
            organization_id=organization_id,
            actor_id=actor_id,
            occurred_at=datetime.now(UTC),
            published_at=None,
            correlation_id=request.state.request_id,
            causation_id=None,
            idempotency_key=key,
            payload={"capability_id": item.id, "status": item.status, "version": item.version},
            provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
            schema_version="0.1",
        )
    )


def _if_match(request: Request, value: str | None) -> int:
    if value is None:
        _fail(request, 400, "PRECONDITION_REQUIRED", "CONCURRENCY", "If-Match is required.")
    token = value.strip('"').removeprefix("version-")
    try:
        version = int(token)
    except ValueError:
        _fail(request, 400, "INVALID_PRECONDITION", "CONCURRENCY", "Invalid If-Match version.")
    if version < 1:
        _fail(request, 400, "INVALID_PRECONDITION", "CONCURRENCY", "Invalid If-Match version.")
    return version


def _validate_units(request: Request, quantity: Quantity, minimum_batch: Quantity | None):
    try:
        request.app.state.unit_registry.validate(quantity)
        if minimum_batch is not None:
            request.app.state.unit_registry.validate(minimum_batch)
    except DomainError as exc:
        _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))


def _location(request: Request, session: Session, location_id: str, organization_id: str):
    location = session.scalar(
        select(_api().Location).where(
            _api().Location.id == location_id,
            _api().Location.organization_id == organization_id,
        )
    )
    if location is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Capability location not found.")
    return location


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
            "Idempotent Capability result is unavailable.",
        )
    response.status_code = 200
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


def _database_error(request: Request):
    _fail(request, 503, "DATABASE_UNAVAILABLE", "DATABASE_FAILURE", "Database operation failed.")


@router.get("/v1/capabilities")
def list_capabilities(
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("capabilities:read"))],
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
    status: str | None = None,
    location_id: str | None = None,
):
    statement = select(Capability).where(Capability.organization_id == principal.organization_id)
    if cursor:
        statement = statement.where(Capability.id > cursor)
    if status is not None:
        if status not in {item.value for item in CapabilityStatus}:
            _fail(
                request,
                422,
                "INVALID_STATUS",
                "VALIDATION_FAILURE",
                "Unknown Capability status.",
            )
        statement = statement.where(Capability.status == status)
    if location_id is not None:
        statement = statement.where(Capability.location_id == location_id)
    rows = session.scalars(statement.order_by(Capability.id).limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].id if has_more and rows else None
    return _collection(request, [_data(row) for row in rows], next_cursor, has_more, limit)


@router.post("/v1/capabilities", status_code=201)
def create_capability(
    body: CapabilityInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("capabilities:write"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    payload = body.model_dump(mode="json")
    digest = _body_hash(payload)
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    _check_reuse(prior, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    location = _location(request, session, body.location_id, principal.organization_id)
    capacity = _quantity(body.capacity, body.unit, body.unit_registry_version)
    minimum_batch = (
        _quantity(body.minimum_batch, body.unit, body.unit_registry_version)
        if body.minimum_batch is not None
        else None
    )
    _validate_units(request, capacity, minimum_batch)
    now = datetime.now(UTC)
    item = Capability(
        id=body.id or f"cap_{uuid4().hex}",
        organization_id=principal.organization_id,
        accepted_inputs=body.accepted_inputs,
        output_specifications=body.output_specifications,
        transformation_ids=body.transformation_ids,
        capacity_value=capacity.value,
        unit=capacity.unit,
        unit_registry_version=capacity.unit_registry_version,
        minimum_batch_value=minimum_batch.value if minimum_batch is not None else None,
        location_id=location.id,
        operating_window_start=body.operating_window_start.astimezone(UTC),
        operating_window_end=body.operating_window_end.astimezone(UTC),
        processing_cost=body.processing_cost,
        certifications=body.certifications,
        regulatory_constraints=body.regulatory_constraints,
        status=body.status,
        version=1,
        created_by=principal.actor_id,
        provenance=body.provenance,
        created_at=now,
        updated_at=now,
    )
    session.add(item)
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _event(
        session,
        request,
        principal.organization_id,
        principal.actor_id,
        "capability.created",
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
        _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "Capability creation conflicted.")
    except SQLAlchemyError:
        session.rollback()
        _database_error(request)
    response.headers["ETag"] = '"version-1"'
    return _envelope(request, _data(item))


@router.get("/v1/capabilities/{capability_id}")
def get_capability(
    capability_id: str,
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("capabilities:read"))],
):
    item = _find(session, capability_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Capability not found.")
    return _envelope(request, _data(item))


@router.patch("/v1/capabilities/{capability_id}")
def patch_capability(
    capability_id: str,
    body: CapabilityPatch,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("capabilities:write"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    expected = _if_match(request, if_match)
    payload = body.model_dump(mode="json", exclude_unset=True)
    digest = _body_hash(payload | {"expected_version": expected, "capability_id": capability_id})
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    _check_reuse(prior, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    item = _find(session, capability_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Capability not found.")
    if item.version != expected:
        _fail(request, 412, "STALE_VERSION", "CONCURRENCY", "Capability version is stale.")
    current = _domain(item)
    unit = body.unit or current.capacity.unit
    registry_version = body.unit_registry_version or current.capacity.unit_registry_version
    if unit != current.capacity.unit or registry_version != current.capacity.unit_registry_version:
        _fail(
            request,
            422,
            "UNIT_CHANGE_REQUIRES_REQUANTIFICATION",
            "VALIDATION_FAILURE",
            "Capability capacity units are immutable; create a new quantified capability instead.",
        )
    capacity_value = body.capacity if body.capacity is not None else current.capacity.value
    capacity = _quantity(capacity_value, unit, registry_version)
    minimum_value = body.minimum_batch
    if minimum_value is None and current.minimum_batch is not None:
        minimum_value = current.minimum_batch.value
    minimum_batch = (
        _quantity(minimum_value, unit, registry_version)
        if minimum_value is not None
        else None
    )
    _validate_units(request, capacity, minimum_batch)
    location_id = body.location_id or current.location_id
    location = _location(request, session, location_id, principal.organization_id)
    start = (body.operating_window_start or current.operating_window_start).astimezone(UTC)
    end = (body.operating_window_end or current.operating_window_end).astimezone(UTC)
    status = CapabilityStatus(body.status) if body.status else current.status
    try:
        if status != current.status:
            next_version = current.transition(status).version
        else:
            next_version = current.version + 1
        DomainCapability(
            id=current.id,
            organization_id=current.organization_id,
            accepted_inputs=tuple(body.accepted_inputs or current.accepted_inputs),
            output_specifications=body.output_specifications or current.output_specifications,
            transformation_ids=tuple(body.transformation_ids or current.transformation_ids),
            capacity=capacity,
            minimum_batch=minimum_batch,
            location_id=location.id,
            operating_window_start=start,
            operating_window_end=end,
            processing_cost=body.processing_cost or current.processing_cost,
            certifications=tuple(body.certifications or current.certifications),
            regulatory_constraints=body.regulatory_constraints or current.regulatory_constraints,
            status=status,
            version=next_version,
            created_by=current.created_by,
            provenance=body.provenance or current.provenance,
            created_at=current.created_at,
            updated_at=datetime.now(UTC),
        )
    except DomainError as exc:
        _fail(request, 409, "INVALID_LIFECYCLE_TRANSITION", "DOMAIN_CONFLICT", str(exc))
    values: dict[str, Any] = {
        "accepted_inputs": body.accepted_inputs or item.accepted_inputs,
        "output_specifications": body.output_specifications or item.output_specifications,
        "transformation_ids": body.transformation_ids or item.transformation_ids,
        "capacity_value": capacity.value,
        "minimum_batch_value": minimum_batch.value if minimum_batch is not None else None,
        "location_id": location.id,
        "operating_window_start": start,
        "operating_window_end": end,
        "processing_cost": body.processing_cost or item.processing_cost,
        "certifications": body.certifications or item.certifications,
        "regulatory_constraints": body.regulatory_constraints or item.regulatory_constraints,
        "status": status.value,
        "version": next_version,
        "updated_at": datetime.now(UTC),
    }
    if body.provenance is not None:
        values["provenance"] = body.provenance
    result = session.execute(
        update(Capability)
        .where(
            Capability.id == capability_id,
            Capability.organization_id == principal.organization_id,
            Capability.version == expected,
        )
        .values(**values)
    )
    if result.rowcount != 1:
        session.rollback()
        _fail(request, 412, "STALE_VERSION", "CONCURRENCY", "Capability version is stale.")
    _remember(session, principal.organization_id, idempotency_key, digest, capability_id)
    updated = _find(session, capability_id, principal.organization_id)
    _event(
        session,
        request,
        principal.organization_id,
        principal.actor_id,
        "capability.updated",
        updated,
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
        _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "Capability mutation conflicted.")
    except SQLAlchemyError:
        session.rollback()
        _database_error(request)
    item = _find(session, capability_id, principal.organization_id)
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))
