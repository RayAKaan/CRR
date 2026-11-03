from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.agreement_model import Agreement
from crr.api import create_app
from crr.models import Actor, APIKey, Base, Organization, OutboxEvent
from crr.offer_model import Offer
from crr.opportunity_model import Opportunity

NOW = datetime(2026, 11, 3, 0, tzinfo=UTC)


def client_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    token = "buyer-secret"
    with factory.begin() as session:
        session.add(
            Organization(
                id="org_a",
                name="Factory",
                status="ACTIVE",
                created_at=NOW,
            )
        )
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
                scopes=["agreements:read", "agreements:write"],
                revoked=False,
                created_at=NOW,
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
                conditions={"inspection": "required"},
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
            OutboxEvent(
                id="evt_offer_accepted",
                event_type="offer.updated",
                event_version=1,
                aggregate_type="Offer",
                aggregate_id="off_a",
                aggregate_version=2,
                organization_id="org_a",
                actor_id="act_buyer",
                occurred_at=NOW,
                published_at=None,
                correlation_id="corr_accept",
                causation_id=None,
                idempotency_key="offer-accept",
                payload={"status": "ACCEPTED"},
                provenance={"source_type": "TEST"},
                schema_version="0.1",
            )
        )
    return TestClient(create_app(factory)), token, engine


def headers(token: str, key: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}", "Idempotency-Key": key}


def test_create_agreement_is_idempotent_and_snapshots_accepted_terms():
    client, token, engine = client_fixture()
    request_headers = headers(token, "agreement-create")
    created = client.post(
        "/v1/agreements",
        json={"offer_id": "off_a"},
        headers=request_headers,
    )
    replay = client.post(
        "/v1/agreements",
        json={"offer_id": "off_a"},
        headers=request_headers,
    )
    assert created.status_code == 201, created.text
    assert replay.status_code == 200
    data = created.json()["data"]
    assert data["accepted_by"] == "act_buyer"
    assert data["terms"]["price"] == "125.50"
    with engine.connect() as connection:
        agreement = connection.execute(select(Agreement).where(Agreement.id == data["id"])).one()
        event = connection.execute(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == data["id"])
        ).one()
    assert agreement.offer_version == 2
    assert event.event_type == "agreement.created"


def test_agreement_lifecycle_requires_etag_and_is_versioned():
    client, token, _ = client_fixture()
    created = client.post(
        "/v1/agreements",
        json={"offer_id": "off_a"},
        headers=headers(token, "agreement-create"),
    )
    assert created.status_code == 201, created.text
    agreement_id = created.json()["data"]["id"]
    response = client.patch(
        f"/v1/agreements/{agreement_id}",
        json={"status": "CANCELLED"},
        headers=headers(token, "agreement-cancel") | {"If-Match": '"version-1"'},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "CANCELLED"


def test_agreement_expiry_requires_dedicated_scope():
    client, token, engine = client_fixture()
    created = client.post(
        "/v1/agreements",
        json={"offer_id": "off_a"},
        headers=headers(token, "agreement-create-for-expiry"),
    )
    assert created.status_code == 201, created.text
    agreement_id = created.json()["data"]["id"]
    denied = client.patch(
        f"/v1/agreements/{agreement_id}",
        json={"status": "EXPIRED"},
        headers=headers(token, "agreement-expiry-denied")
        | {"If-Match": '"version-1"'},
    )
    assert denied.status_code == 403

    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        key = session.scalar(select(APIKey).where(APIKey.id == "key_buyer"))
        key.scopes = ["agreements:read", "agreements:write", "agreements:expire"]

    expired = client.patch(
        f"/v1/agreements/{agreement_id}",
        json={"status": "EXPIRED"},
        headers=headers(token, "agreement-expiry")
        | {"If-Match": '"version-1"'},
    )
    assert expired.status_code == 200
    assert expired.json()["data"]["status"] == "EXPIRED"
