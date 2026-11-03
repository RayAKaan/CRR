"""Tenant-isolated Agreement API over accepted Offers."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from crr.agreement_model import Agreement
from crr.agreement_schemas import AgreementCreate, AgreementLifecycleInput
from crr.domain.agreement import Agreement as DomainAgreement
from crr.domain.agreement import AgreementStatus
from crr.domain.errors import DomainError
from crr.models import IdempotencyRecord, OutboxEvent
from crr.offer_model import Offer

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


def _data(item: Agreement) -> dict[str, Any]:
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "offer_id": item.offer_id,
        "offer_version": item.offer_version,
        "proposer_actor_id": item.proposer_actor_id,
        "recipient_actor_id": item.recipient_actor_id,
        "accepted_by": item.accepted_by,
        "accepted_at": item.accepted_at.isoformat(),
        "terms": json.loads(item.terms_snapshot),
        "status": item.status,
        "version": item.version,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
        "provenance": json.loads(item.provenance),
    }


def _find(session: Session, agreement_id: str, organization_id: str):
    return session.scalar(
        select(Agreement).where(
            Agreement.id == agreement_id,
            Agreement.organization_id == organization_id,
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
    if prior and (prior.request_hash != digest or prior.object_type != "Agreement"):
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
    agreement_id: str,
) -> None:
    session.add(
        IdempotencyRecord(
            organization_id=organization_id,
            idempotency_key=key,
            request_hash=digest,
            object_type="Agreement",
            object_id=agreement_id,
            created_at=datetime.now(UTC),
        )
    )


def _emit(
    session: Session,
    request: Request,
    principal: Any,
    item: Agreement,
    key: str,
    event_type: str,
) -> None:
    session.add(
        OutboxEvent(
            id=f"evt_{uuid4().hex}",
            event_type=event_type,
            event_version=1,
            aggregate_type="Agreement",
            aggregate_id=item.id,
            aggregate_version=item.version,
            organization_id=principal.organization_id,
            actor_id=principal.actor_id,
            occurred_at=datetime.now(UTC),
            published_at=None,
            correlation_id=request.state.request_id,
            causation_id=item.offer_id,
            idempotency_key=key,
            payload={
                "agreement_id": item.id,
                "offer_id": item.offer_id,
                "version": item.version,
                "status": item.status,
            },
            provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
            schema_version="0.1",
        )
    )


def _replay(session: Session, response: Response, request: Request, prior, org_id: str):
    item = _find(session, prior.object_id, org_id)
    if item is None:
        _fail(
            request,
            409,
            "IDEMPOTENCY_STATE_MISSING",
            "DOMAIN_CONFLICT",
            "Idempotent Agreement result is unavailable.",
        )
    response.status_code = 200
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


@router.post("/v1/agreements", status_code=201)
def create_agreement(
    body: AgreementCreate,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("agreements:write"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(body.model_dump(mode="json"))
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)
    offer = session.scalar(
        select(Offer).where(
            Offer.id == body.offer_id,
            Offer.organization_id == principal.organization_id,
        )
    )
    if offer is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Accepted Offer not found.")
    if offer.status != "ACCEPTED":
        _fail(
            request,
            409,
            "OFFER_NOT_ACCEPTED",
            "DOMAIN_CONFLICT",
            "Agreement creation requires an accepted Offer.",
        )
    if principal.actor_id != offer.recipient_actor_id:
        _fail(
            request,
            403,
            "ACCEPTANCE_ACTOR_MISMATCH",
            "AUTHORIZATION_FAILURE",
            "Only the Offer recipient may create its Agreement.",
        )
    acceptance = session.scalar(
        select(OutboxEvent).where(
            OutboxEvent.aggregate_type == "Offer",
            OutboxEvent.aggregate_id == offer.id,
            OutboxEvent.aggregate_version == offer.version,
            OutboxEvent.event_type == "offer.updated",
        )
    )
    if acceptance is None or acceptance.actor_id != offer.recipient_actor_id:
        _fail(
            request,
            409,
            "ACCEPTANCE_NOT_ATTRIBUTED",
            "DOMAIN_CONFLICT",
            "The accepted Offer has no matching recipient-attributed acceptance event.",
        )
    try:
        domain = DomainAgreement.from_accepted_offer(
            _domain_offer(offer),
            agreement_id=f"agr_{uuid4().hex}",
            accepted_by=acceptance.actor_id,
            accepted_at=acceptance.occurred_at,
            provenance=json.dumps(
                {"source_type": "OFFER_ACCEPTANCE", "event_id": acceptance.id},
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
    except DomainError as exc:
        _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))
    item = Agreement(
        id=domain.id,
        organization_id=domain.organization_id,
        offer_id=domain.offer_id,
        offer_version=domain.offer_version,
        proposer_actor_id=domain.proposer_actor_id,
        recipient_actor_id=domain.recipient_actor_id,
        accepted_by=domain.accepted_by,
        accepted_at=domain.accepted_at,
        terms_snapshot=domain.terms_snapshot,
        status=domain.status.value,
        version=domain.version,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
        provenance=domain.provenance,
    )
    session.add(item)
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _emit(session, request, principal, item, idempotency_key, "agreement.created")
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
        if prior:
            return _replay(session, response, request, prior, principal.organization_id)
        _fail(
            request,
            409,
            "AGREEMENT_ALREADY_EXISTS",
            "DOMAIN_CONFLICT",
            "An Agreement already exists for this Offer.",
        )
    except SQLAlchemyError:
        session.rollback()
        _fail(
            request,
            503,
            "DATABASE_UNAVAILABLE",
            "DATABASE_FAILURE",
            "Agreement could not be persisted.",
        )
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


def _domain_offer(item: Offer):
    from crr.domain.offer import Offer as DomainOffer
    from crr.domain.offer import OfferStatus
    from crr.domain.quantity import Quantity

    return DomainOffer(
        id=item.id,
        organization_id=item.organization_id,
        opportunity_id=item.opportunity_id,
        opportunity_version=item.opportunity_version,
        proposer_actor_id=item.proposer_actor_id,
        recipient_actor_id=item.recipient_actor_id,
        quantity=Quantity(item.quantity_value, item.quantity_unit, item.unit_registry_version),
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
    )


@router.get("/v1/agreements/{agreement_id}")
def get_agreement(
    agreement_id: str,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("agreements:read"))],
):
    item = _find(session, agreement_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Agreement not found.")
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


@router.get("/v1/agreements")
def list_agreements(
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("agreements:read"))],
):
    items = session.scalars(
        select(Agreement)
        .where(Agreement.organization_id == principal.organization_id)
        .order_by(Agreement.created_at.desc(), Agreement.id.desc())
    ).all()
    return _collection(request, [_data(item) for item in items], None, False, len(items))


@router.patch("/v1/agreements/{agreement_id}")
def transition_agreement(
    agreement_id: str,
    body: AgreementLifecycleInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("agreements:write"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(
        body.model_dump(mode="json") | {"agreement_id": agreement_id, "if_match": if_match}
    )
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
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
    item = _find(session, agreement_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Agreement not found.")
    if if_match != f'"version-{item.version}"':
        _fail(
            request,
            409,
            "STALE_VERSION",
            "CONCURRENCY_FAILURE",
            "Agreement version is stale.",
        )
    domain = DomainAgreement(
        id=item.id,
        organization_id=item.organization_id,
        offer_id=item.offer_id,
        offer_version=item.offer_version,
        proposer_actor_id=item.proposer_actor_id,
        recipient_actor_id=item.recipient_actor_id,
        accepted_by=item.accepted_by,
        accepted_at=item.accepted_at,
        terms_snapshot=item.terms_snapshot,
        status=AgreementStatus(item.status),
        version=item.version,
        created_at=item.created_at,
        updated_at=item.updated_at,
        provenance=item.provenance,
    )
    try:
        if body.status == "EXPIRED":
            if (
                "agreements:expire" not in principal.scopes
                and "admin:*" not in principal.scopes
            ):
                _fail(
                    request,
                    403,
                    "EXPIRY_SCOPE_REQUIRED",
                    "AUTHORIZATION_FAILURE",
                    "Agreement expiry requires the agreements:expire scope.",
                )
            changed = domain.expire(at=datetime.now(UTC))
        elif body.status == "CANCELLED":
            changed = domain.cancel(actor_id=principal.actor_id, at=datetime.now(UTC))
        else:
            changed = domain.terminate(actor_id=principal.actor_id, at=datetime.now(UTC))
    except DomainError as exc:
        _fail(request, 409, exc.code, "DOMAIN_CONFLICT", str(exc))
    item.status = changed.status.value
    item.version = changed.version
    item.updated_at = changed.updated_at
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _emit(session, request, principal, item, idempotency_key, "agreement.updated")
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        _fail(
            request,
            503,
            "DATABASE_UNAVAILABLE",
            "DATABASE_FAILURE",
            "Agreement update failed.",
        )
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))
