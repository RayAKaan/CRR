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
from crr.models import Actor, IdempotencyRecord, Location, OutboxEvent
from crr.transformation_model import Transformation
from crr.transformation_schemas import TransformationInput, TransformationPatch
from crr.domain.errors import DomainError
from crr.domain.quantity import Quantity
from crr.domain.transformation import Transformation as DomainTransformation
from crr.domain.transformation import TransformationStatus

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


def _body_hash(payload: dict[str, Any]) -> str:
    return _api()._body_hash(payload)


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


def _find(session: Session, item_id: str, organization_id: str):
    return session.scalar(
        select(Transformation).where(
            Transformation.id == item_id,
            Transformation.organization_id == organization_id,
        )
    )


def _idempotency(session, organization_id, key, digest, request):
    if not key or not key.strip() or len(key) > 255:
        _fail(request, 400, "IDEMPOTENCY_KEY_REQUIRED", "VALIDATION_FAILURE", "A valid Idempotency-Key is required.")
    return session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.organization_id == organization_id,
            IdempotencyRecord.idempotency_key == key,
        )
    )


def _check_reuse(prior, digest, request):
    if prior and (prior.request_hash != digest or prior.object_type != "Transformation"):
        _fail(request, 409, "IDEMPOTENCY_CONFLICT", "DOMAIN_CONFLICT", "Idempotency key was reused with a different request.")


def _remember(session, organization_id, key, digest, item_id):
    session.add(
        IdempotencyRecord(
            organization_id=organization_id,
            idempotency_key=key,
            request_hash=digest,
            object_type="Transformation",
            object_id=item_id,
            created_at=datetime.now(UTC),
        )
    )


def _event(session, request, organization_id, actor_id, event_type, item, key):
    session.add(
        OutboxEvent(
            id=f"evt_{uuid4().hex}",
            event_type=event_type,
            event_version=1,
            aggregate_type="Transformation",
            aggregate_id=item.id,
            aggregate_version=item.version,
            organization_id=organization_id,
            actor_id=actor_id,
            occurred_at=datetime.now(UTC),
            published_at=None,
            correlation_id=request.state.request_id,
            causation_id=None,
            idempotency_key=key,
            payload={"transformation_id": item.id, "status": item.status, "version": item.version},
            provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
            schema_version="0.1",
        )
    )


def _if_match(request, value: str | None) -> int:
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


def _references(request, session, organization_id, capability_ids, location_ids):
    capabilities = set(capability_ids)
    locations = set(location_ids)
    if len(capabilities) != len(capability_ids) or len(locations) != len(location_ids):
        _fail(request, 422, "INVALID_REFERENCE", "VALIDATION_FAILURE", "Reference identifiers must be unique.")
    if capabilities:
        found = set(session.scalars(select(Capability.id).where(Capability.organization_id == organization_id, Capability.id.in_(capabilities))).all())
        if found != capabilities:
            _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "One or more Capability references were not found.")
    if locations:
        found = set(session.scalars(select(Location.id).where(Location.organization_id == organization_id, Location.id.in_(locations))).all())
        if found != locations:
            _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "One or more Location references were not found.")


def _validate(request, session, item: DomainTransformation):
    try:
        request.app.state.unit_registry.validate(item.capacity)
    except DomainError as exc:
        _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))
    _references(request, session, item.organization_id, item.eligible_capability_ids, item.eligible_location_ids)


