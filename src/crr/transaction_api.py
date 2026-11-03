"""Tenant-isolated Transaction API over accepted Agreements and complete Reservations."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from crr.agreement_model import Agreement
from crr.domain.errors import DomainError
from crr.domain.quantity import Quantity, exact_decimal
from crr.domain.reservation import Reservation as DomainReservation
from crr.domain.reservation import ReservationStatus
from crr.domain.transaction import Transaction as DomainTransaction
from crr.domain.transaction import (
    TransactionStatus,
    validate_transaction_reservation_coverage,
)
from crr.models import IdempotencyRecord, OutboxEvent, Resource, ResourceState
from crr.offer_model import Offer
from crr.opportunity_model import Opportunity
from crr.reservation_model import Reservation as ReservationRecord
from crr.transaction_model import Transaction as TransactionRecord
from crr.transaction_model import transaction_reservations
from crr.transaction_schemas import TransactionCreate, TransactionLifecycleInput

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


def _agreement_terms(
    agreement: Agreement,
    request: Request,
) -> tuple[Quantity, Decimal, str, datetime, datetime]:
    try:
        terms = json.loads(agreement.terms_snapshot)
        quantity = terms["quantity"]
        agreed_quantity = Quantity(
            exact_decimal(quantity["value"]),
            quantity["unit"],
            quantity["unit_registry_version"],
        )
        price = exact_decimal(terms["price"])
        currency = terms["currency"]
        valid_from = datetime.fromisoformat(terms["valid_from"])
        valid_until = datetime.fromisoformat(terms["valid_until"])
        if (
            valid_from.tzinfo is None
            or valid_from.utcoffset() is None
            or valid_until.tzinfo is None
            or valid_until.utcoffset() is None
        ):
            raise ValueError("Agreement terms contain naive timestamps.")
        if valid_from >= valid_until:
            raise ValueError("Agreement validity window is invalid.")
        if not isinstance(currency, str) or len(currency) != 3 or currency.upper() != currency:
            raise ValueError("Agreement currency is invalid.")
        return agreed_quantity, price, currency, valid_from, valid_until
    except (KeyError, TypeError, ValueError, DomainError) as exc:
        _fail(
            request,
            409,
            "AGREEMENT_TERMS_INVALID",
            "DOMAIN_CONFLICT",
            f"Agreement terms cannot produce a Transaction: {exc}",
        )


def _reservation_domain(item: ReservationRecord) -> DomainReservation:
    return DomainReservation(
        id=item.id,
        organization_id=item.organization_id,
        agreement_id=item.agreement_id,
        resource_id=item.resource_id,
        resource_state_id=item.resource_state_id,
        resource_version=item.resource_version,
        quantity=Quantity(item.quantity_value, item.quantity_unit, item.unit_registry_version),
        status=ReservationStatus(item.status),
        expires_at=item.expires_at,
        version=item.version,
        created_by=item.created_by,
        created_at=item.created_at,
        updated_at=item.updated_at,
        provenance=item.provenance,
    )


def _transaction_domain(session: Session, item: TransactionRecord) -> DomainTransaction:
    reservation_ids = tuple(
        session.scalars(
            select(transaction_reservations.c.reservation_id)
            .where(
                transaction_reservations.c.organization_id == item.organization_id,
                transaction_reservations.c.transaction_id == item.id,
            )
            .order_by(transaction_reservations.c.reservation_id)
        ).all()
    )
    return DomainTransaction(
        id=item.id,
        organization_id=item.organization_id,
        agreement_id=item.agreement_id,
        offer_id=item.offer_id,
        offer_version=item.offer_version,
        opportunity_id=item.opportunity_id,
        opportunity_version=item.opportunity_version,
        route_candidate_id=item.route_candidate_id,
        resource_id=item.resource_id,
        resource_state_id=item.resource_state_id,
        resource_version=item.resource_version,
        proposer_actor_id=item.proposer_actor_id,
        recipient_actor_id=item.recipient_actor_id,
        quantity=Quantity(item.quantity_value, item.quantity_unit, item.unit_registry_version),
        price=item.price,
        currency=item.currency,
        terms_snapshot=item.terms_snapshot,
        reservation_ids=reservation_ids,
        status=TransactionStatus(item.status),
        version=item.version,
        created_by=item.created_by,
        created_at=item.created_at,
        updated_at=item.updated_at,
        provenance=item.provenance,
        scheduled_for=item.scheduled_for,
    )


def _data(session: Session, item: TransactionRecord) -> dict[str, Any]:
    domain = _transaction_domain(session, item)
    return {
        "id": item.id,
        "organization_id": item.organization_id,
        "agreement_id": item.agreement_id,
        "offer_id": item.offer_id,
        "offer_version": item.offer_version,
        "opportunity_id": item.opportunity_id,
        "opportunity_version": item.opportunity_version,
        "route_candidate_id": item.route_candidate_id,
        "resource_id": item.resource_id,
        "resource_state_id": item.resource_state_id,
        "resource_state_version": item.resource_version,
        "parties": {
            "proposer_actor_id": item.proposer_actor_id,
            "recipient_actor_id": item.recipient_actor_id,
        },
        "quantity": {
            "value": str(item.quantity_value),
            "unit": item.quantity_unit,
            "unit_registry_version": item.unit_registry_version,
        },
        "price": str(item.price),
        "currency": item.currency,
        "terms": json.loads(item.terms_snapshot),
        "reservation_ids": list(domain.reservation_ids),
        "status": item.status,
        "scheduled_for": item.scheduled_for.isoformat() if item.scheduled_for else None,
        "version": item.version,
        "created_by": item.created_by,
        "created_at": item.created_at.isoformat(),
        "updated_at": item.updated_at.isoformat(),
        "provenance": item.provenance,
    }


def _find(session: Session, transaction_id: str, organization_id: str):
    return session.scalar(
        select(TransactionRecord).where(
            TransactionRecord.id == transaction_id,
            TransactionRecord.organization_id == organization_id,
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
    if prior and (prior.request_hash != digest or prior.object_type != "Transaction"):
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
    transaction_id: str,
) -> None:
    session.add(
        IdempotencyRecord(
            organization_id=organization_id,
            idempotency_key=key,
            request_hash=digest,
            object_type="Transaction",
            object_id=transaction_id,
            created_at=datetime.now(UTC),
        )
    )


def _emit(
    session: Session,
    request: Request,
    principal: Any,
    item: TransactionRecord,
    key: str,
    event_type: str,
) -> None:
    reservation_ids = session.scalars(
        select(transaction_reservations.c.reservation_id)
        .where(
            transaction_reservations.c.organization_id == item.organization_id,
            transaction_reservations.c.transaction_id == item.id,
        )
        .order_by(transaction_reservations.c.reservation_id)
    ).all()
    session.add(
        OutboxEvent(
            id=f"evt_{uuid4().hex}",
            event_type=event_type,
            event_version=1,
            aggregate_type="Transaction",
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
                "transaction_id": item.id,
                "agreement_id": item.agreement_id,
                "offer_id": item.offer_id,
                "offer_version": item.offer_version,
                "opportunity_id": item.opportunity_id,
                "opportunity_version": item.opportunity_version,
                "route_candidate_id": item.route_candidate_id,
                "resource_id": item.resource_id,
                "resource_state_id": item.resource_state_id,
                "resource_version": item.resource_version,
                "reservation_ids": reservation_ids,
                "status": item.status,
                "version": item.version,
                "scheduled_for": item.scheduled_for.isoformat() if item.scheduled_for else None,
                "provenance": item.provenance,
            },
            provenance={"source_type": "CRR_API", "request_id": request.state.request_id},
            schema_version="0.1",
        )
    )


def _emit_reservation(
    session: Session,
    request: Request,
    principal: Any,
    transaction: TransactionRecord,
    item: ReservationRecord,
    event_type: str,
) -> None:
    reservation_event_key = (
        f"transaction-cancel:{transaction.id}:v{transaction.version + 1}:{item.id}"
    )
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
            causation_id=transaction.id,
            idempotency_key=reservation_event_key,
            payload={
                "reservation_id": item.id,
                "transaction_id": transaction.id,
                "agreement_id": transaction.agreement_id,
                "status": item.status,
                "version": item.version,
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
            "Idempotent Transaction result is unavailable.",
        )
    response.status_code = 200
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(session, item))


@router.post("/v1/transactions", status_code=201)
def create_transaction(
    body: TransactionCreate,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("transactions:write"))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(body.model_dump(mode="json"))
    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)

    agreement = session.scalar(
        select(Agreement)
        .where(
            Agreement.id == body.agreement_id,
            Agreement.organization_id == principal.organization_id,
        )
        .with_for_update()
    )
    if agreement is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Agreement not found.")
    if agreement.status != "ACTIVE":
        _fail(
            request,
            409,
            "AGREEMENT_NOT_ACTIVE",
            "DOMAIN_CONFLICT",
            "Transaction creation requires an active Agreement.",
        )
    if principal.actor_id not in {agreement.proposer_actor_id, agreement.recipient_actor_id}:
        _fail(
            request,
            403,
            "AGREEMENT_PARTICIPANT_REQUIRED",
            "AUTHORIZATION_FAILURE",
            "Only an Agreement participant may create its Transaction.",
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
        select(Opportunity)
        .where(
            Opportunity.id == offer.opportunity_id,
            Opportunity.organization_id == principal.organization_id,
        )
        .with_for_update()
    )
    if opportunity is None or opportunity.version != offer.opportunity_version:
        _fail(
            request,
            409,
            "OPPORTUNITY_STALE",
            "DOMAIN_CONFLICT",
            "The source Opportunity no longer matches the accepted Offer.",
        )
    if opportunity.status != "OPEN":
        _fail(
            request,
            409,
            "OPPORTUNITY_NOT_ACTIVE",
            "DOMAIN_CONFLICT",
            "Transaction creation requires an active source Opportunity.",
        )

    now = datetime.now(UTC)
    if now < opportunity.valid_from or now >= opportunity.valid_until:
        _fail(
            request,
            409,
            "OPPORTUNITY_WINDOW_CLOSED",
            "DOMAIN_CONFLICT",
            "Transaction creation requires a currently valid Opportunity.",
        )
    agreed_quantity, price, currency, valid_from, valid_until = _agreement_terms(agreement, request)
    if now < valid_from or now >= valid_until:
        _fail(
            request,
            409,
            "AGREEMENT_WINDOW_CLOSED",
            "DOMAIN_CONFLICT",
            "Agreement terms are outside their Transaction validity window.",
        )

    state = session.scalar(
        select(ResourceState).where(
            ResourceState.id == opportunity.source_resource_state_id,
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
        resource.version != opportunity.source_resource_state_version
        or state.resource_version != opportunity.source_resource_state_version
    ):
        _fail(
            request,
            409,
            "RESOURCE_STATE_STALE",
            "CONCURRENCY_FAILURE",
            "Transaction must reference the current source ResourceState version.",
        )

    prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
    if prior:
        return _replay(session, response, request, prior, principal.organization_id)

    reservations = session.scalars(
        select(ReservationRecord)
        .where(
            ReservationRecord.organization_id == principal.organization_id,
            ReservationRecord.agreement_id == agreement.id,
            ReservationRecord.status == ReservationStatus.ACTIVE.value,
            ReservationRecord.expires_at > now,
            ReservationRecord.created_at <= now,
        )
        .order_by(ReservationRecord.id)
        .with_for_update()
    ).all()
    reservation_ids = tuple(sorted(item.id for item in reservations))
    if set(reservation_ids) != set(body.reservation_ids):
        _fail(
            request,
            409,
            "RESERVATION_SET_MISMATCH",
            "DOMAIN_CONFLICT",
            "Transaction must include every active, unexpired Reservation for its Agreement.",
        )
    try:
        domain_reservations = [_reservation_domain(item) for item in reservations]
        validate_transaction_reservation_coverage(
            organization_id=principal.organization_id,
            agreement_id=agreement.id,
            resource_id=resource.id,
            resource_state_id=state.id,
            resource_version=state.resource_version,
            agreement_status=agreement.status,
            agreed_quantity=agreed_quantity,
            reservations=domain_reservations,
            now=now,
        )
        domain = DomainTransaction(
            id=f"txn_{uuid4().hex}",
            organization_id=principal.organization_id,
            agreement_id=agreement.id,
            offer_id=agreement.offer_id,
            offer_version=agreement.offer_version,
            opportunity_id=opportunity.id,
            opportunity_version=opportunity.version,
            route_candidate_id=opportunity.route_candidate_id,
            resource_id=resource.id,
            resource_state_id=state.id,
            resource_version=state.resource_version,
            proposer_actor_id=agreement.proposer_actor_id,
            recipient_actor_id=agreement.recipient_actor_id,
            quantity=agreed_quantity,
            price=price,
            currency=currency,
            terms_snapshot=agreement.terms_snapshot,
            reservation_ids=reservation_ids,
            status=TransactionStatus.AGREED,
            version=1,
            created_by=principal.actor_id,
            created_at=now,
            updated_at=now,
            provenance={
                "source_type": "CRR_API",
                "offer_id": agreement.offer_id,
                "agreement_id": agreement.id,
                "opportunity_id": opportunity.id,
                "route_candidate_id": opportunity.route_candidate_id,
                "reservation_ids": ",".join(reservation_ids),
            },
        )
    except DomainError as exc:
        _fail(request, 422, exc.code, "VALIDATION_FAILURE", str(exc))

    item = TransactionRecord(
        id=domain.id,
        organization_id=domain.organization_id,
        agreement_id=domain.agreement_id,
        offer_id=domain.offer_id,
        offer_version=domain.offer_version,
        opportunity_id=domain.opportunity_id,
        opportunity_version=domain.opportunity_version,
        route_candidate_id=domain.route_candidate_id,
        resource_id=domain.resource_id,
        resource_state_id=domain.resource_state_id,
        resource_version=domain.resource_version,
        proposer_actor_id=domain.proposer_actor_id,
        recipient_actor_id=domain.recipient_actor_id,
        quantity_value=domain.quantity.value,
        quantity_unit=domain.quantity.unit,
        unit_registry_version=domain.quantity.unit_registry_version,
        price=domain.price,
        currency=domain.currency,
        terms_snapshot=domain.terms_snapshot,
        status=domain.status.value,
        version=domain.version,
        created_by=domain.created_by,
        created_at=domain.created_at,
        updated_at=domain.updated_at,
        scheduled_for=None,
        provenance=domain.provenance,
    )
    try:
        session.add(item)
        session.flush()
        session.execute(
            transaction_reservations.insert(),
            [
                {
                    "organization_id": principal.organization_id,
                    "transaction_id": item.id,
                    "reservation_id": reservation_id,
                }
                for reservation_id in reservation_ids
            ],
        )
        _remember(session, principal.organization_id, idempotency_key, digest, item.id)
        _emit(session, request, principal, item, idempotency_key, "transaction.created")
        session.commit()
    except IntegrityError:
        session.rollback()
        prior = _idempotency(session, principal.organization_id, idempotency_key, digest, request)
        if prior:
            return _replay(session, response, request, prior, principal.organization_id)
        existing = session.scalar(
            select(TransactionRecord.id).where(
                TransactionRecord.organization_id == principal.organization_id,
                TransactionRecord.agreement_id == body.agreement_id,
            )
        )
        if existing is not None:
            _fail(
                request,
                409,
                "TRANSACTION_ALREADY_EXISTS",
                "DOMAIN_CONFLICT",
                "This Agreement already has a Transaction.",
            )
        _fail(
            request,
            409,
            "TRANSACTION_CONFLICT",
            "DOMAIN_CONFLICT",
            "Transaction creation conflicted with another operation.",
        )
    except SQLAlchemyError:
        session.rollback()
        _fail(
            request,
            503,
            "DATABASE_UNAVAILABLE",
            "DATABASE_FAILURE",
            "Transaction could not be persisted.",
        )
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(session, item))


@router.get("/v1/transactions")
def list_transactions(
    request: Request,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("transactions:read"))],
    limit: int = Query(default=50, ge=1, le=100),
    cursor: str | None = None,
):
    statement = select(TransactionRecord).where(
        TransactionRecord.organization_id == principal.organization_id
    )
    if cursor:
        statement = statement.where(TransactionRecord.id > cursor)
    rows = session.scalars(statement.order_by(TransactionRecord.id).limit(limit + 1)).all()
    has_more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = rows[-1].id if has_more and rows else None
    return _collection(
        request,
        [_data(session, row) for row in rows],
        next_cursor,
        has_more,
        limit,
    )


@router.get("/v1/transactions/{transaction_id}")
def get_transaction(
    transaction_id: str,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("transactions:read"))],
):
    item = _find(session, transaction_id, principal.organization_id)
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Transaction not found.")
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(session, item))


@router.patch("/v1/transactions/{transaction_id}")
def transition_transaction(
    transaction_id: str,
    body: TransactionLifecycleInput,
    request: Request,
    response: Response,
    session: Annotated[Session, Depends(_session_dependency())],
    principal: Annotated[Any, Depends(_scope_dependency("transactions:write"))],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    digest = _body_hash(
        body.model_dump(mode="json")
        | {"transaction_id": transaction_id, "if_match": if_match}
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
        select(TransactionRecord)
        .where(
            TransactionRecord.id == transaction_id,
            TransactionRecord.organization_id == principal.organization_id,
        )
        .with_for_update()
    )
    if item is None:
        _fail(request, 404, "NOT_FOUND", "NOT_FOUND", "Transaction not found.")
    if if_match != f'"version-{item.version}"':
        _fail(
            request,
            409,
            "STALE_VERSION",
            "CONCURRENCY_FAILURE",
            "Transaction version is stale.",
        )
    domain = _transaction_domain(session, item)
    now = datetime.now(UTC)
    try:
        if body.status == "SCHEDULED":
            if domain.status is TransactionStatus.DISPUTED:
                if (
                    "transactions:resolve" not in principal.scopes
                    and "admin:*" not in principal.scopes
                ):
                    _fail(
                        request,
                        403,
                        "TRANSACTION_RESOLUTION_SCOPE_REQUIRED",
                        "AUTHORIZATION_FAILURE",
                        "Resolving a Transaction dispute requires transactions:resolve.",
                    )
                if body.scheduled_for is None or not body.resolution_note:
                    _fail(
                        request,
                        422,
                        "TRANSACTION_RESOLUTION_INPUT_REQUIRED",
                        "VALIDATION_FAILURE",
                        "Dispute resolution requires scheduled_for and resolution_note.",
                    )
                if body.reason is not None:
                    _fail(
                        request,
                        422,
                        "UNEXPECTED_LIFECYCLE_FIELD",
                        "VALIDATION_FAILURE",
                        "Dispute resolution must not include reason.",
                    )
                changed = domain.resolve(
                    actor_id=principal.actor_id,
                    at=now,
                    scheduled_for=body.scheduled_for,
                    resolution_note=body.resolution_note,
                )
            else:
                if body.scheduled_for is None:
                    _fail(
                        request,
                        422,
                        "TRANSACTION_SCHEDULE_REQUIRED",
                        "VALIDATION_FAILURE",
                        "Scheduling requires scheduled_for.",
                    )
                if body.reason is not None or body.resolution_note is not None:
                    _fail(
                        request,
                        422,
                        "UNEXPECTED_LIFECYCLE_FIELD",
                        "VALIDATION_FAILURE",
                        "Scheduling must not include reason or resolution_note.",
                    )
                changed = domain.schedule(
                    actor_id=principal.actor_id,
                    at=now,
                    scheduled_for=body.scheduled_for,
                )
        elif body.status == "DISPUTED":
            if (
                not body.reason
                or body.scheduled_for is not None
                or body.resolution_note is not None
            ):
                _fail(
                    request,
                    422,
                    "TRANSACTION_DISPUTE_INPUT_INVALID",
                    "VALIDATION_FAILURE",
                    "Disputing requires reason only.",
                )
            changed = domain.dispute(actor_id=principal.actor_id, at=now, reason=body.reason)
        else:
            if (
                not body.reason
                or body.scheduled_for is not None
                or body.resolution_note is not None
            ):
                _fail(
                    request,
                    422,
                    "TRANSACTION_CANCELLATION_INPUT_INVALID",
                    "VALIDATION_FAILURE",
                    "Cancelling requires reason only.",
                )
            changed = domain.cancel(actor_id=principal.actor_id, at=now, reason=body.reason)
    except DomainError as exc:
        _fail(request, 409, exc.code, "DOMAIN_CONFLICT", str(exc))

    if changed.status is TransactionStatus.CANCELLED:
        linked_reservations = session.scalars(
            select(ReservationRecord)
            .join(
                transaction_reservations,
                (transaction_reservations.c.organization_id == ReservationRecord.organization_id)
                & (transaction_reservations.c.reservation_id == ReservationRecord.id),
            )
            .where(
                transaction_reservations.c.organization_id == principal.organization_id,
                transaction_reservations.c.transaction_id == item.id,
            )
            .with_for_update()
        ).all()
        for reservation in linked_reservations:
            if reservation.status != ReservationStatus.ACTIVE.value:
                continue
            reservation_domain = _reservation_domain(reservation)
            try:
                reservation_changed = (
                    reservation_domain.expire(at=now)
                    if reservation.expires_at <= now
                    else reservation_domain.release(actor_id=principal.actor_id, at=now)
                )
            except DomainError as exc:
                _fail(request, 409, exc.code, "DOMAIN_CONFLICT", str(exc))
            reservation.status = reservation_changed.status.value
            reservation.version = reservation_changed.version
            reservation.updated_at = reservation_changed.updated_at
            reservation.provenance = reservation_changed.provenance
            _emit_reservation(
                session,
                request,
                principal,
                item,
                reservation,
                "reservation.expired"
                if reservation_changed.status is ReservationStatus.EXPIRED
                else "reservation.released",
            )

    item.status = changed.status.value
    item.version = changed.version
    item.updated_at = changed.updated_at
    item.scheduled_for = changed.scheduled_for
    item.provenance = changed.provenance
    _remember(session, principal.organization_id, idempotency_key, digest, item.id)
    _emit(session, request, principal, item, idempotency_key, "transaction.updated")
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        _fail(
            request,
            409,
            "TRANSACTION_CONFLICT",
            "DOMAIN_CONFLICT",
            "Transaction lifecycle update conflicted with another operation.",
        )
    except SQLAlchemyError:
        session.rollback()
        _fail(
            request,
            503,
            "DATABASE_UNAVAILABLE",
            "DATABASE_FAILURE",
            "Transaction lifecycle update failed.",
        )
    response.headers["ETag"] = f'"version-{item.version}"'
    return _envelope(request, _data(session, item))
