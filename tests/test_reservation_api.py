import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.agreement_model import Agreement
from crr.api import create_app
from crr.models import (
    Actor,
    APIKey,
    Base,
    Location,
    Organization,
    OutboxEvent,
    Resource,
    ResourceState,
)
from crr.offer_model import Offer
from crr.opportunity_model import Opportunity
from crr.reservation_model import Reservation
from crr.transaction_model import Transaction, transaction_reservations

NOW = datetime(2026, 11, 3, 0, tzinfo=UTC)


def reservation_fixture(state_quantity: str = "20.000"):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    token = "buyer-secret"
    with factory.begin() as session:
        session.add(Organization(id="org_a", name="Factory", status="ACTIVE", created_at=NOW))
        session.add_all(
            [
                Actor(
                    id="act_seller",
                    organization_id="org_a",
                    name="Seller",
                    role="ORG_ADMIN",
                    active=True,
                    created_at=NOW,
                ),
                Actor(
                    id="act_buyer",
                    organization_id="org_a",
                    name="Buyer",
                    role="ORG_ADMIN",
                    active=True,
                    created_at=NOW,
                ),
            ]
        )
        session.add(
            APIKey(
                id="key_buyer",
                organization_id="org_a",
                actor_id="act_buyer",
                secret_hash=sha256(token.encode()).hexdigest(),
                scopes=[
                    "reservations:read",
                    "reservations:write",
                    "reservations:expire",
                    "resources:write",
                    "transactions:read",
                    "transactions:write",
                    "transactions:resolve",
                    "executions:read",
                    "executions:write",
                    "executions:plan",
                    "execution:operate",
                    "execution:correct",
                    "executions:exceptions:write",
                    "executions:exceptions:resolve",
                    "executions:close",
                    "executions:cancel",
                ],
                revoked=False,
                created_at=NOW,
            )
        )
        session.add(
            Location(
                id="loc_a",
                organization_id="org_a",
                name="Yard",
                provenance={"source_type": "TEST"},
                created_at=NOW,
            )
        )
        session.add(
            Resource(
                id="res_a",
                organization_id="org_a",
                resource_type="ALUMINUM",
                version=1,
                created_by="act_seller",
                provenance={"source_type": "TEST"},
                created_at=NOW,
            )
        )
        session.add(
            ResourceState(
                id="rst_a",
                organization_id="org_a",
                resource_id="res_a",
                resource_version=1,
                state_type="ALUMINUM_SCRAP",
                quantity_value=Decimal(state_quantity),
                unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                location_id="loc_a",
                effective_at=NOW,
                recorded_at=NOW,
                created_by="act_seller",
                provenance={"source_type": "TEST"},
                quality={},
                physical_properties={},
                predecessor_state_ids=[],
            )
        )
        session.add(
            Opportunity(
                id="opp_a",
                organization_id="org_a",
                route_candidate_id="route_a",
                candidate_set_fingerprint="a" * 64,
                source_resource_state_id="rst_a",
                source_resource_state_version=1,
                target_demand_id="dem_a",
                target_demand_version=1,
                route_provenance={"route_id": "route_a"},
                advisory_provenance=None,
                economic_model_id=None,
                economic_model_version=None,
                commercial_perspective=None,
                currency="SAR",
                quantity_value=Decimal("20.000"),
                quantity_unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                valid_from=NOW,
                valid_until=datetime(2026, 12, 1, tzinfo=UTC),
                status="OPEN",
                version=1,
                created_by="act_seller",
                provenance={"source_type": "TEST"},
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.add(
            Offer(
                id="off_a",
                organization_id="org_a",
                opportunity_id="opp_a",
                opportunity_version=1,
                proposer_actor_id="act_seller",
                recipient_actor_id="act_buyer",
                quantity_value=Decimal("10.250"),
                quantity_unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                price=Decimal("125.50"),
                currency="SAR",
                delivery_terms={"incoterm": "DAP"},
                timing_terms={"delivery_by": "2026-11-30"},
                route_assumptions={"route_id": "route_a"},
                conditions={},
                valid_from=NOW,
                valid_until=datetime(2026, 12, 1, tzinfo=UTC),
                status="ACCEPTED",
                version=2,
                created_by="act_seller",
                provenance={"source_type": "TEST"},
                created_at=NOW,
                updated_at=NOW,
            )
        )
        session.add(
            Agreement(
                id="agr_a",
                organization_id="org_a",
                offer_id="off_a",
                offer_version=2,
                proposer_actor_id="act_seller",
                recipient_actor_id="act_buyer",
                accepted_by="act_buyer",
                accepted_at=NOW,
                terms_snapshot=json.dumps(
                    {
                        "quantity": {
                            "value": "10.250",
                            "unit": "t",
                            "unit_registry_version": "CRR-UNITS-0.1",
                        },
                        "price": "125.50",
                        "currency": "SAR",
                        "delivery_terms": {"incoterm": "DAP"},
                        "timing_terms": {"delivery_by": "2026-11-30"},
                        "valid_from": NOW.isoformat(),
                        "valid_until": datetime(2026, 12, 1, tzinfo=UTC).isoformat(),
                    }
                ),
                status="ACTIVE",
                version=1,
                created_at=NOW,
                updated_at=NOW,
                provenance=json.dumps({"source_type": "TEST"}),
            )
        )
    return TestClient(create_app(factory)), token, engine


def auth(token: str, key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if key:
        headers["Idempotency-Key"] = key
    return headers


def payload(quantity: str = "6.000") -> dict:
    return {
        "agreement_id": "agr_a",
        "resource_state_id": "rst_a",
        "resource_state_version": 1,
        "quantity_value": quantity,
        "quantity_unit": "t",
        "unit_registry_version": "CRR-UNITS-0.1",
        "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
    }


def test_create_reservation_is_idempotent_and_audited():
    client, token, engine = reservation_fixture()
    headers = auth(token, "reservation-create")
    request_payload = payload()
    created = client.post("/v1/reservations", json=request_payload, headers=headers)
    replay = client.post("/v1/reservations", json=request_payload, headers=headers)
    assert created.status_code == 201, created.text
    assert replay.status_code == 200
    item = created.json()["data"]
    assert item["quantity"]["value"] == "6.000"
    assert item["status"] == "ACTIVE"
    fetched = client.get(f"/v1/reservations/{item['id']}", headers=auth(token))
    assert fetched.status_code == 200
    with engine.connect() as connection:
        record = connection.execute(select(Reservation).where(Reservation.id == item["id"])).one()
        event = connection.execute(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == item["id"])
        ).one()
        state = connection.execute(select(ResourceState).where(ResourceState.id == "rst_a")).one()
        resource = connection.execute(select(Resource).where(Resource.id == "res_a")).one()
    assert record.resource_state_id == "rst_a"
    assert state.quantity_value == Decimal("20.000")
    assert resource.version == 1
    assert event.event_type == "reservation.created"


def test_reservations_cannot_exceed_agreement_or_physical_quantity():
    client, token, _ = reservation_fixture()
    first = client.post(
        "/v1/reservations",
        json=payload("6.000"),
        headers=auth(token, "reservation-one"),
    )
    second = client.post(
        "/v1/reservations",
        json=payload("4.250"),
        headers=auth(token, "reservation-two"),
    )
    over_agreement = client.post(
        "/v1/reservations",
        json=payload("0.001"),
        headers=auth(token, "reservation-three"),
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert over_agreement.status_code == 422
    assert over_agreement.json()["error"]["code"] == "DOMAIN_VALIDATION_FAILED"


def test_reservation_rejects_stale_state_wrong_source_and_incompatible_unit():
    client, token, _ = reservation_fixture()
    stale = payload()
    stale["resource_state_version"] = 2
    response = client.post(
        "/v1/reservations",
        json=stale,
        headers=auth(token, "reservation-stale"),
    )
    assert response.status_code == 409

    wrong_state = payload()
    wrong_state["resource_state_id"] = "rst_other"
    response = client.post(
        "/v1/reservations",
        json=wrong_state,
        headers=auth(token, "reservation-wrong-state"),
    )
    assert response.status_code == 409

    wrong_unit = payload()
    wrong_unit["quantity_unit"] = "kg"
    response = client.post(
        "/v1/reservations",
        json=wrong_unit,
        headers=auth(token, "reservation-wrong-unit"),
    )
    assert response.status_code == 422


def test_release_is_versioned_and_frees_allocation():
    client, token, engine = reservation_fixture()
    created = client.post(
        "/v1/reservations",
        json=payload("10.000"),
        headers=auth(token, "reservation-for-release"),
    )
    assert created.status_code == 201, created.text
    reservation_id = created.json()["data"]["id"]
    released = client.patch(
        f"/v1/reservations/{reservation_id}",
        json={"status": "RELEASED"},
        headers=auth(token, "reservation-release") | {"If-Match": '"version-1"'},
    )
    assert released.status_code == 200, released.text
    assert released.json()["data"]["status"] == "RELEASED"
    assert released.json()["data"]["version"] == 2
    replacement = client.post(
        "/v1/reservations",
        json=payload("10.000"),
        headers=auth(token, "reservation-after-release"),
    )
    assert replacement.status_code == 201, replacement.text
    with engine.connect() as connection:
        statuses = connection.execute(select(Reservation.status)).scalars().all()
    assert statuses.count("RELEASED") == 1
    assert statuses.count("ACTIVE") == 1


def test_reservation_expiry_requires_scope_and_expiry_instant():
    client, token, engine = reservation_fixture()
    created = client.post(
        "/v1/reservations",
        json=payload(),
        headers=auth(token, "reservation-for-expiry"),
    )
    reservation_id = created.json()["data"]["id"]
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        key = session.scalar(select(APIKey).where(APIKey.id == "key_buyer"))
        key.scopes = ["reservations:read", "reservations:write"]
    denied = client.patch(
        f"/v1/reservations/{reservation_id}",
        json={"status": "EXPIRED"},
        headers=auth(token, "reservation-expire-denied") | {"If-Match": '"version-1"'},
    )
    assert denied.status_code == 403

    with factory.begin() as session:
        key = session.scalar(select(APIKey).where(APIKey.id == "key_buyer"))
        key.scopes = ["reservations:read", "reservations:write", "reservations:expire"]
    early = client.patch(
        f"/v1/reservations/{reservation_id}",
        json={"status": "EXPIRED"},
        headers=auth(token, "reservation-expire-early") | {"If-Match": '"version-1"'},
    )
    assert early.status_code == 409


def test_reservation_reads_are_tenant_scoped_and_require_scope():
    client, token, engine = reservation_fixture()
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        key = session.scalar(select(APIKey).where(APIKey.id == "key_buyer"))
        key.scopes = ["reservations:write"]
    denied = client.get("/v1/reservations", headers=auth(token))
    assert denied.status_code == 403

    with factory.begin() as session:
        key = session.scalar(select(APIKey).where(APIKey.id == "key_buyer"))
        key.scopes = ["reservations:read"]
    missing = client.get("/v1/reservations/rsv_other", headers=auth(token))
    assert missing.status_code == 404


def test_reserved_resource_state_cannot_be_physically_transitioned():
    client, token, _ = reservation_fixture()
    created = client.post(
        "/v1/reservations",
        json=payload("5.000"),
        headers=auth(token, "reservation-locks-state"),
    )
    assert created.status_code == 201, created.text
    transition = client.post(
        "/v1/resource-states/rst_a/transitions",
        json={
            "kind": "CORRECTION",
            "reason": "Attempted consumption while quantity is reserved",
            "occurred_at": (datetime.now(UTC) + timedelta(minutes=1)).isoformat(),
            "state_type": "ALUMINUM_INGOT",
            "quantity": {
                "value": "4.000",
                "unit": "t",
                "unit_registry_version": "CRR-UNITS-0.1",
            },
            "location_id": "loc_a",
            "provenance": {"source_type": "TEST"},
        },
        headers=auth(token, "resource-transition-blocked") | {"If-Match": '"version-1"'},
    )
    assert transition.status_code == 409
    assert transition.json()["error"]["code"] == "RESOURCE_STATE_RESERVED"


def test_active_transaction_locks_linked_reservation_from_release():
    client, token, engine = reservation_fixture()
    created = client.post(
        "/v1/reservations",
        json=payload("10.250"),
        headers=auth(token, "reservation-for-transaction"),
    )
    assert created.status_code == 201, created.text
    reservation_id = created.json()["data"]["id"]
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        session.add(
            Transaction(
                id="txn_a",
                organization_id="org_a",
                agreement_id="agr_a",
                offer_id="off_a",
                offer_version=2,
                opportunity_id="opp_a",
                opportunity_version=1,
                route_candidate_id="route_a",
                resource_id="res_a",
                resource_state_id="rst_a",
                resource_version=1,
                proposer_actor_id="act_seller",
                recipient_actor_id="act_buyer",
                quantity_value=Decimal("10.250"),
                quantity_unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                price=Decimal("125.50"),
                currency="SAR",
                terms_snapshot='{"quantity":{"value":"10.250","unit":"t"}}',
                status="AGREED",
                version=1,
                created_by="act_buyer",
                created_at=NOW,
                updated_at=NOW,
                provenance={"source_type": "TEST"},
            )
        )
        session.execute(
            transaction_reservations.insert().values(
                organization_id="org_a",
                transaction_id="txn_a",
                reservation_id=reservation_id,
            )
        )
    blocked = client.patch(
        f"/v1/reservations/{reservation_id}",
        json={"status": "RELEASED"},
        headers=auth(token, "reservation-release-blocked") | {"If-Match": '"version-1"'},
    )
    assert blocked.status_code == 409
    assert blocked.json()["error"]["code"] == "RESERVATION_BOUND_TO_TRANSACTION"


def create_full_transaction_reservations(client, token):
    first = client.post(
        "/v1/reservations",
        json=payload("4.000"),
        headers=auth(token, "transaction-reservation-first"),
    )
    second = client.post(
        "/v1/reservations",
        json=payload("6.250"),
        headers=auth(token, "transaction-reservation-second"),
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    return [first.json()["data"]["id"], second.json()["data"]["id"]]


def test_transaction_creation_is_idempotent_and_links_complete_reservation_set():
    client, token, engine = reservation_fixture()
    reservation_ids = create_full_transaction_reservations(client, token)
    body = {"agreement_id": "agr_a", "reservation_ids": reservation_ids}
    headers = auth(token, "transaction-create")
    created = client.post("/v1/transactions", json=body, headers=headers)
    replay = client.post("/v1/transactions", json=body, headers=headers)
    assert created.status_code == 201, created.text
    assert replay.status_code == 200
    duplicate = client.post(
        "/v1/transactions",
        json=body,
        headers=auth(token, "transaction-create-duplicate"),
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "TRANSACTION_ALREADY_EXISTS"
    conflicting_replay = client.post(
        "/v1/transactions",
        json={"agreement_id": "agr_a", "reservation_ids": [reservation_ids[0]]},
        headers=headers,
    )
    assert conflicting_replay.status_code == 409
    assert conflicting_replay.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"
    data = created.json()["data"]
    assert data["status"] == "AGREED"
    assert data["quantity"]["value"] == "10.250"
    assert set(data["reservation_ids"]) == set(reservation_ids)
    assert data["price"] == "125.50"
    assert data["offer_version"] == 2
    assert data["opportunity_version"] == 1
    detail = client.get(f"/v1/transactions/{data['id']}", headers=auth(token))
    collection = client.get("/v1/transactions", headers=auth(token))
    assert detail.status_code == 200
    assert collection.status_code == 200
    assert collection.json()["data"][0]["id"] == data["id"]
    with engine.connect() as connection:
        transaction = connection.execute(
            select(Transaction).where(Transaction.id == data["id"])
        ).one()
        linked = (
            connection.execute(
                select(transaction_reservations.c.reservation_id).where(
                    transaction_reservations.c.transaction_id == data["id"]
                )
            )
            .scalars()
            .all()
        )
        event = connection.execute(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == data["id"])
        ).one()
        state = connection.execute(select(ResourceState).where(ResourceState.id == "rst_a")).one()
    assert transaction.status == "AGREED"
    assert set(linked) == set(reservation_ids)
    assert event.event_type == "transaction.created"
    assert event.payload["offer_version"] == 2
    assert event.payload["opportunity_version"] == 1
    assert set(event.payload["reservation_ids"]) == set(reservation_ids)
    assert state.quantity_value == Decimal("20.000")


def test_transaction_creation_rejects_incomplete_reservation_coverage():
    client, token, _ = reservation_fixture()
    partial = client.post(
        "/v1/reservations",
        json=payload("6.000"),
        headers=auth(token, "transaction-reservation-partial"),
    )
    assert partial.status_code == 201, partial.text
    response = client.post(
        "/v1/transactions",
        json={"agreement_id": "agr_a", "reservation_ids": [partial.json()["data"]["id"]]},
        headers=auth(token, "transaction-incomplete"),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "DOMAIN_VALIDATION_FAILED"


def test_transaction_creation_requires_every_active_reservation():
    client, token, _ = reservation_fixture()
    reservation_ids = create_full_transaction_reservations(client, token)
    response = client.post(
        "/v1/transactions",
        json={"agreement_id": "agr_a", "reservation_ids": reservation_ids[:1]},
        headers=auth(token, "transaction-reservation-subset"),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RESERVATION_SET_MISMATCH"


def test_transaction_lifecycle_resolves_disputes_and_cancels_allocations_atomically():
    client, token, engine = reservation_fixture()
    reservation_ids = create_full_transaction_reservations(client, token)
    created = client.post(
        "/v1/transactions",
        json={"agreement_id": "agr_a", "reservation_ids": reservation_ids},
        headers=auth(token, "transaction-lifecycle-create"),
    )
    assert created.status_code == 201, created.text
    transaction_id = created.json()["data"]["id"]

    scheduled = client.patch(
        f"/v1/transactions/{transaction_id}",
        json={
            "status": "SCHEDULED",
            "scheduled_for": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
        },
        headers=auth(token, "transaction-schedule") | {"If-Match": '"version-1"'},
    )
    assert scheduled.status_code == 200, scheduled.text
    assert scheduled.json()["data"]["status"] == "SCHEDULED"

    disputed = client.patch(
        f"/v1/transactions/{transaction_id}",
        json={"status": "DISPUTED", "reason": "Delivery window requires review"},
        headers=auth(token, "transaction-dispute") | {"If-Match": '"version-2"'},
    )
    assert disputed.status_code == 200, disputed.text
    assert disputed.json()["data"]["status"] == "DISPUTED"

    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        key = session.scalar(select(APIKey).where(APIKey.id == "key_buyer"))
        key.scopes = [
            "reservations:read",
            "reservations:write",
            "transactions:read",
            "transactions:write",
        ]
    resolution_body = {
        "status": "SCHEDULED",
        "scheduled_for": (datetime.now(UTC) + timedelta(days=3)).isoformat(),
        "resolution_note": "Both participants accepted the revised date",
    }
    denied_resolution = client.patch(
        f"/v1/transactions/{transaction_id}",
        json=resolution_body,
        headers=auth(token, "transaction-resolve-denied") | {"If-Match": '"version-3"'},
    )
    assert denied_resolution.status_code == 403
    with factory.begin() as session:
        key = session.scalar(select(APIKey).where(APIKey.id == "key_buyer"))
        key.scopes = [
            "reservations:read",
            "reservations:write",
            "transactions:read",
            "transactions:write",
            "transactions:resolve",
        ]
    resolved = client.patch(
        f"/v1/transactions/{transaction_id}",
        json=resolution_body,
        headers=auth(token, "transaction-resolve") | {"If-Match": '"version-3"'},
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["data"]["status"] == "SCHEDULED"

    cancelled = client.patch(
        f"/v1/transactions/{transaction_id}",
        json={"status": "CANCELLED", "reason": "Mutual cancellation"},
        headers=auth(token, "transaction-cancel") | {"If-Match": '"version-4"'},
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["data"]["status"] == "CANCELLED"
    assert cancelled.json()["data"]["version"] == 5

    with engine.connect() as connection:
        reservation_statuses = (
            connection.execute(
                select(Reservation.status).where(Reservation.id.in_(reservation_ids))
            )
            .scalars()
            .all()
        )
        released_events = connection.execute(
            select(OutboxEvent).where(
                OutboxEvent.aggregate_type == "Reservation",
                OutboxEvent.aggregate_id.in_(reservation_ids),
                OutboxEvent.event_type == "reservation.released",
            )
        ).all()
        transaction_events = connection.execute(
            select(OutboxEvent).where(
                OutboxEvent.aggregate_type == "Transaction",
                OutboxEvent.aggregate_id == transaction_id,
            )
        ).all()
    assert reservation_statuses == ["RELEASED", "RELEASED"]
    assert len(released_events) == 2
    assert len(transaction_events) == 5
    blocked_new_reservation = client.post(
        "/v1/reservations",
        json=payload("1.000"),
        headers=auth(token, "reservation-after-transaction-cancel"),
    )
    assert blocked_new_reservation.status_code == 409
    assert blocked_new_reservation.json()["error"]["code"] == "AGREEMENT_ALREADY_TRANSACTED"


def create_scheduled_transaction(client, token, key_prefix="execution"):
    reservation_ids = create_full_transaction_reservations(client, token)
    created = client.post(
        "/v1/transactions",
        json={"agreement_id": "agr_a", "reservation_ids": reservation_ids},
        headers=auth(token, f"{key_prefix}-transaction"),
    )
    assert created.status_code == 201, created.text
    transaction_id = created.json()["data"]["id"]
    scheduled = client.patch(
        f"/v1/transactions/{transaction_id}",
        json={
            "status": "SCHEDULED",
            "scheduled_for": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
        },
        headers=auth(token, f"{key_prefix}-schedule") | {"If-Match": '"version-1"'},
    )
    assert scheduled.status_code == 200, scheduled.text
    return transaction_id


def test_execution_creation_and_reported_operations_are_idempotent_and_audited():
    client, token, engine = reservation_fixture()
    transaction_id = create_scheduled_transaction(client, token)
    body = {"transaction_id": transaction_id}
    headers = auth(token, "execution-create")
    created = client.post("/v1/executions", json=body, headers=headers)
    replay = client.post("/v1/executions", json=body, headers=headers)
    assert created.status_code == 201, created.text
    assert replay.status_code == 200
    data = created.json()["data"]
    execution_id = data["id"]
    assert data["status"] == "PLANNED"
    assert data["resource_state_id"] == "rst_a"
    assert data["quantity"]["value"] == "10.250"
    assert created.headers["etag"] == '"version-1"'

    planned_for = datetime.now(UTC) + timedelta(days=1)
    planned = client.post(
        f"/v1/executions/{execution_id}/operations/planned",
        json={"operation_type": "PICKUP", "planned_for": planned_for.isoformat()},
        headers=auth(token, "execution-plan") | {"If-Match": '"version-1"'},
    )
    assert planned.status_code == 201, planned.text
    plan = planned.json()["data"]["operations"][0]
    assert plan["mode"] == "PLANNED"
    assert plan["occurred_at"] is None

    occurred_at = datetime.now(UTC) + timedelta(minutes=1)
    reported_body = {
        "planned_operation_id": plan["id"],
        "occurred_at": occurred_at.isoformat(),
        "quantity_value": "4.000",
        "quantity_unit": "t",
        "unit_registry_version": "CRR-UNITS-0.1",
    }
    reported_headers = auth(token, "execution-report") | {"If-Match": '"version-2"'}
    reported = client.post(
        f"/v1/executions/{execution_id}/operations/reported",
        json=reported_body,
        headers=reported_headers,
    )
    replayed_report = client.post(
        f"/v1/executions/{execution_id}/operations/reported",
        json=reported_body,
        headers=reported_headers,
    )
    assert reported.status_code == 201, reported.text
    assert replayed_report.status_code == 200
    detail = client.get(f"/v1/executions/{execution_id}", headers=auth(token))
    collection = client.get("/v1/executions", headers=auth(token))
    assert detail.status_code == 200
    assert collection.status_code == 200
    result = detail.json()["data"]
    assert result["status"] == "IN_PROGRESS"
    assert len(result["operations"]) == 2
    assert result["operations"][1]["mode"] == "REPORTED"
    assert result["operations"][1]["quantity"]["value"] == "4.000"

    with engine.connect() as connection:
        state = connection.execute(select(ResourceState).where(ResourceState.id == "rst_a")).one()
        events = connection.execute(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == execution_id)
        ).all()
    assert state.quantity_value == Decimal("20.000")
    assert state.resource_version == 1
    assert len(events) == 3
    assert {event.event_type for event in events} == {
        "execution.created",
        "execution.operation.planned",
        "execution.operation.reported",
    }


def test_execution_rejects_unplanned_duplicate_out_of_order_and_stale_reports():
    client, token, _ = reservation_fixture()
    transaction_id = create_scheduled_transaction(client, token, "execution-validation")
    created = client.post(
        "/v1/executions",
        json={"transaction_id": transaction_id},
        headers=auth(token, "execution-validation-create"),
    )
    execution_id = created.json()["data"]["id"]
    no_plan = client.post(
        f"/v1/executions/{execution_id}/operations/reported",
        json={
            "planned_operation_id": "missing",
            "occurred_at": datetime.now(UTC).isoformat(),
        },
        headers=auth(token, "execution-no-plan") | {"If-Match": '"version-1"'},
    )
    assert no_plan.status_code == 404

    shipment_plan = client.post(
        f"/v1/executions/{execution_id}/operations/planned",
        json={
            "operation_type": "SHIPMENT",
            "planned_for": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        },
        headers=auth(token, "execution-shipment-plan") | {"If-Match": '"version-1"'},
    )
    assert shipment_plan.status_code == 201
    plan_id = shipment_plan.json()["data"]["operations"][0]["id"]
    shipment = client.post(
        f"/v1/executions/{execution_id}/operations/reported",
        json={
            "planned_operation_id": plan_id,
            "occurred_at": datetime.now(UTC).isoformat(),
        },
        headers=auth(token, "execution-shipment-report") | {"If-Match": '"version-2"'},
    )
    assert shipment.status_code == 409
    assert shipment.json()["error"]["code"] == "DOMAIN_VALIDATION_FAILED"

    pickup_plan = client.post(
        f"/v1/executions/{execution_id}/operations/planned",
        json={
            "operation_type": "PICKUP",
            "planned_for": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        },
        headers=auth(token, "execution-pickup-plan") | {"If-Match": '"version-2"'},
    )
    assert pickup_plan.status_code == 201
    stale = client.post(
        f"/v1/executions/{execution_id}/operations/reported",
        json={
            "planned_operation_id": pickup_plan.json()["data"]["operations"][-1]["id"],
            "occurred_at": datetime.now(UTC).isoformat(),
        },
        headers=auth(token, "execution-stale-report") | {"If-Match": '"version-1"'},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "STALE_VERSION"


def test_execution_exceptions_and_corrections_are_append_only_and_authorized():
    client, token, _ = reservation_fixture()
    transaction_id = create_scheduled_transaction(client, token, "execution-history")
    created = client.post(
        "/v1/executions",
        json={"transaction_id": transaction_id},
        headers=auth(token, "execution-history-create"),
    )
    execution_id = created.json()["data"]["id"]
    plan = client.post(
        f"/v1/executions/{execution_id}/operations/planned",
        json={
            "operation_type": "PICKUP",
            "planned_for": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        },
        headers=auth(token, "execution-history-plan") | {"If-Match": '"version-1"'},
    )
    plan_id = plan.json()["data"]["operations"][0]["id"]
    actual = client.post(
        f"/v1/executions/{execution_id}/operations/reported",
        json={
            "planned_operation_id": plan_id,
            "occurred_at": datetime.now(UTC).isoformat(),
            "quantity_value": "3.000",
            "quantity_unit": "t",
            "unit_registry_version": "CRR-UNITS-0.1",
        },
        headers=auth(token, "execution-history-actual") | {"If-Match": '"version-2"'},
    )
    assert actual.status_code == 201, actual.text
    original = actual.json()["data"]["operations"][-1]

    exception = client.post(
        f"/v1/executions/{execution_id}/exceptions",
        json={"code": "VEHICLE_DELAY", "reason": "Vehicle delayed at source"},
        headers=auth(token, "execution-history-exception") | {"If-Match": '"version-3"'},
    )
    assert exception.status_code == 201, exception.text
    exception_id = exception.json()["data"]["exceptions"][0]["id"]
    assert exception.json()["data"]["status"] == "EXCEPTION"

    resolved = client.post(
        f"/v1/executions/{execution_id}/exceptions/{exception_id}/resolution",
        json={"reason": "Replacement vehicle assigned"},
        headers=auth(token, "execution-history-resolution") | {"If-Match": '"version-4"'},
    )
    assert resolved.status_code == 201, resolved.text
    assert resolved.json()["data"]["status"] == "IN_PROGRESS"

    correction = client.post(
        f"/v1/executions/{execution_id}/corrections",
        json={
            "original_operation_id": original["id"],
            "occurred_at": (datetime.now(UTC) + timedelta(minutes=2)).isoformat(),
            "reason": "Corrected measured quantity from signed scale ticket",
            "quantity_value": "3.250",
            "quantity_unit": "t",
            "unit_registry_version": "CRR-UNITS-0.1",
        },
        headers=auth(token, "execution-history-correction") | {"If-Match": '"version-5"'},
    )
    assert correction.status_code == 201, correction.text
    operations = correction.json()["data"]["operations"]
    assert len(operations) == 3
    assert operations[1]["id"] == original["id"]
    assert operations[2]["supersedes_operation_id"] == original["id"]
    assert operations[2]["correction_reason"] == (
        "Corrected measured quantity from signed scale ticket"
    )


def test_execution_close_is_operational_not_verified_and_cancel_is_pre_execution_only():
    client, token, engine = reservation_fixture()
    transaction_id = create_scheduled_transaction(client, token, "execution-close")
    created = client.post(
        "/v1/executions",
        json={"transaction_id": transaction_id},
        headers=auth(token, "execution-close-create"),
    )
    execution_id = created.json()["data"]["id"]
    plan = client.post(
        f"/v1/executions/{execution_id}/operations/planned",
        json={
            "operation_type": "PICKUP",
            "planned_for": (datetime.now(UTC) + timedelta(days=1)).isoformat(),
        },
        headers=auth(token, "execution-close-plan") | {"If-Match": '"version-1"'},
    )
    plan_id = plan.json()["data"]["operations"][0]["id"]
    reported = client.post(
        f"/v1/executions/{execution_id}/operations/reported",
        json={
            "planned_operation_id": plan_id,
            "occurred_at": datetime.now(UTC).isoformat(),
        },
        headers=auth(token, "execution-close-report") | {"If-Match": '"version-2"'},
    )
    assert reported.status_code == 201, reported.text
    closed = client.post(
        f"/v1/executions/{execution_id}/close",
        json={"reason": "Operational handling completed at the facility"},
        headers=auth(token, "execution-close-finalize") | {"If-Match": '"version-3"'},
    )
    assert closed.status_code == 200, closed.text
    assert closed.json()["data"]["status"] == "CLOSED"
    assert closed.json()["data"]["provenance"]["verification_status"] == "NOT_VERIFIED"

    blocked_plan = client.post(
        f"/v1/executions/{execution_id}/operations/planned",
        json={
            "operation_type": "DELIVERY",
            "planned_for": (datetime.now(UTC) + timedelta(days=2)).isoformat(),
        },
        headers=auth(token, "execution-after-close") | {"If-Match": '"version-4"'},
    )
    assert blocked_plan.status_code == 409

    cancel_transaction = create_scheduled_transaction(client, token, "execution-cancel")
    planned_execution = client.post(
        "/v1/executions",
        json={"transaction_id": cancel_transaction},
        headers=auth(token, "execution-cancel-create"),
    )
    cancel_id = planned_execution.json()["data"]["id"]
    cancelled = client.post(
        f"/v1/executions/{cancel_id}/cancel",
        json={"reason": "Parties cancelled before physical work began"},
        headers=auth(token, "execution-cancel-finalize") | {"If-Match": '"version-1"'},
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["data"]["status"] == "CANCELLED"

    with engine.connect() as connection:
        state = connection.execute(select(ResourceState).where(ResourceState.id == "rst_a")).one()
    assert state.quantity_value == Decimal("20.000")
    assert state.resource_version == 1


def test_execution_create_requires_scheduled_transaction_and_scope():
    client, token, _ = reservation_fixture()
    reservation_ids = create_full_transaction_reservations(client, token)
    created = client.post(
        "/v1/transactions",
        json={"agreement_id": "agr_a", "reservation_ids": reservation_ids},
        headers=auth(token, "execution-unscheduled-transaction"),
    )
    assert created.status_code == 201
    transaction_id = created.json()["data"]["id"]
    unscheduled = client.post(
        "/v1/executions",
        json={"transaction_id": transaction_id},
        headers=auth(token, "execution-unscheduled-create"),
    )
    assert unscheduled.status_code == 409
    assert unscheduled.json()["error"]["code"] == "TRANSACTION_NOT_SCHEDULED"
