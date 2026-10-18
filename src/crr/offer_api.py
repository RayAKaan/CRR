"""Tenant-isolated commercial Offer API."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from crr.domain.errors import DomainError
from crr.domain.offer import Offer as DomainOffer
from crr.domain.offer import OfferStatus
from crr.domain.quantity import Quantity
from crr.models import Actor, IdempotencyRecord, OutboxEvent
from crr.offer_model import Offer
from crr.offer_schemas import OfferInput, OfferStatusInput
from crr.opportunity_model import Opportunity

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


def _data(item: Offer) -> dict[str, Any]:
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "opportunity_id": item.opportunity_id,
        "opportunity_version": item.opportunity_version,
        "proposer_actor_id": item.proposer_actor_id,
        "recipient_actor_id": item.recipient_actor_id,
        "quantity": {
            "value": str(item.quantity_value),
            "unit": item.quantity_unit,
            "unit_registry_version": item.unit_registry_version,
        },
        "price": str(item.price),
        "currency": item.currency,
        "delivery_terms": item.delivery_terms,
        "timing_terms": item.timing_terms,
        "route_assumptions": item.route_assumptions,
        "conditions": item.conditions,
        "valid_from": item.valid_from.isoformat(),
        "valid_until": item.valid_until.isoformat(),
        "status": item.status,
        "version": item.version,
        "created_by": item.created_by,
        "provenance": item.provenance,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
    }


def _find(session: Session, offer_id: str, organization_id: str):
    return session.scalar(
        select(Offer).where(
            Offer.id == offer_id,
            Offer.organization_id == organization_id,
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
    if prior and (prior.request_hash != digest or prior.object_type != "Offer"):
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
    object_id: str,
):
    session.add(
        IdempotencyRecord(
            organization_id=organization_id,
            idempotency_key=key,
            request_hash=digest,
            object_type="Offer",
            object_id=object_id,
            created_at=datetime.now(UTC),
        )
    )


def _event(
    session: Session,
    request: Request,
    organization_id: str,
    actor_id: str,
    item: Offer,
    key: str,
    event_type: str,
):
    session.add(
        OutboxEvent(
            id=f"evt_{uuid4().hex}",
            event_type=event_type,
            event_version=1,
            aggregate_type="Offer",
            aggregate_id=item.id,
            aggregate_version=item.version,
            organization_id=organization_id,
            actor_id=actor_id,
            occurred_at=datetime.now(UTC),
            published_at=None,
            correlation_id=request.state.request_id,
            causation_id=None,
            idempotency_key=key,
            payload={"offer_id": item.id, "version": item.version, "status": item.status},
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
            "Idempotent Offer result is unavailable.",
        )
    response.status_code = 200
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


def _validate_opportunity(
    session: Session,
    request: Request,
    principal: Any,
    body: OfferInput,
) -> Opportunity:
    opportunity = session.scalar(
        select(Opportunity).where(
            Opportunity.id == body.opportunity_id,
            Opportunity.organization_id == principal.organization_id,
        )
    )
    if opportunity is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Opportunity not found.")
    if opportunity.version != body.opportunity_version:
        _fail(
            request,
            409,
            "OPPORTUNITY_STALE",
            "DOMAIN_CONFLICT",
            "Offer source Opportunity version is stale.",
        )
    if opportunity.status != "OPEN":
        _fail(
            request,
            409,
            "OPPORTUNITY_NOT_ELIGIBLE",
            "DOMAIN_CONFLICT",
            "Only open Opportunities can receive Offers.",
        )
    now = datetime.now(UTC)
    if now >= opportunity.valid_until:
        _fail(
            request,
            409,
            "OPPORTUNITY_EXPIRED",
            "DOMAIN_CONFLICT",
            "Opportunity has expired.",
        )
    if body.valid_from < opportunity.valid_from or body.valid_until > opportunity.valid_until:
        _fail(
            request,
            422,
            "OFFER_WINDOW_INVALID",
            "VALIDATION_FAILURE",
            "Offer validity must be contained within the Opportunity validity window.",
        )
    if body.quantity_value > opportunity.quantity_value:
        _fail(
            request,
            422,
            "OFFER_QUANTITY_EXCEEDS_OPPORTUNITY",
            "VALIDATION_FAILURE",
            "Offer quantity cannot exceed the Opportunity quantity.",
        )
    if (
        body.quantity_unit != opportunity.quantity_unit
        or body.unit_registry_version != opportunity.unit_registry_version
    ):
        _fail(
            request,
            422,
            "OFFER_UNIT_MISMATCH",
            "VALIDATION_FAILURE",
            "Offer quantity unit must match the Opportunity snapshot.",
        )
    if body.currency != opportunity.currency:
        _fail(
            request,
            422,
            "OFFER_CURRENCY_MISMATCH",
            "VALIDATION_FAILURE",
            "Offer currency must match the Opportunity monetary context.",
        )
    return opportunity


def _validate_participants(
    session: Session,
    request: Request,
    principal: Any,
    body: OfferInput,
) -> None:
    actors = session.scalars(
        select(Actor).where(
            Actor.id.in_([body.proposer_actor_id, body.recipient_actor_id]),
            Actor.organization_id == principal.organization_id,
        )
    ).all()
    by_id = {actor.id: actor for actor in actors}
    if len(by_id) != 2:
        _fail(
            request,
            404,
            "NOT_FOUND",
            "NOT_FOUND",
            "Offer participant not found in the authenticated organization.",
        )
    if not by_id[body.proposer_actor_id].active or not by_id[body.recipient_actor_id].active:
        _fail(
            request,
            409,
            "PARTICIPANT_INACTIVE",
            "DOMAIN_CONFLICT",
            "Offer participants must be active actors.",
        )


def _build(
    body: OfferInput,
    principal: Any,
    opportunity: Opportunity,
    now: datetime,
) -> DomainOffer:
    return DomainOffer(
        id=body.id or f"off_{uuid4().hex}",
        organization_id=principal.organization_id,
        opportunity_id=opportunity.id,
        opportunity_version=opportunity.version,
        proposer_actor_id=body.proposer_actor_id,
        recipient_actor_id=body.recipient_actor_id,
        quantity=Quantity(body.quantity_value, body.quantity_unit, body.unit_registry_version),
        price=body.price,
        currency=body.currency,
        delivery_terms=body.delivery_terms,
        timing_terms=body.timing_terms,
        route_assumptions=body.route_assumptions,
        conditions=body.conditions,
        valid_from=body.valid_from,
        valid_until=body.valid_until,
        status=OfferStatus(body.status),
        version=1,
        created_by=principal.actor_id,
        provenance=body.provenance,
        created_at=now,
        updated_at=now,
    )


def _persist(domain_item: DomainOffer) -> Offer:
    return Offer(
        id=domain_item.id,
        organization_id=domain_item.organization_id,
        opportunity_id=domain_item.opportunity_id,
        opportunity_version=domain_item.opportunity_version,
        proposer_actor_id=domain_item.proposer_actor_id,
        recipient_actor_id=domain_item.recipient_actor_id,
        quantity_value=domain_item.quantity.value,
        quantity_unit=domain_item.quantity.unit,
        unit_registry_version=domain_item.quantity.unit_registry_version,
        price=domain_item.price,
        currency=domain_item.currency,
        delivery_terms=domain_item.delivery_terms,
        timing_terms=domain_item.timing_terms,
        route_assumptions=domain_item.route_assumptions,
        conditions=domain_item.conditions,
        valid_from=domain_item.valid_from,
        valid_until=domain_item.valid_until,
        status=domain_item.status.value,
        version=domain_item.version,
        created_by=domain_item.created_by,
        provenance=domain_item.provenance,
        created_at=domain_item.created_at,
        updated_at=domain_item.updated_at,
    )


@router.post("/v1/offers", status_code=201)
def create_offer(
    body: OfferInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("offers:write"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(body.model_dump(mode="json"))
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    _check_reuse(prior, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    opportunity = _validate_opportunity(session, request, principal, body)
    _validate_participants(session, request, principal, body)
    if body.proposer_actor_id != principal.actor_id:
        _fail(
            request,
            403,
            "ACTOR_NOT_AUTHORIZED",
            "AUTHORIZATION_FAILURE",
            "Offer creation must be attributed to the authenticated proposer actor.",
        )
    registry = request.app.state.unit_registry
    try:
        registry.validate(
            Quantity(
                body.quantity_value,
                body.quantity_unit,
                body.unit_registry_version,
            )
        )
    except DomainError as exc:
        _fail(request, 422, "UNIT_VALIDATION_FAILED", "VALIDATION_FAILURE", str(exc))
    now = datetime.now(UTC)
    try:
        item = _persist(_build(body, principal, opportunity, now))
    except DomainError as exc:
        _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))
    session.add(item)
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _event(
        session,
        request,
        principal.organization_id,
        principal.actor_id,
        item,
        idempotency_key,
        "offer.created",
    )
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
        _check_reuse(prior, digest, request)
        if prior:
            return _replay(session, response, request, prior, principal.organization_id)
        raise
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


@router.get("/v1/offers/{offer_id}")
def get_offer(
    offer_id: str,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("offers:read"))],
):
    item = _find(session, offer_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Offer not found.")
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


@router.get("/v1/offers")
def list_offers(
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("offers:read"))],
):
    items = session.scalars(
        select(Offer)
        .where(Offer.organization_id == principal.organization_id)
        .order_by(Offer.created_at.desc(), Offer.id.desc())
    ).all()
    return _collection(request, [_data(item) for item in items], None, False, len(items))


@router.patch("/v1/offers/{offer_id}")
def transition_offer(
    offer_id: str,
    body: OfferStatusInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("offers:write"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(body.model_dump(mode="json") | {"offer_id": offer_id, "if_match": if_match})
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    _check_reuse(prior, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    if not if_match:
        _fail(
            request,
            428,
            "IF_MATCH_REQUIRED",
            "CONCURRENCY_FAILURE",
            "If-Match is required.",
        )
    item = _find(session, offer_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Offer not found.")
    expected = f'"version-{item.version}"'
    if if_match != expected:
        _fail(
            request,
            409,
            "STALE_VERSION",
            "CONCURRENCY_FAILURE",
            "Offer version is stale.",
        )
    try:
        domain = DomainOffer(
            id=item.id,
            organization_id=item.organization_id,
            opportunity_id=item.opportunity_id,
            opportunity_version=item.opportunity_version,
            proposer_actor_id=item.proposer_actor_id,
            recipient_actor_id=item.recipient_actor_id,
            quantity=Quantity(
                item.quantity_value,
                item.quantity_unit,
                item.unit_registry_version,
            ),
            price=item.price,
            currency=item.currency,
            delivery_terms=item.delivery_terms,
            timing_terms=item.timing_terms,
            route_assumptions=item.route_assumptions,
            conditions=item.conditions,
            valid_from=item.valid_from,
            valid_until=item.valid_until,
            status=OfferStatus(item.status),
            version=item.version,
            created_by=item.created_by,
            provenance=item.provenance,
            created_at=item.created_at,
            updated_at=item.updated_at,
        ).transition(OfferStatus(body.status))
    except DomainError as exc:
        _fail(request, 409, exc.code, "DOMAIN_CONFLICT", str(exc))
    item.status = domain.status.value
    item.version = domain.version
    item.updated_at = domain.updated_at
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _event(
        session,
        request,
        principal.organization_id,
        principal.actor_id,
        item,
        idempotency_key,
        "offer.updated",
    )
    session.commit()
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))
