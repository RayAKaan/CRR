"""Tenant-isolated Phase 1 REST API."""

import hashlib
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from crr.database import SessionLocal
from crr.domain import Quantity, TransitionKind, transition_state
from crr.domain import ResourceState as DomainState
from crr.domain.errors import DomainError
from crr.models import (
    Actor,
    APIKey,
    IdempotencyRecord,
    Location,
    Organization,
    OutboxEvent,
    Resource,
    ResourceState,
    StateTransition,
)
from crr.schemas import (
    ActorCreate,
    LocationCreate,
    ResourceCreate,
    ResourceStateCreate,
    ResourceStateTransitionCreate,
)
from crr.unit_registry import load_unit_registry

bearer = HTTPBearer(auto_error=False)


class Principal:
    def __init__(self, organization_id: str, actor_id: str, scopes: list[str]):
        self.organization_id = organization_id
        self.actor_id = actor_id
        self.scopes = frozenset(scopes)


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _body_hash(payload: dict) -> str:
    return _hash(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def _fail(request: Request, status: int, code: str, category: str, message: str):
    raise HTTPException(
        status_code=status,
        detail={
            "error": {
                "code": code,
                "category": category,
                "severity": "BLOCKING",
                "message": message,
                "details": [],
                "retryable": status in (429, 502, 503, 504),
                "request_id": request.state.request_id,
                "correlation_id": request.state.request_id,
            }
        },
    )


def _envelope(request: Request, data):
    return {
        "data": data,
        "meta": {
            "request_id": request.state.request_id,
            "api_version": "v1",
            "schema_version": "0.1",
        },
    }


def _state_data(state: ResourceState) -> dict:
    return {
        "id": state.id,
        "resource_id": state.resource_id,
        "organization_id": state.organization_id,
        "version": state.resource_version,
        "state_type": state.state_type,
        "quantity": {
            "value": str(state.quantity_value),
            "unit": state.unit,
            "unit_registry_version": state.unit_registry_version,
        },
        "location_id": state.location_id,
        "effective_at": state.effective_at.isoformat(),
        "recorded_at": state.recorded_at.isoformat(),
        "created_by": state.created_by,
        "provenance": state.provenance,
        "quality": state.quality,
        "physical_properties": state.physical_properties,
        "predecessor_state_ids": state.predecessor_state_ids,
    }


def db_session(request: Request):
    with request.app.state.session_factory() as session:
        yield session


def principal_for(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    session: Annotated[Session, Depends(db_session)],
    request: Request,
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        _fail(
            request,
            401,
            "AUTHENTICATION_REQUIRED",
            "AUTHENTICATION",
            "A bearer API key is required.",
        )
    key = session.scalar(
        select(APIKey).where(
            APIKey.secret_hash == _hash(credentials.credentials), APIKey.revoked.is_(False)
        )
    )
    if key is None:
        _fail(request, 401, "INVALID_CREDENTIAL", "AUTHENTICATION", "API key is invalid.")
    actor = session.scalar(
        select(Actor).where(
            Actor.id == key.actor_id,
            Actor.organization_id == key.organization_id,
            Actor.active.is_(True),
        )
    )
    if actor is None:
        _fail(request, 401, "INVALID_ACTOR", "AUTHENTICATION", "API key actor is inactive.")
    return Principal(key.organization_id, key.actor_id, key.scopes)


def scope_required(scope: str) -> Callable:
    def dependency(
        principal: Annotated[Principal, Depends(principal_for)],
        request: Request,
    ) -> Principal:
        if scope not in principal.scopes and "admin:*" not in principal.scopes:
            _fail(request, 403, "SCOPE_REQUIRED", "AUTHORIZATION", f"Required scope: {scope}.")
        return principal

    return dependency


def create_app(session_factory: sessionmaker = SessionLocal, unit_registry=None) -> FastAPI:
    app = FastAPI(title="CRR Reference API", version="v1")
    app.state.session_factory = session_factory
    app.state.unit_registry = unit_registry or load_unit_registry()

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        supplied_id = request.headers.get("X-Request-ID", "")
        request.state.request_id = (
            supplied_id
            if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", supplied_id)
            else f"req_{uuid4().hex}"
        )
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @app.exception_handler(HTTPException)
    async def http_errors(request: Request, exc: HTTPException):
        detail = (
            exc.detail
            if isinstance(exc.detail, dict)
            else {
                "error": {
                    "code": "HTTP_ERROR",
                    "category": "REQUEST_FAILURE",
                    "severity": "BLOCKING",
                    "message": str(exc.detail),
                    "details": [],
                    "retryable": False,
                    "request_id": request.state.request_id,
                    "correlation_id": request.state.request_id,
                }
            }
        )
        return Response(
            json.dumps(detail), status_code=exc.status_code, media_type="application/json"
        )

    @app.exception_handler(RequestValidationError)
    async def request_errors(request: Request, exc: RequestValidationError):
        details = [
            {"path": ".".join(map(str, item["loc"])), "message": item["msg"]}
            for item in exc.errors()
        ]
        return Response(
            json.dumps(
                {
                    "error": {
                        "code": "REQUEST_VALIDATION_FAILED",
                        "category": "VALIDATION_FAILURE",
                        "severity": "BLOCKING",
                        "message": "Request did not satisfy the API schema.",
                        "details": details,
                        "retryable": False,
                        "request_id": request.state.request_id,
                        "correlation_id": request.state.request_id,
                    }
                }
            ),
            status_code=422,
            media_type="application/json",
        )

    def check_idempotency(session, principal, key, digest, request, object_type):
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
                IdempotencyRecord.organization_id == principal.organization_id,
                IdempotencyRecord.idempotency_key == key,
            )
        )
        if prior and (prior.request_hash != digest or prior.object_type != object_type):
            _fail(
                request,
                409,
                "IDEMPOTENCY_CONFLICT",
                "DOMAIN_CONFLICT",
                "Idempotency key was reused with a different request.",
            )
        return prior

    def remember(session, principal, key, digest, obj_type, obj_id):
        session.add(
            IdempotencyRecord(
                organization_id=principal.organization_id,
                idempotency_key=key,
                request_hash=digest,
                object_type=obj_type,
                object_id=obj_id,
                created_at=datetime.now(UTC),
            )
        )

    def emit(
        session,
        request,
        principal,
        event_type,
        aggregate_type,
        aggregate_id,
        aggregate_version,
        payload,
        key=None,
        causation_id=None,
    ):
        session.add(
            OutboxEvent(
                id=f"evt_{uuid4().hex}",
                event_type=event_type,
                event_version=1,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                aggregate_version=aggregate_version,
                organization_id=principal.organization_id,
                actor_id=principal.actor_id,
                occurred_at=datetime.now(UTC),
                published_at=None,
                correlation_id=request.state.request_id,
                causation_id=causation_id,
                idempotency_key=key,
                payload=payload,
                provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
                schema_version="0.1",
            )
        )

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/v1/organizations/{organization_id}")
    def get_organization(
        organization_id: str,
        request: Request,
        session: Annotated[Session, Depends(db_session)],
        principal: Annotated[Principal, Depends(scope_required("organizations:read"))],
    ):
        if organization_id != principal.organization_id:
            _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Organization not found.")
        org = session.get(Organization, organization_id)
        if org is None:
            _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Organization not found.")
        return _envelope(request, {"id": org.id, "name": org.name, "status": org.status})

    @app.get("/v1/actors/{actor_id}")
    def get_actor(
        actor_id: str,
        request: Request,
        session: Annotated[Session, Depends(db_session)],
        principal: Annotated[Principal, Depends(scope_required("actors:read"))],
    ):
        actor = session.scalar(
            select(Actor).where(
                Actor.id == actor_id,
                Actor.organization_id == principal.organization_id,
            )
        )
        if actor is None:
            _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Actor not found.")
        return _envelope(
            request,
            {
                "id": actor.id,
                "organization_id": actor.organization_id,
                "name": actor.name,
                "role": actor.role,
                "active": actor.active,
            },
        )

    @app.post("/v1/actors", status_code=201)
    def create_actor(
        body: ActorCreate,
        request: Request,
        response: Response,
        session: Annotated[Session, Depends(db_session)],
        principal: Annotated[Principal, Depends(scope_required("actors:write"))],
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ):
        payload = body.model_dump(mode="json")
        digest = _body_hash(payload)
        prior = check_idempotency(session, principal, idempotency_key, digest, request, "Actor")
        if prior:
            response.status_code = 200
            actor = session.scalar(
                select(Actor).where(
                    Actor.id == prior.object_id,
                    Actor.organization_id == principal.organization_id,
                )
            )
            return _envelope(
                request,
                {
                    "id": actor.id,
                    "organization_id": actor.organization_id,
                    "name": actor.name,
                    "role": actor.role,
                    "version": 1,
                },
            )
        actor = Actor(
            id=body.id or f"act_{uuid4().hex}",
            organization_id=principal.organization_id,
            name=body.name,
            role=body.role,
            active=True,
            created_at=datetime.now(UTC),
        )
        session.add(actor)
        remember(session, principal, idempotency_key, digest, "Actor", actor.id)
        emit(
            session,
            request,
            principal,
            "actor.created",
            "Actor",
            actor.id,
            1,
            {"actor_id": actor.id, "role": actor.role},
            idempotency_key,
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "Actor creation conflicted.")
        except SQLAlchemyError:
            session.rollback()
            _fail(
                request,
                503,
                "DATABASE_UNAVAILABLE",
                "DATABASE_FAILURE",
                "Database operation failed.",
            )
        return _envelope(
            request,
            {
                "id": actor.id,
                "organization_id": actor.organization_id,
                "name": actor.name,
                "role": actor.role,
                "version": 1,
            },
        )

    @app.get("/v1/locations/{location_id}")
    def get_location(
        location_id: str,
        request: Request,
        session: Annotated[Session, Depends(db_session)],
        principal: Annotated[Principal, Depends(scope_required("locations:read"))],
    ):
        item = session.scalar(
            select(Location).where(
                Location.id == location_id,
                Location.organization_id == principal.organization_id,
            )
        )
        if item is None:
            _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Location not found.")
        return _envelope(
            request,
            {
                "id": item.id,
                "organization_id": item.organization_id,
                "name": item.name,
                "address": item.address,
                "latitude": item.latitude,
                "longitude": item.longitude,
                "jurisdiction": item.jurisdiction,
                "provenance": item.provenance,
                "created_at": item.created_at.isoformat(),
            },
        )

    @app.post("/v1/locations", status_code=201)
    def create_location(
        body: LocationCreate,
        request: Request,
        response: Response,
        session: Annotated[Session, Depends(db_session)],
        principal: Annotated[Principal, Depends(scope_required("locations:write"))],
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ):
        payload = body.model_dump(mode="json")
        digest = _body_hash(payload)
        prior = check_idempotency(session, principal, idempotency_key, digest, request, "Location")
        if prior:
            response.status_code = 200
            item = session.scalar(
                select(Location).where(
                    Location.id == prior.object_id,
                    Location.organization_id == principal.organization_id,
                )
            )
            return _envelope(request, {"id": item.id, "name": item.name})
        item = Location(
            id=body.id or f"loc_{uuid4().hex}",
            organization_id=principal.organization_id,
            name=body.name,
            address=body.address,
            latitude=body.latitude,
            longitude=body.longitude,
            jurisdiction=body.jurisdiction,
            provenance=body.provenance,
            created_at=datetime.now(UTC),
        )
        session.add(item)
        remember(session, principal, idempotency_key, digest, "Location", item.id)
        emit(
            session,
            request,
            principal,
            "location.created",
            "Location",
            item.id,
            1,
            {"location_id": item.id},
            idempotency_key,
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "Location creation conflicted.")
        except SQLAlchemyError:
            session.rollback()
            _fail(
                request,
                503,
                "DATABASE_UNAVAILABLE",
                "DATABASE_FAILURE",
                "Database operation failed.",
            )
        return _envelope(
            request, {"id": item.id, "organization_id": item.organization_id, "name": item.name}
        )

    @app.get("/v1/resources/{resource_id}")
    def get_resource(
        resource_id: str,
        request: Request,
        session: Annotated[Session, Depends(db_session)],
        principal: Annotated[Principal, Depends(scope_required("resources:read"))],
    ):
        item = session.scalar(
            select(Resource).where(
                Resource.id == resource_id,
                Resource.organization_id == principal.organization_id,
            )
        )
        if item is None:
            _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Resource not found.")
        latest_state = session.scalar(
            select(ResourceState)
            .where(
                ResourceState.resource_id == item.id,
                ResourceState.organization_id == principal.organization_id,
            )
            .order_by(ResourceState.resource_version.desc())
            .limit(1)
        )
        return _envelope(
            request,
            {
                "id": item.id,
                "organization_id": item.organization_id,
                "resource_type": item.resource_type,
                "description": item.description,
                "version": item.version,
                "current_state_id": latest_state.id if latest_state else None,
                "provenance": item.provenance,
                "created_at": item.created_at.isoformat(),
            },
        )

    @app.post("/v1/resources", status_code=201)
    def create_resource(
        body: ResourceCreate,
        request: Request,
        response: Response,
        session: Annotated[Session, Depends(db_session)],
        principal: Annotated[Principal, Depends(scope_required("resources:write"))],
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ):
        payload = body.model_dump(mode="json")
        digest = _body_hash(payload)
        prior = check_idempotency(session, principal, idempotency_key, digest, request, "Resource")
        if prior:
            response.status_code = 200
            item = session.scalar(
                select(Resource).where(
                    Resource.id == prior.object_id,
                    Resource.organization_id == principal.organization_id,
                )
            )
            return _envelope(
                request,
                {"id": item.id, "resource_type": item.resource_type, "version": item.version},
            )
        item = Resource(
            id=body.id or f"res_{uuid4().hex}",
            organization_id=principal.organization_id,
            resource_type=body.resource_type,
            description=body.description,
            version=0,
            created_by=principal.actor_id,
            provenance=body.provenance,
            created_at=datetime.now(UTC),
        )
        session.add(item)
        remember(session, principal, idempotency_key, digest, "Resource", item.id)
        emit(
            session,
            request,
            principal,
            "resource.created",
            "Resource",
            item.id,
            1,
            {"resource_id": item.id},
            idempotency_key,
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "Resource creation conflicted.")
        except SQLAlchemyError:
            session.rollback()
            _fail(
                request,
                503,
                "DATABASE_UNAVAILABLE",
                "DATABASE_FAILURE",
                "Database operation failed.",
            )
        return _envelope(
            request,
            {
                "id": item.id,
                "organization_id": item.organization_id,
                "resource_type": item.resource_type,
                "version": item.version,
            },
        )

    @app.post("/v1/resource-states", status_code=201)
    def create_initial_state(
        body: ResourceStateCreate,
        request: Request,
        response: Response,
        session: Annotated[Session, Depends(db_session)],
        principal: Annotated[Principal, Depends(scope_required("resources:write"))],
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ):
        payload = body.model_dump(mode="json")
        digest = _body_hash(payload)
        prior = check_idempotency(
            session, principal, idempotency_key, digest, request, "ResourceState"
        )
        if prior:
            item = session.scalar(
                select(ResourceState).where(
                    ResourceState.id == prior.object_id,
                    ResourceState.organization_id == principal.organization_id,
                )
            )
            response.status_code = 200
            return _envelope(request, _state_data(item))
        resource = session.scalar(
            select(Resource).where(
                Resource.id == body.resource_id,
                Resource.organization_id == principal.organization_id,
            )
        )
        location = session.scalar(
            select(Location).where(
                Location.id == body.location_id,
                Location.organization_id == principal.organization_id,
            )
        )
        if resource is None or location is None:
            _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Resource or location not found.")
        if resource.version != 0:
            _fail(
                request,
                409,
                "CONFLICT",
                "DOMAIN_CONFLICT",
                "An initial state already exists; use an explicit transition.",
            )
        quantity = Quantity(
            body.quantity.value, body.quantity.unit, body.quantity.unit_registry_version
        )
        try:
            app.state.unit_registry.validate(quantity)
        except DomainError as exc:
            _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))
        item = ResourceState(
            id=body.id or f"rst_{uuid4().hex}",
            organization_id=principal.organization_id,
            resource_id=resource.id,
            resource_version=1,
            state_type=body.state_type,
            quantity_value=str(quantity.value),
            unit=quantity.unit,
            unit_registry_version=quantity.unit_registry_version,
            location_id=location.id,
            effective_at=body.effective_at,
            recorded_at=datetime.now(UTC),
            created_by=principal.actor_id,
            provenance=body.provenance,
            quality=body.quality,
            physical_properties=body.physical_properties,
            predecessor_state_ids=[],
        )
        resource.version = 1
        session.add(item)
        remember(session, principal, idempotency_key, digest, "ResourceState", item.id)
        emit(
            session,
            request,
            principal,
            "resource.state.created",
            "ResourceState",
            resource.id,
            1,
            {"resource_state_id": item.id, "resource_id": resource.id},
            idempotency_key,
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "State creation conflicted.")
        except SQLAlchemyError:
            session.rollback()
            _fail(
                request,
                503,
                "DATABASE_UNAVAILABLE",
                "DATABASE_FAILURE",
                "Database operation failed.",
            )
        response.headers["ETag"] = '"version-1"'
        return _envelope(request, _state_data(item))

    @app.get("/v1/resource-states/{state_id}")
    def get_resource_state(
        state_id: str,
        request: Request,
        session: Annotated[Session, Depends(db_session)],
        principal: Annotated[Principal, Depends(scope_required("resources:read"))],
    ):
        item = session.scalar(
            select(ResourceState).where(
                ResourceState.id == state_id,
                ResourceState.organization_id == principal.organization_id,
            )
        )
        if item is None:
            _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "ResourceState not found.")
        return _envelope(request, _state_data(item))

    @app.post("/v1/resource-states/{state_id}/transitions", status_code=201)
    def transition_state_route(
        state_id: str,
        body: ResourceStateTransitionCreate,
        request: Request,
        response: Response,
        session: Annotated[Session, Depends(db_session)],
        principal: Annotated[Principal, Depends(scope_required("resources:write"))],
        if_match: Annotated[str | None, Header(alias="If-Match")] = None,
        idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    ):
        if if_match is None:
            _fail(request, 400, "PRECONDITION_REQUIRED", "CONCURRENCY", "If-Match is required.")
        token = if_match.strip('"')
        if token.startswith("version-"):
            token = token.removeprefix("version-")
        try:
            expected = int(token)
        except ValueError:
            _fail(
                request,
                400,
                "INVALID_PRECONDITION",
                "CONCURRENCY",
                "If-Match must contain a positive version.",
            )
        payload = body.model_dump(mode="json")
        digest = _body_hash(
            payload | {"predecessor_state_id": state_id, "expected_version": expected}
        )
        prior = check_idempotency(
            session, principal, idempotency_key, digest, request, "StateTransition"
        )
        if prior:
            if prior.object_type != "StateTransition":
                _fail(
                    request,
                    409,
                    "IDEMPOTENCY_CONFLICT",
                    "DOMAIN_CONFLICT",
                    "Idempotency key belongs to another operation.",
                )
            item = session.get(ResourceState, prior.object_id)
            response.status_code = 200
            response.headers["ETag"] = f'"version-{item.resource_version}"'
            return _envelope(request, _state_data(item))
        predecessor = session.scalar(
            select(ResourceState).where(
                ResourceState.id == state_id,
                ResourceState.organization_id == principal.organization_id,
            )
        )
        if predecessor is None:
            _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "ResourceState not found.")
        resource = session.scalar(
            select(Resource).where(
                Resource.id == predecessor.resource_id,
                Resource.organization_id == principal.organization_id,
            )
        )
        location = session.scalar(
            select(Location).where(
                Location.id == body.location_id,
                Location.organization_id == principal.organization_id,
            )
        )
        if resource is None or location is None:
            _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Resource or location not found.")
        if expected < 1 or expected != resource.version or expected != predecessor.resource_version:
            _fail(request, 412, "STALE_VERSION", "CONCURRENCY", "ResourceState version is stale.")
        quantity = Quantity(
            body.quantity.value, body.quantity.unit, body.quantity.unit_registry_version
        )
        try:
            app.state.unit_registry.validate(quantity)
            old = DomainState(
                id=predecessor.id,
                resource_id=predecessor.resource_id,
                organization_id=predecessor.organization_id,
                version=predecessor.resource_version,
                state_type=predecessor.state_type,
                quantity=Quantity(
                    predecessor.quantity_value, predecessor.unit, predecessor.unit_registry_version
                ),
                location_id=predecessor.location_id,
                effective_at=predecessor.effective_at,
                recorded_at=predecessor.recorded_at,
                created_by=predecessor.created_by,
                provenance=predecessor.provenance,
                quality=predecessor.quality,
                physical_properties=predecessor.physical_properties,
                predecessor_state_ids=tuple(predecessor.predecessor_state_ids),
            )
            new, event = transition_state(
                old,
                expected_version=expected,
                organization_id=principal.organization_id,
                actor_id=principal.actor_id,
                kind=TransitionKind(body.kind),
                reason=body.reason,
                occurred_at=body.occurred_at,
                state_type=body.state_type,
                quantity=quantity,
                location_id=location.id,
                provenance=body.provenance,
                quality=body.quality,
                physical_properties=body.physical_properties,
            )
        except DomainError as exc:
            _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))
        result = session.execute(
            update(Resource)
            .where(
                Resource.id == resource.id,
                Resource.organization_id == principal.organization_id,
                Resource.version == expected,
            )
            .values(version=expected + 1)
        )
        if result.rowcount != 1:
            session.rollback()
            _fail(request, 412, "STALE_VERSION", "CONCURRENCY", "ResourceState version is stale.")
        successor = ResourceState(
            id=new.id,
            organization_id=new.organization_id,
            resource_id=new.resource_id,
            resource_version=new.version,
            state_type=new.state_type,
            quantity_value=str(new.quantity.value),
            unit=new.quantity.unit,
            unit_registry_version=new.quantity.unit_registry_version,
            location_id=new.location_id,
            effective_at=new.effective_at,
            recorded_at=new.recorded_at,
            created_by=new.created_by,
            provenance=dict(new.provenance),
            quality=dict(new.quality),
            physical_properties=dict(new.physical_properties),
            predecessor_state_ids=list(new.predecessor_state_ids),
        )
        session.add_all(
            [
                successor,
                StateTransition(
                    id=event.id,
                    organization_id=event.organization_id,
                    resource_id=event.resource_id,
                    predecessor_state_id=event.predecessor_state_id,
                    successor_state_id=event.successor_state_id,
                    aggregate_version=event.aggregate_version,
                    transition_kind=event.kind.value,
                    occurred_at=event.occurred_at,
                    actor_id=event.actor_id,
                    reason=event.reason,
                    provenance=dict(event.provenance),
                    idempotency_key=idempotency_key,
                    request_hash=digest,
                ),
            ]
        )
        remember(session, principal, idempotency_key, digest, "StateTransition", successor.id)
        emit(
            session,
            request,
            principal,
            "resource.state.transitioned",
            "ResourceState",
            resource.id,
            new.version,
            {
                "predecessor_state_id": predecessor.id,
                "successor_state_id": successor.id,
                "resource_version": new.version,
            },
            idempotency_key,
            predecessor.id,
        )
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "Transition conflicted.")
        except SQLAlchemyError:
            session.rollback()
            _fail(
                request,
                503,
                "DATABASE_UNAVAILABLE",
                "DATABASE_FAILURE",
                "Database operation failed.",
            )
        response.headers["ETag"] = f'"version-{successor.resource_version}"'
        return _envelope(request, _state_data(successor))

    @app.get("/v1/resources/{resource_id}/resource-states")
    def resource_state_history(
        resource_id: str,
        request: Request,
        session: Annotated[Session, Depends(db_session)],
        principal: Annotated[Principal, Depends(scope_required("resources:read"))],
    ):
        resource = session.scalar(
            select(Resource).where(
                Resource.id == resource_id,
                Resource.organization_id == principal.organization_id,
            )
        )
        if resource is None:
            _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Resource not found.")
        states = session.scalars(
            select(ResourceState)
            .where(
                ResourceState.resource_id == resource.id,
                ResourceState.organization_id == principal.organization_id,
            )
            .order_by(ResourceState.resource_version)
        ).all()
        return _envelope(request, [_state_data(item) for item in states])

    return app


app = create_app()
