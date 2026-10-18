"""Transformation v1 API for the canonical declarative process model."""

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
from crr.domain.errors import DomainError
from crr.domain.quantity import Quantity
from crr.domain.transformation import Transformation as DomainTransformation
from crr.domain.transformation import TransformationStatus
from crr.models import IdempotencyRecord, Location, OutboxEvent
from crr.transformation_model import Transformation
from crr.transformation_schemas import TransformationInput, TransformationPatch

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


def _find(session: Session, item_id: str, organization_id: str):
    return session.scalar(
        select(Transformation).where(
            Transformation.id == item_id,
            Transformation.organization_id == organization_id,
        )
    )


def _data(item: Transformation) -> dict[str, Any]:
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "input_specifications": item.input_specifications,
        "output_specifications": item.output_specifications,
        "yield": {
            "min": str(item.yield_min_value),
            "target": str(item.yield_target_value),
            "max": str(item.yield_max_value),
        },
        "loss_residuals": item.loss_residuals,
        "duration_seconds": item.duration_seconds,
        "capacity": {
            "value": str(item.capacity_value),
            "unit": item.unit,
            "unit_registry_version": item.unit_registry_version,
        },
        "cost_metadata": item.cost_metadata,
        "quality_effects": item.quality_effects,
        "regulatory_requirements": item.regulatory_requirements,
        "eligible_capability_ids": item.eligible_capability_ids,
        "eligible_location_ids": item.eligible_location_ids,
        "status": item.status,
        "version": item.version,
        "created_by": item.created_by,
        "provenance": item.provenance,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _domain(item: Transformation) -> DomainTransformation:
    return DomainTransformation(
        id=item.id,
        organization_id=item.organization_id,
        input_specifications=tuple(item.input_specifications),
        output_specifications=tuple(item.output_specifications),
        yield_min=item.yield_min_value,
        yield_target=item.yield_target_value,
        yield_max=item.yield_max_value,
        loss_residuals=tuple(item.loss_residuals),
        duration_seconds=item.duration_seconds,
        capacity=Quantity(item.capacity_value, item.unit, item.unit_registry_version),
        cost_metadata=item.cost_metadata,
        quality_effects=item.quality_effects,
        regulatory_requirements=item.regulatory_requirements,
        eligible_capability_ids=tuple(item.eligible_capability_ids),
        eligible_location_ids=tuple(item.eligible_location_ids),
        status=TransformationStatus(item.status),
        version=item.version,
        created_by=item.created_by,
        provenance=item.provenance,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _check_refs(
    request: Request,
    session: Session,
    organization_id: str,
    capability_ids: list[str],
    location_ids: list[str],
) -> None:
    if len(set(capability_ids)) != len(capability_ids) or len(set(location_ids)) != len(location_ids):
        _fail(
            request,
            422,
            "INVALID_REFERENCE",
            "VALIDATION_FAILURE",
            "Reference identifiers must be unique.",
        )
    if capability_ids:
        found = set(
            session.scalars(
                select(Capability.id).where(
                    Capability.organization_id == organization_id,
                    Capability.id.in_(capability_ids),
                )
            ).all()
        )
        if found != set(capability_ids):
            _fail(
                request,
                404,
                "NOT_FOUND",
                "NOT_FOUND",
                "One or more Capability references were not found.",
            )
    if location_ids:
        found = set(
            session.scalars(
                select(Location.id).where(
                    Location.organization_id == organization_id,
                    Location.id.in_(location_ids),
                )
            ).all()
        )
        if found != set(location_ids):
            _fail(
                request,
                404,
                "NOT_FOUND",
                "NOT_FOUND",
                "One or more Location references were not found.",
            )


def _validate(request: Request, session: Session, item: DomainTransformation) -> None:
    try:
        request.app.state.unit_registry.validate(item.capacity)
    except DomainError as exc:
        _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))
    _check_refs(
        request,
        session,
        item.organization_id,
        list(item.eligible_capability_ids),
        list(item.eligible_location_ids),
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
    if prior and (prior.request_hash != digest or prior.object_type != "Transformation"):
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
) -> None:
    session.add(
        IdempotencyRecord(
            organization_id=organization_id,
            idempotency_key=key,
            request_hash=digest,
            object_type="Transformation",
            object_id=object_id,
            created_at=datetime.now(UTC),
        )
    )


