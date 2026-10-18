from datetime import UTC, datetime
from hashlib import sha256

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.api import create_app
from crr.models import Actor, APIKey, Base, Organization, OutboxEvent
from crr.opportunity_model import Opportunity

NOW = datetime(2026, 10, 18, 12, tzinfo=UTC)


def make_client(org_id: str = "org_a", scopes: list[str] | None = None):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    token = "test-secret"
    with factory.begin() as session:
        session.add(Organization(id=org_id, name="Factory", status="ACTIVE", created_at=NOW))
        session.add_all(
            [
                Actor(
                    id=f"act_{org_id}_proposer",
                    organization_id=org_id,
                    name="Proposer",
                    role="ORG_ADMIN",
                    active=True,
                    created_at=NOW,
                ),
                Actor(
                    id=f"act_{org_id}_recipient",
                    organization_id=org_id,
                    name="Recipient",
                    role="ORG_ADMIN",
                    active=True,
                    created_at=NOW,
                ),
            ]
        )
        session.add(
            APIKey(
                id=f"key_{org_id}",
                organization_id=org_id,
                actor_id=f"act_{org_id}_proposer",
                secret_hash=sha256(token.encode()).hexdigest(),
                scopes=scopes or ["admin:*"],
                revoked=False,
                created_at=NOW,
            )
        )
    return TestClient(create_app(factory)), token, engine


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def seed_opportunity(engine, org_id: str = "org_a") -> None:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        session.add(
            Opportunity(
                id=f"opp_{org_id}",
                organization_id=org_id,
                route_candidate_id=f"route_{org_id}",
                candidate_set_fingerprint="a" * 64,
                source_resource_state_id=f"rst_{org_id}",
                source_resource_state_version=1,
                target_demand_id=f"dem_{org_id}",
                target_demand_version=1,
                route_provenance={"candidate_id": f"route_{org_id}"},
                advisory_provenance=None,
                economic_model_id=None,
                economic_model_version=None,
                commercial_perspective=None,
                currency="USD",
                quantity_value="20.000",
                quantity_unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                valid_from=NOW,
                valid_until=datetime(2027, 1, 1, tzinfo=UTC),
                status="OPEN",
                version=1,
                created_by=f"act_{org_id}_proposer",
                provenance={"source_type": "TEST"},
                created_at=NOW,
                updated_at=NOW,
            )
        )


def offer_payload(org_id: str = "org_a") -> dict:
    return {
        "id": f"off_{org_id}",
        "opportunity_id": f"opp_{org_id}",
        "opportunity_version": 1,
        "proposer_actor_id": f"act_{org_id}_proposer",
        "recipient_actor_id": f"act_{org_id}_recipient",
        "quantity_value": "10.000",
        "quantity_unit": "t",
        "unit_registry_version": "CRR-UNITS-0.1",
        "price": "125.50",
        "currency": "USD",
        "delivery_terms": {"incoterm": "DAP"},
        "timing_terms": {"delivery": "2026-12"},
        "route_assumptions": {"opportunity_version": 1},
        "conditions": {"inspection": "required"},
        "valid_from": "2026-10-18T12:00:00Z",
        "valid_until": "2026-12-15T23:59:59Z",
        "provenance": {"source_type": "TEST"},
        "status": "OPEN",
    }


def test_offer_create_get_and_idempotent_replay():
    client, token, engine = make_client(scopes=["offers:write", "offers:read"])
    seed_opportunity(engine)
    headers = auth(token) | {"Idempotency-Key": "offer-create"}
    payload = offer_payload()

    created = client.post("/v1/offers", json=payload, headers=headers)
    replay = client.post("/v1/offers", json=payload, headers=headers)
    fetched = client.get("/v1/offers/off_org_a", headers=auth(token))

    assert created.status_code == 201, created.text
    assert replay.status_code == 200
    assert fetched.status_code == 200
    assert fetched.json()["data"]["price"] == "125.50"

    with engine.connect() as connection:
        event = connection.execute(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == "off_org_a")
        ).one()
    assert event.event_type == "offer.created"


def test_offer_requires_least_privilege_and_authentic_proposer():
    client, token, engine = make_client(scopes=["offers:read"])
    seed_opportunity(engine)
    response = client.post(
        "/v1/offers",
        json=offer_payload(),
        headers=auth(token) | {"Idempotency-Key": "offer-scope"},
    )
    assert response.status_code == 403


def test_offer_rejects_stale_opportunity_and_over_broad_window():
    client, token, engine = make_client(scopes=["offers:write"])
    seed_opportunity(engine)
    payload = offer_payload()
    payload["opportunity_version"] = 2
    stale = client.post(
        "/v1/offers",
        json=payload,
        headers=auth(token) | {"Idempotency-Key": "offer-stale"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "OPPORTUNITY_STALE"

    payload = offer_payload()
    payload["valid_until"] = "2027-01-01T00:00:01Z"
    broad = client.post(
        "/v1/offers",
        json=payload,
        headers=auth(token) | {"Idempotency-Key": "offer-window"},
    )
    assert broad.status_code == 422


def test_offer_lifecycle_requires_etag_and_rejects_terminal_reopen():
    client, token, engine = make_client(scopes=["offers:write", "offers:read"])
    seed_opportunity(engine)
    create = client.post(
        "/v1/offers",
        json=offer_payload(),
        headers=auth(token) | {"Idempotency-Key": "offer-life"},
    )
    assert create.status_code == 201

    opened = client.patch(
        "/v1/offers/off_org_a",
        json={"status": "OPEN"},
        headers=auth(token) | {"Idempotency-Key": "offer-open", "If-Match": '"version-1"'},
    )
    assert opened.status_code == 200
    accepted = client.patch(
        "/v1/offers/off_org_a",
        json={"status": "ACCEPTED"},
        headers=auth(token) | {"Idempotency-Key": "offer-accept", "If-Match": '"version-2"'},
    )
    assert accepted.status_code == 200
    illegal = client.patch(
        "/v1/offers/off_org_a",
        json={"status": "OPEN"},
        headers=auth(token) | {"Idempotency-Key": "offer-reopen", "If-Match": '"version-3"'},
    )
    assert illegal.status_code == 409


def test_offer_rejects_cross_tenant_participant_reference():
    client, token, engine = make_client(scopes=["offers:write"])
    seed_opportunity(engine)
    payload = offer_payload()
    payload["recipient_actor_id"] = "act_other_recipient"
    response = client.post(
        "/v1/offers",
        json=payload,
        headers=auth(token) | {"Idempotency-Key": "offer-cross-tenant"},
    )
    assert response.status_code == 404


def test_offer_does_not_mutate_opportunity():
    client, token, engine = make_client(scopes=["offers:write"])
    seed_opportunity(engine)
    client.post(
        "/v1/offers",
        json=offer_payload(),
        headers=auth(token) | {"Idempotency-Key": "offer-immutability"},
    )
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        opportunity = session.scalar(select(Opportunity).where(Opportunity.id == "opp_org_a"))
        assert opportunity.version == 1
        assert opportunity.status == "OPEN"
