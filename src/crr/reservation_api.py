"""Tenant-isolated Reservation API with serialized exact allocation."""

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
from crr.domain.errors import DomainError
from crr.domain.quantity import Quantity, exact_decimal
from crr.domain.reservation import (
    Reservation as DomainReservation,
    ReservationStatus,
    active_reserved_quantity,
    validate_reservation_capacity,
)
from crr.models import IdempotencyRecord, OutboxEvent, Resource, ResourceState
from crr.opportunity_model import Opportunity
from crr.offer_model import Offer
from crr.reservation_model import Reservation as ReservationRecord
from crr.reservation_schemas import ReservationCreate, ReservationLifecycleInput

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


def _data(item: ReservationRecord) -> dict[str, Any]:
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "agreement_id": item.agreement_id,
        "resource_id": item.resource_id,
        "resource_state_id": item.resource_state_id,
        "resource_state_version": item.resource_version,
        "quantity": {
            "value": str(item.quantity_value),
            "unit": item.quantity_unit,
            "unit_registry_version": item.unit_registry_version,
        },
        "status": item.status,
        "expires_at": item.expires_at.isoformat(),
        "version": item.version,
        "created_by": item.created_by,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
        "provenance": item.provenance,
    }


def _find(session: Session, reservation_id: str, organization_id: str):
    return session.scalar(
        select(ReservationRecord).where(
            ReservationRecord.id == reservation_id,
            ReservationRecord.organization_id == organization_id,
        )
    )


def _domain(item: ReservationRecord) -> DomainReservation:
    return DomainReservation(
        id=item.id,
        organization_id=item.organization_id,
        agreement_id=item.agreement_id,
        resource_id=item.resource_id,
        resource_state_id=item.resource_state_id,
        resource_version=item.resource_version,
        quantity=Quantity(
            item.quantity_value,
            item.quantity_unit,
            item.unit_registry_version,
        ),
        status=ReservationStatus(item.status),
        expires_at=item.expires_at,
        version=item.version,
        created_by=item.created_by,
        created_at=item.created_at,
        updated_at=item.updated_at,
        provenance=item.provenance,
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
    if prior and (prior.request_hash != digest or prior.object_type != "Reservation"):
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
    reservation_id: str,
) -> None:
    session.add(
        IdempotencyRecord(
            organization_id=organization_id,
            idempotency_key=key,
            request_hash=digest,
            object_type="Reservation",
            object_id=reservation_id,
            created_at=datetime.now(UTC),
        )
    )