def _event(
    session: Session,
    request: Request,
    principal: Any,
    event_type: str,
    item: Transformation,
    key: str,
) -> None:
    session.add(
        OutboxEvent(
            id=f"evt_{uuid4().hex}",
            event_type=event_type,
            event_version=1,
            aggregate_type="Transformation",
            aggregate_id=item.id,
            aggregate_version=item.version,
            organization_id=principal.organization_id,
            actor_id=principal.actor_id,
            occurred_at=datetime.now(UTC),
            published_at=None,
            correlation_id=request.state.request_id,
            causation_id=None,
            idempotency_key=key,
            payload={
                "transformation_id": item.id,
                "status": item.status,
                "version": item.version,
            },
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


@router.get("/v1/transformations")
def list_transformations(
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("transformations:read"))],
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
):
    statement = select(Transformation).where(Transformation.organization_id == principal.organization_id)
    if cursor:
        statement = statement.where(Transformation.id > cursor)
    rows = session.scalars(statement.order_by(Transformation.id).limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].id if has_more and rows else None
    return _collection(request, [_data(row) for row in rows], next_cursor, has_more, limit)


@router.get("/v1/transformations/{transformation_id}")
def get_transformation(
    transformation_id: str,
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("transformations:read"))],
):
    item = _find(session, transformation_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Transformation not found.")
    return _envelope(request, _data(item))


@router.post("/v1/transformations", status_code=201)
def create_transformation(
    body: TransformationInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("transformations:write"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    payload = body.model_dump(mode="json")
    digest = _body_hash(payload)
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        item = _find(session, prior.object_id, principal.organization_id)
        if item is None:
            _fail(
                request,
                409,
                "IDEMPOTENCY_STATE_MISSING",
                "DOMAIN_CONFLICT",
                "Idempotent result is unavailable.",
            )
        response.status_code = 200
        response.headers["ETag"] = f'"version-{item.version}"'
        return _envelope(request, _data(item))
    now = datetime.now(UTC)
    item = Transformation(
        id=body.id or f"trn_{uuid4().hex}",
        organization_id=principal.organization_id,
        input_specifications=body.input_specifications,
        output_specifications=body.output_specifications,
        yield_min_value=body.yield_min,
        yield_target_value=body.yield_target,
        yield_max_value=body.yield_max,
        loss_residuals=body.loss_residuals,
        duration_seconds=body.duration_seconds,
        capacity_value=body.capacity,
        unit=body.unit,
        unit_registry_version=body.unit_registry_version,
        cost_metadata=body.cost_metadata,
        quality_effects=body.quality_effects,
        regulatory_requirements=body.regulatory_requirements,
        eligible_capability_ids=body.eligible_capability_ids,
        eligible_location_ids=body.eligible_location_ids,
        status=body.status,
        version=1,
        created_by=principal.actor_id,
        provenance=body.provenance,
        created_at=now,
        updated_at=now,
    )
    _validate(request, session, _domain(item))
    session.add(item)
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _event(session, request, principal, "transformation.created", item, idempotency_key)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "Transformation creation conflicted.")
    except SQLAlchemyError:
        session.rollback()
        _fail(request, 503, "DATABASE_UNAVAILABLE", "DATABASE_FAILURE", "Database operation failed.")
    response.headers["ETag"] = '"version-1"'
    return _envelope(request, _data(item))


@router.patch("/v1/transformations/{transformation_id}")
def patch_transformation(
    transformation_id: str,
    body: TransformationPatch,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("transformations:write"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    expected = _if_match(request, if_match)
    payload = body.model_dump(mode="json") | {
        "transformation_id": transformation_id,
        "expected_version": expected,
    }
    digest = _body_hash(payload)
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        item = _find(session, prior.object_id, principal.organization_id)
        if item is None:
            _fail(
                request,
                409,
                "IDEMPOTENCY_STATE_MISSING",
                "DOMAIN_CONFLICT",
                "Idempotent result is unavailable.",
            )
        response.status_code = 200
        response.headers["ETag"] = f'"version-{item.version}"'
        return _envelope(request, _data(item))
    item = _find(session, transformation_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Transformation not found.")
    if item.version != expected:
        _fail(request, 412, "STALE_VERSION", "CONCURRENCY", "Transformation version is stale.")

    values = body.model_dump(exclude_unset=True)
    merged: dict[str, Any] = {
        "input_specifications": item.input_specifications,
        "output_specifications": item.output_specifications,
        "yield_min": item.yield_min_value,
        "yield_target": item.yield_target_value,
        "yield_max": item.yield_max_value,
        "loss_residuals": item.loss_residuals,
        "duration_seconds": item.duration_seconds,
        "capacity": item.capacity_value,
        "unit": item.unit,
        "unit_registry_version": item.unit_registry_version,
        "cost_metadata": item.cost_metadata,
        "quality_effects": item.quality_effects,
        "regulatory_requirements": item.regulatory_requirements,
        "eligible_capability_ids": item.eligible_capability_ids,
        "eligible_location_ids": item.eligible_location_ids,
        "status": item.status,
        "provenance": item.provenance,
    }
    merged.update(values)
    status = TransformationStatus(merged["status"])
    base = _domain(item)
    now = datetime.now(UTC)
    if status != base.status:
        new_version = base.transition(status, now).version
    else:
        new_version = item.version + 1

    candidate = DomainTransformation(
        id=item.id,
        organization_id=item.organization_id,
        input_specifications=tuple(merged["input_specifications"]),
        output_specifications=tuple(merged["output_specifications"]),
        yield_min=Decimal(merged["yield_min"]),
        yield_target=Decimal(merged["yield_target"]),
        yield_max=Decimal(merged["yield_max"]),
        loss_residuals=tuple(merged["loss_residuals"]),
        duration_seconds=merged["duration_seconds"],
        capacity=Quantity(
            Decimal(merged["capacity"]),
            merged["unit"],
            merged["unit_registry_version"],
        ),
        cost_metadata=merged["cost_metadata"],
        quality_effects=merged["quality_effects"],
        regulatory_requirements=merged["regulatory_requirements"],
        eligible_capability_ids=tuple(merged["eligible_capability_ids"]),
        eligible_location_ids=tuple(merged["eligible_location_ids"]),
        status=status,
        version=new_version,
        created_by=item.created_by,
        provenance=merged["provenance"],
        created_at=item.created_at,
        updated_at=now,
    )
    _validate(request, session, candidate)
    result = session.execute(
        update(Transformation)
        .where(
            Transformation.id == item.id,
            Transformation.organization_id == principal.organization_id,
            Transformation.version == expected,
        )
        .values(
            input_specifications=list(candidate.input_specifications),
            output_specifications=list(candidate.output_specifications),
            yield_min_value=candidate.yield_min,
            yield_target_value=candidate.yield_target,
            yield_max_value=candidate.yield_max,
            loss_residuals=list(candidate.loss_residuals),
            duration_seconds=candidate.duration_seconds,
            capacity_value=candidate.capacity.value,
            unit=candidate.capacity.unit,
            unit_registry_version=candidate.capacity.unit_registry_version,
            cost_metadata=candidate.cost_metadata,
            quality_effects=candidate.quality_effects,
            regulatory_requirements=candidate.regulatory_requirements,
            eligible_capability_ids=list(candidate.eligible_capability_ids),
            eligible_location_ids=list(candidate.eligible_location_ids),
            status=candidate.status.value,
            version=candidate.version,
            provenance=candidate.provenance,
            updated_at=now,
        )
    )
    if result.rowcount != 1:
        session.rollback()
        _fail(request, 412, "STALE_VERSION", "CONCURRENCY", "Transformation version is stale.")
    item = _find(session, transformation_id, principal.organization_id)
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _event(session, request, principal, "transformation.updated", item, idempotency_key)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "Transformation update conflicted.")
    except SQLAlchemyError:
        session.rollback()
        _fail(request, 503, "DATABASE_UNAVAILABLE", "DATABASE_FAILURE", "Database operation failed.")
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))
