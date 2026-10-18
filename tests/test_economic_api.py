from datetime import UTC, datetime
from hashlib import sha256

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.api import create_app
from crr.models import Actor, APIKey, Base, Organization, OutboxEvent

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
        session.add(
            Actor(
                id=f"act_{org_id}",
                organization_id=org_id,
                name="Economist",
                role="ORG_ADMIN",
                active=True,
                created_at=NOW,
            )
        )
        session.add(
            APIKey(
                id=f"key_{org_id}",
                organization_id=org_id,
                actor_id=f"act_{org_id}",
                secret_hash=sha256(token.encode()).hexdigest(),
                scopes=scopes or ["admin:*"],
                revoked=False,
                created_at=NOW,
            )
        )
    return TestClient(create_app(factory)), token, engine


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def payload(model_id: str = "eco_1") -> dict:
    return {
        "id": model_id,
        "model_key": "standard-route",
        "version": 1,
        "currency": "SAR",
        "valid_from": "2026-10-18T00:00:00Z",
        "valid_until": "2026-12-31T23:59:59Z",
        "calculation_version": "1",
        "rounding": {"mode": "HALF_EVEN", "scale": 2},
        "components": [
            {
                "perspective": "SUPPLIER",
                "kind": "VALUE",
                "label": "sale value",
                "amount": "100.00",
                "source": "contract",
            },
            {
                "perspective": "SUPPLIER",
                "kind": "COST",
                "label": "transport",
                "amount": "120.00",
                "source": "tariff",
            },
        ],
        "status": "ACTIVE",
        "provenance": {"source_type": "TEST"},
    }


def test_create_and_get_economic_model():
    client, token, _ = make_client(scopes=["economic_models:write", "economic_models:read"])
    headers = auth(token) | {"Idempotency-Key": "eco-create-1"}

    created = client.post("/v1/economic-models", json=payload(), headers=headers)
    assert created.status_code == 201
    assert created.json()["data"]["currency"] == "SAR"
    assert created.headers["etag"] == '"version-1"'

    fetched = client.get("/v1/economic-models/eco_1", headers=auth(token))
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == "eco_1"


def test_create_requires_economic_write_scope():
    client, token, _ = make_client(scopes=["economic_models:read"])
    response = client.post(
        "/v1/economic-models",
        json=payload(),
        headers=auth(token) | {"Idempotency-Key": "eco-create-2"},
    )
    assert response.status_code == 403


def test_idempotent_create_replays_and_conflicting_payload_is_rejected():
    client, token, _ = make_client(scopes=["economic_models:write"])
    headers = auth(token) | {"Idempotency-Key": "eco-create-3"}

    first = client.post("/v1/economic-models", json=payload(), headers=headers)
    replay = client.post("/v1/economic-models", json=payload(), headers=headers)
    changed = client.post(
        "/v1/economic-models",
        json=payload(model_id="eco_changed"),
        headers=headers,
    )

    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == "eco_1"
    assert changed.status_code == 409


def test_cross_tenant_model_is_not_readable():
    client_a, token_a, engine = make_client(
        org_id="org_a", scopes=["economic_models:write", "economic_models:read"]
    )
    created = client_a.post(
        "/v1/economic-models",
        json=payload(),
        headers=auth(token_a) | {"Idempotency-Key": "eco-tenant-a"},
    )
    assert created.status_code == 201

    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        session.add(Organization(id="org_b", name="Factory B", status="ACTIVE", created_at=NOW))
        session.add(
            Actor(
                id="act_org_b",
                organization_id="org_b",
                name="Other",
                role="ORG_ADMIN",
                active=True,
                created_at=NOW,
            )
        )
        session.add(
            APIKey(
                id="key_org_b",
                organization_id="org_b",
                actor_id="act_org_b",
                secret_hash=sha256("other-secret".encode()).hexdigest(),
                scopes=["economic_models:read"],
                revoked=False,
                created_at=NOW,
            )
        )

    client_b = TestClient(create_app(factory))
    response = client_b.get(
        "/v1/economic-models/eco_1",
        headers=auth("other-secret"),
    )
    assert response.status_code == 404


def test_model_creation_emits_one_outbox_event():
    client, token, engine = make_client(scopes=["economic_models:write"])
    response = client.post(
        "/v1/economic-models",
        json=payload(),
        headers=auth(token) | {"Idempotency-Key": "eco-event-1"},
    )
    assert response.status_code == 201

    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory() as session:
        events = session.query(OutboxEvent).filter_by(aggregate_id="eco_1").all()
        assert len(events) == 1
        assert events[0].event_type == "economic_model.created"