def _emit(
    session: Session,
    request: Request,
    principal: Any,
    item: ReservationRecord,
    key: str,
    event_type: str,
) -> None:
    session.add(
        OutboxEvent(
            id=f"evt_{uuid4().hex}",
            event_type=event_type,
            event_version=1,
            aggregate_type="Reservation",
            aggregate_id=item.id,
            aggregate_version=item.version,
            organization_id=principal.organization_id,
            actor_id=principal.actor_id,
            occurred_at=datetime.now(UTC),
            published_at=None,
            correlation_id=request.state.request_id,
            causation_id=item.agreement_id,
            idempotency_key=key,
            payload={
                "reservation_id": item.id,
                "agreement_id": item.agreement_id,
                "resource_state_id": item.resource_state_id,
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
            "Idempotent Reservation result is unavailable.",
        )
    response.status_code = 200
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


def _agreement_quantity(agreement: Agreement, request: Request) -> tuple[Quantity, datetime, datetime]:
    try:
        terms = json.loads(agreement.terms_snapshot)
        quantity = terms["quantity"]
        agreed = Quantity(
            exact_decimal(quantity["value"]),
            quantity["unit"],
            quantity["unit_registry_version"],
        )
        valid_from = datetime.fromisoformat(terms["valid_from"])
        valid_until = datetime.fromisoformat(terms["valid_until"])
    except (KeyError, TypeError, ValueError, DomainError) as exc:
        _fail(
            request,
            409,
            "AGREEMENT_TERMS_INVALID",
            "DOMAIN_CONFLICT",
            "Agreement has no valid canonical quantity or validity window.",
        )
        raise exc
    if valid_from.tzinfo is None or valid_until.tzinfo is None:
        _fail(
            request,
            409,
            "AGREEMENT_TERMS_INVALID",
            "DOMAIN_CONFLICT",
            "Agreement validity timestamps must be timezone-aware.",
        )
    return agreed, valid_from, valid_until


@router.post("/v1/reservations", status_code=201)
def create_reservation(
    body: ReservationCreate,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("reservations:write"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(body.model_dump(mode="json"))
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)

    agreement = session.scalar(
        select(Agreement).where(
            Agreement.id == body.agreement_id,
            Agreement.organization_id == principal.organization_id,
        )
    )
    if agreement is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Agreement not found.")
    if agreement.status != "ACTIVE":
        _fail(
            request,
            409,
            "AGREEMENT_NOT_ACTIVE",
            "DOMAIN_CONFLICT",
            "Reservations require an active Agreement.",
        )
    if principal.actor_id not in {agreement.proposer_actor_id, agreement.recipient_actor_id}:
        _fail(
            request,
            403,
            "AGREEMENT_PARTICIPANT_REQUIRED",
            "AUTHORIZATION_FAILURE",
            "Only an Agreement participant may create a Reservation.",
        )

    offer = session.scalar(
        select(Offer).where(
            Offer.id == agreement.offer_id,
            Offer.organization_id == principal.organization_id,
            Offer.version == agreement.offer_version,
        )
    )
    if offer is None or offer.status != "ACCEPTED":
        _fail(
            request,
            409,
            "AGREEMENT_OFFER_STALE",
            "DOMAIN_CONFLICT",
            "The Agreement's accepted Offer is unavailable or has changed.",
        )
    opportunity = session.scalar(
        select(Opportunity).where(
            Opportunity.id == offer.opportunity_id,
            Opportunity.organization_id == principal.organization_id,
        )
    )
    if opportunity is None or opportunity.version != offer.opportunity_version:
        _fail(
            request,
            409,
            "OPPORTUNITY_STALE",
            "DOMAIN_CONFLICT",
            "The source Opportunity no longer matches the accepted Offer.",
        )
    if opportunity.source_resource_state_id != body.resource_state_id:
        _fail(
            request,
            409,
            "RESOURCE_STATE_NOT_IN_OPPORTUNITY",
            "DOMAIN_CONFLICT",
            "Reservation must reference the source ResourceState of the accepted Opportunity.",
        )

    # This row lock serializes every allocation against this Resource on PostgreSQL.
    state = session.scalar(
        select(ResourceState).where(
            ResourceState.id == body.resource_state_id,
            ResourceState.organization_id == principal.organization_id,
        )
    )
    if state is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Source ResourceState not found.")
    resource = session.scalar(
        select(Resource)
        .where(
            Resource.id == state.resource_id,
            Resource.organization_id == principal.organization_id,
        )
        .with_for_update()
    )
    if resource is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Source Resource not found.")
    if (
        resource.version != body.resource_state_version
        or state.resource_version != body.resource_state_version
        or opportunity.source_resource_state_version != body.resource_state_version
    ):
        _fail(
            request,
            409,
            "RESOURCE_STATE_STALE",
            "CONCURRENCY_FAILURE",
            "Reservation must reference the current ResourceState version.",
        )

    now = datetime.now(UTC)
    agreement_quantity, valid_from, valid_until = _agreement_quantity(agreement, request)
    if now < valid_from or now >= valid_until:
        _fail(
            request,
            409,
            "AGREEMENT_WINDOW_CLOSED",
            "DOMAIN_CONFLICT",
            "Agreement terms are outside their reservation validity window.",
        )
    if body.expires_at <= now or body.expires_at > valid_until:
        _fail(
            request,
            422,
            "RESERVATION_EXPIRY_INVALID",
            "VALIDATION_FAILURE",
            "Reservation expiry must be in the future and no later than Agreement expiry.",
        )

    requested = Quantity(
        body.quantity_value,
        body.quantity_unit,
        body.unit_registry_version,
    )
    state_quantity = Quantity(state.quantity_value, state.unit, state.unit_registry_version)
    existing_for_state = session.scalars(
        select(ReservationRecord).where(
            ReservationRecord.organization_id == principal.organization_id,
            ReservationRecord.resource_state_id == state.id,
            ReservationRecord.status == ReservationStatus.ACTIVE.value,
            ReservationRecord.expires_at > now,
            ReservationRecord.created_at <= now,
        )
    ).all()
    existing_for_agreement = session.scalars(
        select(ReservationRecord).where(
            ReservationRecord.organization_id == principal.organization_id,
            ReservationRecord.agreement_id == agreement.id,
            ReservationRecord.status == ReservationStatus.ACTIVE.value,
            ReservationRecord.expires_at > now,
            ReservationRecord.created_at <= now,
        )
    ).all()
    active_for_state = [_domain(item) for item in existing_for_state]
    active_for_agreement = [_domain(item) for item in existing_for_agreement]
    try:
        already_reserved = active_reserved_quantity(
            active_for_state,
            now=now,
            unit=state.unit,
            unit_registry_version=state.unit_registry_version,
        )
        already_reserved_for_agreement = active_reserved_quantity(
            active_for_agreement,
            now=now,
            unit=agreement_quantity.unit,
            unit_registry_version=agreement_quantity.unit_registry_version,
        )
        validate_reservation_capacity(
            requested=requested,
            agreement_quantity=agreement_quantity,
            state_quantity=state_quantity,
            already_reserved=already_reserved,
            already_reserved_for_agreement=already_reserved_for_agreement,
        )
        domain = DomainReservation(
            id=f"rsv_{uuid4().hex}",
            organization_id=principal.organization_id,
            agreement_id=agreement.id,
            resource_id=resource.id,
            resource_state_id=state.id,
            resource_version=state.resource_version,
            quantity=requested,
            status=ReservationStatus.ACTIVE,
            expires_at=body.expires_at,
            version=1,
            created_by=principal.actor_id,
            created_at=now,
            updated_at=now,
            provenance={
                "source_type": "CRR_API",
                "opportunity_id": opportunity.id,
                "offer_id": offer.id,
                "agreement_id": agreement.id,
                "resource_state_version": str(state.resource_version),
            },
        )
    except DomainError as exc:
        _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))

    item = ReservationRecord(
        id=domain.id,
        organization_id=domain.organization_id,
        agreement_id=domain.agreement_id,
        resource_id=domain.resource_id,
        resource_state_id=domain.resource_state_id,
        resource_version=domain.resource_version,
        quantity_value=domain.quantity.value,
        quantity_unit=domain.quantity.unit,
        unit_registry_version=domain.quantity.unit_registry_version,
        status=domain.status.value,
        expires_at=domain.expires_at,
        version=domain.version,
        created_by=domain.created_by,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
        provenance=domain.provenance,
    )
    session.add(item)
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _emit(session, request, principal, item, idempotency_key, "reservation.created")
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
            "RESERVATION_CONFLICT",
            "DOMAIN_CONFLICT",
            "Reservation conflicted with another allocation or integrity constraint.",
        )
    except SQLAlchemyError:
        session.rollback()
        _fail(
            request,
            503,
            "DATABASE_UNAVAILABLE",
            "DATABASE_FAILURE",
            "Reservation could not be persisted.",
        )
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


