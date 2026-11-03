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
    created = client.post("/v1/reservations", json=payload(), headers=headers)
    replay = client.post("/v1/reservations", json=payload(), headers=headers)
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
        state = connection.execute(
            select(ResourceState).where(ResourceState.id == "rst_a")
        ).one()
        resource = connection.execute(
            select(Resource).where(Resource.id == "res_a")
        ).one()
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
            "kind": "PHYSICAL_CHANGE",
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
