"""Tenant-isolated commercial Opportunity API."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from crr.demand_model import Demand
from crr.domain.errors import DomainError
from crr.domain.opportunity import Opportunity as DomainOpportunity
from crr.domain.opportunity import OpportunityStatus
from crr.domain.quantity import Quantity
from crr.domain.routing import Rejection, RouteCandidate, RouteLeg, RouteStatus
from crr.economic_model import EconomicModel
from crr.models import IdempotencyRecord, OutboxEvent, ResourceState
from crr.opportunity_model import Opportunity
from crr.opportunity_schemas import OpportunityInput, OpportunityStatusInput

router = APIRouter()


def _api():
    from crr import api
    return api


def _fail(request: Request, status: int, code: str, category: str, message: str):
    _api()._fail(request, status, code, category, message)


def _envelope(request: Request, data: Any):
    return _api()._envelope(request, data)


def _collection(request: Request, data: list[dict[str, Any]], cursor: str | None, has_more: bool, limit: int):
    return _api()._collection(request, data, cursor, has_more, limit)


def _session_dependency():
    return _api().db_session


def _scope_dependency(scope: str):
    return _api().scope_required(scope)


def _body_hash(payload: dict[str, Any]) -> str:
    return _api()._body_hash(payload)


def _candidate(body: OpportunityInput) -> RouteCandidate:
    snapshot = body.route_candidate
    return RouteCandidate(
        id=snapshot.id,
        organization_id=snapshot.organization_id,
        source_resource_state_id=snapshot.source_resource_state_id,
        target_demand_id=snapshot.target_demand_id,
        legs=tuple(
            RouteLeg(leg.kind, leg.object_id, leg.input_state_type, leg.output_state_type)
            for leg in snapshot.legs
        ),
        status=RouteStatus.FEASIBLE,
        rejections=tuple(
            Rejection(item.code, item.object_id, item.message) for item in snapshot.rejections
        ),
        source_version=snapshot.source_version,
        target_version=snapshot.target_version,
        evaluated_at=snapshot.evaluated_at,
        provenance=snapshot.provenance,
    )


def _fingerprint(candidate: RouteCandidate) -> str:
    from crr.domain.optimization import fingerprint_candidates
    return fingerprint_candidates((candidate,))


def _data(item: Opportunity) -> dict[str, Any]:
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "route_candidate_id": item.route_candidate_id,
        "candidate_set_fingerprint": item.candidate_set_fingerprint,
        "source_resource_state_id": item.source_resource_state_id,
        "source_resource_state_version": item.source_resource_state_version,
        "target_demand_id": item.target_demand_id,
        "target_demand_version": item.target_demand_version,
        "route_provenance": item.route_provenance,
        "advisory_provenance": item.advisory_provenance,
        "economic_model_id": item.economic_model_id,
        "economic_model_version": item.economic_model_version,
        "commercial_perspective": item.commercial_perspective,
        "currency": item.currency,
        "quantity": {
            "value": str(item.quantity_value),
            "unit": item.quantity_unit,
            "unit_registry_version": item.unit_registry_version,
        },
        "valid_from": item.valid_from.isoformat(),
        "valid_until": item.valid_until.isoformat(),
        "status": item.status,
        "version": item.version,
        "created_by": item.created_by,
        "provenance": item.provenance,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _find(session: Session, opportunity_id: str, organization_id: str):
    return session.scalar(
        select(Opportunity).where(
            Opportunity.id == opportunity_id,
            Opportunity.organization_id == organization_id,
        )
    )


def _idempotency(session: Session, organization_id: str, key: str | None, digest: str, request: Request):
    if not key or not key.strip() or len(key) > 255:
        _fail(request, 400, "IDEMPOTENCY_KEY_REQUIRED", "VALIDATION_FAILURE", "A valid Idempotency-Key is required.")
    return session.scalar(
        select(IdempotencyRecord).where(
            IdempotencyRecord.organization_id == organization_id,
            IdempotencyRecord.idempotency_key == key,
        )
    )


def _check_reuse(prior, digest: str, request: Request):
    if prior and (prior.request_hash != digest or prior.object_type != "Opportunity"):
        _fail(request, 409, "IDEMPOTENCY_CONFLICT", "DOMAIN_CONFLICT", "Idempotency key was reused with a different request.")


def _remember(session: Session, organization_id: str, key: str, digest: str, object_id: str):
    session.add(
        IdempotencyRecord(
            organization_id=organization_id,
            idempotency_key=key,
            request_hash=digest,
            object_type="Opportunity",
            object_id=object_id,
            created_at=datetime.now(UTC),
        )
    )


def _event(session: Session, request: Request, organization_id: str, actor_id: str, item: Opportunity, key: str, event_type: str):
    session.add(
        OutboxEvent(
            id=f"evt_{uuid4().hex}",
            event_type=event_type,
            event_version=1,
            aggregate_type="Opportunity",
            aggregate_id=item.id,
            aggregate_version=item.version,
            organization_id=organization_id,
            actor_id=actor_id,
            occurred_at=datetime.now(UTC),
            published_at=None,
            correlation_id=request.state.request_id,
            causation_id=None,
            idempotency_key=key,
            payload={"opportunity_id": item.id, "version": item.version, "status": item.status},
            provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
            schema_version="0.1",
        )
    )


def _replay(session: Session, response: Response, request: Request, prior, organization_id: str):
    item = _find(session, prior.object_id, organization_id)
    if item is None:
        _fail(request, 409, "IDEMPOTENCY_STATE_MISSING", "DOMAIN_CONFLICT", "Idempotent Opportunity result is unavailable.")
    response.status_code = 200
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


def _validate_source(session: Session, request: Request, principal: Any, body: OpportunityInput):
    candidate = _candidate(body)
    if candidate.organization_id != principal.organization_id:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Route candidate not found.")
    if candidate.rejections or candidate.status is not RouteStatus.FEASIBLE:
        _fail(request, 409, "ROUTE_NOT_FEASIBLE", "DOMAIN_CONFLICT", "Only feasible route candidates may become Opportunities.")
    source = session.scalar(select(ResourceState).where(ResourceState.id == body.source_resource_state_id, ResourceState.organization_id == principal.organization_id))
    demand = session.scalar(select(Demand).where(Demand.id == body.target_demand_id, Demand.organization_id == principal.organization_id))
    if source is None or demand is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Opportunity source object not found.")
    if source.resource_version != candidate.source_version or demand.version != candidate.target_version:
        _fail(request, 409, "ROUTE_STALE", "DOMAIN_CONFLICT", "Route source versions no longer match canonical state.")
    if demand.status != "ACTIVE":
        _fail(request, 409, "DEMAND_NOT_ELIGIBLE", "DOMAIN_CONFLICT", "Target Demand is not active.")
    if body.valid_until > demand.timing_end:
        _fail(request, 422, "OPPORTUNITY_WINDOW_INVALID", "VALIDATION_FAILURE", "Opportunity validity cannot exceed the Demand timing window.")
    economic_model = None
    if body.economic_model_id is not None:
        economic_model = session.scalar(select(EconomicModel).where(EconomicModel.id == body.economic_model_id, EconomicModel.organization_id == principal.organization_id, EconomicModel.version == body.economic_model_version))
        if economic_model is None:
            _fail(request, 409, "ECONOMIC_MODEL_STALE", "DOMAIN_CONFLICT", "Referenced EconomicModel version is unavailable.")
        if economic_model.currency != body.currency:
            _fail(request, 422, "CURRENCY_MISMATCH", "VALIDATION_FAILURE", "Opportunity currency does not match the EconomicModel.")
        if economic_model.status != "ACTIVE":
            _fail(request, 409, "ECONOMIC_MODEL_INACTIVE", "DOMAIN_CONFLICT", "Referenced EconomicModel is not active.")
    quantity = Quantity(body.quantity_value, body.quantity_unit, body.unit_registry_version)
    try:
        request.app.state.unit_registry.validate(quantity)
    except DomainError as exc:
        _fail(request, 422, "UNIT_VALIDATION_FAILED", "VALIDATION_FAILURE", str(exc))
    if body.quantity_value > demand.quantity_max_value or body.quantity_value > source.quantity_value:
        _fail(request, 422, "QUANTITY_INSUFFICIENT_OR_EXCESSIVE", "VALIDATION_FAILURE", "Opportunity quantity exceeds a canonical source or demand bound.")
    if body.valid_until <= datetime.now(UTC):
        _fail(request, 422, "OPPORTUNITY_EXPIRED", "VALIDATION_FAILURE", "Opportunity validity window is already expired.")
    return source, demand, economic_model, candidate


def _build_domain_item(body: OpportunityInput, principal: Any, source: ResourceState, demand: Demand, economic_model: EconomicModel | None, candidate: RouteCandidate, now: datetime) -> DomainOpportunity:
    return DomainOpportunity(
        id=body.id or f"opp_{uuid4().hex}", organization_id=principal.organization_id,
        route_candidate_id=candidate.id, candidate_set_fingerprint=body.candidate_set_fingerprint,
        source_resource_state_id=source.id, source_resource_state_version=source.resource_version,
        target_demand_id=demand.id, target_demand_version=demand.version,
        route_provenance={"candidate": body.route_candidate.model_dump(mode="json"), "candidate_set_fingerprint": body.candidate_set_fingerprint},
        advisory_provenance=body.advisory_provenance,
        economic_model_id=economic_model.id if economic_model is not None else None,
        economic_model_version=economic_model.version if economic_model is not None else None,
        commercial_perspective=body.commercial_perspective, currency=body.currency,
        quantity=Quantity(body.quantity_value, body.quantity_unit, body.unit_registry_version),
        valid_from=body.valid_from, valid_until=body.valid_until, status=OpportunityStatus(body.status),
        version=1, created_by=principal.actor_id, provenance=body.provenance, created_at=now, updated_at=now,
    )


def _persist_item(domain_item: DomainOpportunity) -> Opportunity:
    return Opportunity(
        id=domain_item.id, organization_id=domain_item.organization_id, route_candidate_id=domain_item.route_candidate_id,
        candidate_set_fingerprint=domain_item.candidate_set_fingerprint, source_resource_state_id=domain_item.source_resource_state_id,
        source_resource_state_version=domain_item.source_resource_state_version, target_demand_id=domain_item.target_demand_id,
        target_demand_version=domain_item.target_demand_version, route_provenance=domain_item.route_provenance,
        advisory_provenance=domain_item.advisory_provenance, economic_model_id=domain_item.economic_model_id,
        economic_model_version=domain_item.economic_model_version, commercial_perspective=domain_item.commercial_perspective,
        currency=domain_item.currency, quantity_value=domain_item.quantity.value, quantity_unit=domain_item.quantity.unit,
        unit_registry_version=domain_item.quantity.unit_registry_version, valid_from=domain_item.valid_from,
        valid_until=domain_item.valid_until, status=domain_item.status.value, version=domain_item.version,
        created_by=domain_item.created_by, provenance=domain_item.provenance, created_at=domain_item.created_at,
        updated_at=domain_item.updated_at,
    )


@router.post("/v1/opportunities", status_code=201)
def create_opportunity(body: OpportunityInput, request: Request, response: Response, session: Annotated[Session, Depends(_session_dependency())], principal: Annotated[Any, Depends(_scope_dependency("opportunities:write"))], idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None):
    digest = _body_hash(body.model_dump(mode="json"))
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    _check_reuse(prior, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    source, demand, economic_model, candidate = _validate_source(session, request, principal, body)
    if _fingerprint(candidate) != body.candidate_set_fingerprint:
        _fail(request, 409, "CANDIDATE_SET_TAMPERED", "DOMAIN_CONFLICT", "Route provenance does not match its declared candidate-set fingerprint.")
    now = datetime.now(UTC)
    try:
        domain_item = _build_domain_item(body, principal, source, demand, economic_model, candidate, now)
    except DomainError as exc:
        _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))
    item = _persist_item(domain_item)
    session.add(item)
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _event(session, request, principal.organization_id, principal.actor_id, item, idempotency_key, "opportunity.created")
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
        _check_reuse(prior, digest, request)
        if prior:
            return _replay(session, response, request, prior, principal.organization_id)
        _fail(request, 409, "CONFLICT", "DOMAIN_CONFLICT", "Opportunity creation conflicted.")
    except SQLAlchemyError:
        session.rollback()
        _fail(request, 503, "DATABASE_UNAVAILABLE", "DATABASE_FAILURE", "Database operation failed.")
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


@router.get("/v1/opportunities")
def list_opportunities(request: Request, session: Annotated[Session, Depends(_session_dependency())], principal: Annotated[Any, Depends(_scope_dependency("opportunities:read"))], limit: int = Query(default=50, ge=1, le=100), cursor: str | None = None, status: str | None = None):
    statement = select(Opportunity).where(Opportunity.organization_id == principal.organization_id)
    if cursor:
        statement = statement.where(Opportunity.id > cursor)
    if status is not None:
        if status not in {item.value for item in OpportunityStatus}:
            _fail(request, 422, "INVALID_STATUS", "VALIDATION_FAILURE", "Unknown Opportunity status.")
        statement = statement.where(Opportunity.status == status)
    rows = session.scalars(statement.order_by(Opportunity.id).limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].id if has_more and rows else None
    return _collection(request, [_data(row) for row in rows], next_cursor, has_more, limit)


@router.get("/v1/opportunities/{opportunity_id}")
def get_opportunity(opportunity_id: str, request: Request, session: Annotated[Session, Depends(_session_dependency())], principal: Annotated[Any, Depends(_scope_dependency("opportunities:read"))]):
    item = _find(session, opportunity_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Opportunity not found.")
    return _envelope(request, _data(item))


@router.patch("/v1/opportunities/{opportunity_id}")
def transition_opportunity(opportunity_id: str, body: OpportunityStatusInput, request: Request, response: Response, session: Annotated[Session, Depends(_session_dependency())], principal: Annotated[Any, Depends(_scope_dependency("opportunities:write"))], idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None, if_match: Annotated[str | None, Header(alias="If-Match")] = None):
    item = _find(session, opportunity_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Opportunity not found.")
    if if_match != f'"version-{item.version}"':
        _fail(request, 409, "STALE_VERSION", "CONCURRENCY_FAILURE", "If-Match does not match current version.")
    digest = _body_hash(
        body.model_dump(mode="json") | {"opportunity_id": opportunity_id, "if_match": if_match}
    )
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    _check_reuse(prior, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    try:
        domain_item = DomainOpportunity(
            id=item.id, organization_id=item.organization_id, route_candidate_id=item.route_candidate_id,
            candidate_set_fingerprint=item.candidate_set_fingerprint, source_resource_state_id=item.source_resource_state_id,
            source_resource_state_version=item.source_resource_state_version, target_demand_id=item.target_demand_id,
            target_demand_version=item.target_demand_version, route_provenance=item.route_provenance,
            advisory_provenance=item.advisory_provenance, economic_model_id=item.economic_model_id,
            economic_model_version=item.economic_model_version, commercial_perspective=item.commercial_perspective,
            currency=item.currency, quantity=Quantity(item.quantity_value, item.quantity_unit, item.unit_registry_version),
            valid_from=item.valid_from, valid_until=item.valid_until, status=OpportunityStatus(item.status), version=item.version,
            created_by=item.created_by, provenance=item.provenance, created_at=item.created_at, updated_at=item.updated_at,
        )
        transitioned = domain_item.transition(OpportunityStatus(body.status))
    except DomainError as exc:
        _fail(request, 409, exc.code, "DOMAIN_CONFLICT", str(exc))
    item.status = transitioned.status.value
    item.version = transitioned.version
    item.updated_at = transitioned.updated_at
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _event(session, request, principal.organization_id, principal.actor_id, item, idempotency_key, "opportunity.updated")
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        _fail(request, 503, "DATABASE_UNAVAILABLE", "DATABASE_FAILURE", "Database operation failed.")
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))