@router.get("/v1/reservations/{reservation_id}")
def get_reservation(
    reservation_id: str,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("reservations:read"))],
):
    item = _find(session, reservation_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Reservation not found.")
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))


@router.get("/v1/reservations")
def list_reservations(
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("reservations:read"))],
):
    items = session.scalars(
        select(ReservationRecord)
        .where(ReservationRecord.organization_id == principal.organization_id)
        .order_by(ReservationRecord.created_at.desc(), ReservationRecord.id.desc())
    ).all()
    return _collection(request, [_data(item) for item in items], None, False, len(items))


@router.patch("/v1/reservations/{reservation_id}")
def transition_reservation(
    reservation_id: str,
    body: ReservationLifecycleInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("reservations:write"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(
        body.model_dump(mode="json") | {"reservation_id": reservation_id, "if_match": if_match}
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
    item = session.scalar(
        select(ReservationRecord)
        .where(
            ReservationRecord.id == reservation_id,
            ReservationRecord.organization_id == principal.organization_id,
        )
        .with_for_update()
    )
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Reservation not found.")
    if if_match != f'"version-{item.version}"':
        _fail(
            request,
            409,
            "STALE_VERSION",
            "CONCURRENCY_FAILURE",
            "Reservation version is stale.",
        )
    agreement = session.scalar(
        select(Agreement).where(
            Agreement.id == item.agreement_id,
            Agreement.organization_id == principal.organization_id,
        )
    )
    if agreement is None:
        _fail(
            request,
            409,
            "AGREEMENT_MISSING",
            "DOMAIN_CONFLICT",
            "Reservation Agreement reference is unavailable.",
        )
    if body.status == "RELEASED":
        if principal.actor_id not in {agreement.proposer_actor_id, agreement.recipient_actor_id}:
            _fail(
                request,
                403,
                "AGREEMENT_PARTICIPANT_REQUIRED",
                "AUTHORIZATION_FAILURE",
                "Only an Agreement participant may release a Reservation.",
            )
    else:
        if "reservations:expire" not in principal.scopes and "admin:*" not in principal.scopes:
            _fail(
                request,
                403,
                "EXPIRY_SCOPE_REQUIRED",
                "AUTHORIZATION_FAILURE",
                "Reservation expiry requires the reservations:expire scope.",
            )
    try:
        domain = _domain(item)
        changed = (
            domain.release(actor_id=principal.actor_id, at=datetime.now(UTC))
            if body.status == "RELEASED"
            else domain.expire(at=datetime.now(UTC))
        )
    except DomainError as exc:
        _fail(request, 409, exc.code, "DOMAIN_CONFLICT", str(exc))

    item.status = changed.status.value
    item.version = changed.version
    item.updated_at = changed.updated_at
    item.provenance = changed.provenance
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _emit(
        session,
        request,
        principal,
        item,
        idempotency_key,
        f"reservation.{changed.status.value.lower()}",
    )
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        _fail(
            request,
            503,
            "DATABASE_UNAVAILABLE",
            "DATABASE_FAILURE",
            "Reservation lifecycle update failed.",
        )
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(item))