@router.get("/v1/transformations")
def list_transformations(
    request: Request,
    session: Annotated[Session, Depends(_api().db_session)],
    principal: Annotated[Any, Depends(_api().scope_required("transformations:read"))],
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
):
    statement = select(Transformation).where(Transformation.organization_id == principal.organization_id)
    if cursor:
        statement = statement.where(Transformation.id > cursor)
    rows = session.scalars(statement.order_by(Transformation.id).limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    return _collection(request, [_data(row) for row in rows], rows[-1].id if has_more and rows else None, has_more, limit)


@router.get("/v1/transformations/{transformation_id}")
def get_transformation(
    transformation_id: str,
    request: Request,
    session: Annotated[Session, Depends(_api().db_session)],
    principal: Annotated[Any, Depends(_api().scope_required("transformations:read"))],
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
    session: Annotated[Session, Depends(_api().db_session)],
    principal: Annotated[Any, Depends(_api().scope_required("transformations:write"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    payload = body.model_dump(mode="json")
    digest = _body_hash(payload)
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    _check_reuse(prior, digest, request)
    if prior:
        item = _find(session, prior.object_id, principal.organization_id)
        if item is None:
            _fail(request, 409, "IDEMPOTENCY_STATE_MISSING", "DOMAIN_CONFLICT", "Idempotent result is unavailable.")
        response.status_code = 200
        response.headers["ETag"] = f'"version-{item.version}"'
        return _envelope(request, _data(item))
    now = datetime.now(UTC)
    item_id = body.id or f"trn_{uuid4().hex}"
    item = Transformation(
        id=item_id,
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
    try:
        _validate(request, session, _domain(item))
    except DomainError as exc:
        _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))
    session.add(item)
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _event(session, request, principal.organization_id, principal.actor_id, "transformation.created", item, idempotency_key)
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
    session: Annotated[Session, Depends(_api().db_session)],
    principal: Annotated[Any, Depends(_api().scope_required("transformations:write"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    expected = _if_match(request, if_match)
    payload = body.model_dump(mode="json") | {"transformation_id": transformation_id, "expected_version": expected}
    digest = _body_hash(payload)
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    _check_reuse(prior, digest, request)
    if prior:
        item = _find(session, prior.object_id, principal.organization_id)
        if item is None:
            _fail(request, 409, "IDEMPOTENCY_STATE_MISSING", "DOMAIN_CONFLICT", "Idempotent result is unavailable.")
        response.status_code = 200
        response.headers["ETag"] = f'"version-{item.version}"'
        return _envelope(request, _data(item))
    item = _find(session, transformation_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Transformation not found.")
    if item.version != expected:
        _fail(request, 412, "STALE_VERSION", "CONCURRENCY", "Transformation version is stale.")
    values = body.model_dump(exclude_unset=True)
    current = {
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
    current.update(values)
    now = datetime.now(UTC)
    candidate = DomainTransformation(
        id=item.id,
        organization_id=item.organization_id,
        input_specifications=tuple(current["input_specifications"]),
        output_specifications=tuple(current["output_specifications"]),
        yield_min=Decimal(current["yield_min"]),
        yield_target=Decimal(current["yield_target"]),
        yield_max=Decimal(current["yield_max"]),
        loss_residuals=tuple(current["loss_residuals"]),
        duration_seconds=current["duration_seconds"],
        capacity=Quantity(current["capacity"], current["unit"], current["unit_registry_version"]),
        cost_metadata=current["cost_metadata"],
        quality_effects=current["quality_effects"],
        regulatory_requirements=current["regulatory_requirements"],
        eligible_capability_ids=tuple(current["eligible_capability_ids"]),
        eligible_location_ids=tuple(current["eligible_location_ids"]),
        status=TransformationStatus(current["status"]),
        version=item.version,
        created_by=item.created_by,
        provenance=current["provenance"],
        created_at=item.created_at,
        updated_at=now,
    )
    if "status" in values and TransformationStatus(current["status"]) != TransformationStatus(item.status):
        candidate = _domain(item).transition(TransformationStatus(current["status"]), now)
        candidate = DomainTransformation(
            id=candidate.id, organization_id=candidate.organization_id,
            input_specifications=tuple(current["input_specifications"]),
            output_specifications=tuple(current["output_specifications"]),
            yield_min=Decimal(current["yield_min"]), yield_target=Decimal(current["yield_target"]), yield_max=Decimal(current["yield_max"]),
            loss_residuals=tuple(current["loss_residuals"]), duration_seconds=current["duration_seconds"],
            capacity=Quantity(current["capacity"], current["unit"], current["unit_registry_version"]),
            cost_metadata=current["cost_metadata"], quality_effects=current["quality_effects"], regulatory_requirements=current["regulatory_requirements"],
            eligible_capability_ids=tuple(current["eligible_capability_ids"]), eligible_location_ids=tuple(current["eligible_location_ids"]),
            status=candidate.status, version=candidate.version, created_by=candidate.created_by, provenance=current["provenance"], created_at=item.created_at, updated_at=now,
        )
    else:
        candidate = DomainTransformation(**{**candidate.__dict__}) if False else candidate
        candidate = DomainTransformation(
            id=candidate.id, organization_id=candidate.organization_id,
            input_specifications=candidate.input_specifications, output_specifications=candidate.output_specifications,
            yield_min=candidate.yield_min, yield_target=candidate.yield_target, yield_max=candidate.yield_max,
            loss_residuals=candidate.loss_residuals, duration_seconds=candidate.duration_seconds, capacity=candidate.capacity,
            cost_metadata=candidate.cost_metadata, quality_effects=candidate.quality_effects, regulatory_requirements=candidate.regulatory_requirements,
            eligible_capability_ids=candidate.eligible_capability_ids, eligible_location_ids=candidate.eligible_location_ids,
            status=candidate.status, version=item.version + 1, created_by=candidate.created_by, provenance=candidate.provenance,
            created_at=candidate.created_at, updated_at=now,
        )
    try:
        _validate(request, session, candidate)
    except DomainError as exc:
        _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))
    result = session.execute(
        update(Transformation)
        .where(Transformation.id == item.id, Transformation.organization_id == principal.organization_id, Transformation.version == expected)
        .values(
            input_specifications=list(candidate.input_specifications), output_specifications=list(candidate.output_specifications),
            yield_min_value=candidate.yield_min, yield_target_value=candidate.yield_target, yield_max_value=candidate.yield_max,
            loss_residuals=list(candidate.loss_residuals), duration_seconds=candidate.duration_seconds,
            capacity_value=candidate.capacity.value, unit=candidate.capacity.unit, unit_registry_version=candidate.capacity.unit_registry_version,
            cost_metadata=candidate.cost_metadata, quality_effects=candidate.quality_effects, regulatory_requirements=candidate.regulatory_requirements,
            eligible_capability_ids=list(candidate.eligible_capability_ids), eligible_location_ids=list(candidate.eligible_location_ids),
            status=candidate.status.value, version=candidate.version, provenance=candidate.provenance, updated_at=now,
        )
    )
    if result.rowcount != 1:
        session.rollback()
        _fail(request, 412, "STALE_VERSION", "CONCURRENCY", "Transformation version is stale.")
    item = _find(session, transformation_id, principal.organization_id)
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _event(session, request, principal.organization_id, principal.actor_id, "transformation.updated", item, idempotency_key)
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
