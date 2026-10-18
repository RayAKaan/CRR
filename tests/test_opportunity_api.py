from datetime import UTC, datetime
from hashlib import sha256

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.api import create_app
from crr.demand_model import Demand
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
        session.add(
            Actor(
                id=f"act_{org_id}",
                organization_id=org_id,
                name="Commercial",
                role="ORG_ADMIN",
                active=True,
                created_at=NOW,
            )
        )
        session.add(
            Location(
                id=f"loc_{org_id}",
                organization_id=org_id,
                name="Factory",
                address="Test",
                latitude=None,
                longitude=None,
                jurisdiction="SA-RYD",
                provenance={"source_type": "TEST"},
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


def seed_direct(engine, org_id: str = "org_a") -> None:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        session.add(
            Resource(
                id=f"res_{org_id}",
                organization_id=org_id,
                resource_type="ALUMINUM_SCRAP",
                description=None,
                version=1,
                created_by=f"act_{org_id}",
                provenance={"source_type": "TEST"},
                created_at=NOW,
            )
        )
        session.add(
            ResourceState(
                id=f"rst_{org_id}",
                organization_id=org_id,
                resource_id=f"res_{org_id}",
                resource_version=1,
                state_type="ALUMINUM_SCRAP",
                quantity_value="100.000",
                unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                location_id=f"loc_{org_id}",
                effective_at=NOW,
                recorded_at=NOW,
                created_by=f"act_{org_id}",
                provenance={"source_type": "TEST"},
                quality={},
                physical_properties={},
                predecessor_state_ids=[],
            )
        )
        session.add(
            Demand(
                id=f"dem_{org_id}",
                organization_id=org_id,
                required_state="ALUMINUM_SCRAP",
                quantity_min_value="10.000",
                quantity_target_value="20.000",
                quantity_max_value="30.000",
                remaining_quantity_value="20.000",
                unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                status="ACTIVE",
                location_constraints={},
                timing_start=NOW,
                timing_end=datetime(2030, 1, 1, tzinfo=UTC),
                quality_requirements={},
                pricing_constraints={},
                certifications=[],
                regulatory_constraints={},
                substitutions=[],
                recurrence={},
                version=1,
                created_by=f"act_{org_id}",
                provenance={"source_type": "TEST"},
                created_at=NOW,
                updated_at=NOW,
            )
        )


def route_provenance(client: TestClient, token: str, org_id: str = "org_a"):
    response = client.post(
        "/v1/routes/compute",
        headers=auth(token),
        json={
            "source_resource_state_id": f"rst_{org_id}",
            "target_demand_id": f"dem_{org_id}",
            "optimization": {
                "policy_id": "policy-duration",
                "policy_version": 1,
                "objective": "MIN_DURATION",
                "calculation_version": "1",
                "allow_negative": False,
            },
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["optimization"]["ranked"]
    return data["candidates"][0], data["optimization"]["candidate_set_fingerprint"]


def opportunity_payload(candidate: dict, fingerprint: str, org_id: str = "org_a") -> dict:
    return {
        "id": f"opp_{org_id}",
        "route_candidate": candidate,
        "candidate_set_fingerprint": fingerprint,
        "source_resource_state_id": f"rst_{org_id}",
        "target_demand_id": f"dem_{org_id}",
        "valid_from": "2026-10-18T12:00:00Z",
        "valid_until": "2029-12-31T23:59:59Z",
        "quantity_value": "20.000",
        "quantity_unit": "t",
        "unit_registry_version": "CRR-UNITS-0.1",
        "provenance": {"source_type": "ROUTE_CONVERSION_TEST"},
        "status": "OPEN",
    }


def test_create_get_and_idempotently_replay_opportunity():
    client, token, engine = make_client(
        scopes=["routes:compute", "opportunities:write", "opportunities:read"]
    )
    seed_direct(engine)
    candidate, fingerprint = route_provenance(client, token)
    headers = auth(token) | {"Idempotency-Key": "opp-create-1"}
    payload = opportunity_payload(candidate, fingerprint)

    created = client.post("/v1/opportunities", json=payload, headers=headers)
    replay = client.post("/v1/opportunities", json=payload, headers=headers)
    fetched = client.get("/v1/opportunities/opp_org_a", headers=auth(token))

    assert created.status_code == 201, created.text
    assert replay.status_code == 200
    assert fetched.status_code == 200
    assert fetched.json()["data"]["status"] == "OPEN"

    with engine.connect() as connection:
        event = connection.execute(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == "opp_org_a")
        ).one()
    assert event.event_type == "opportunity.created"


def test_opportunity_requires_least_privilege_scope():
    client, token, engine = make_client(scopes=["opportunities:read"])
    seed_direct(engine)
    response = client.post(
        "/v1/opportunities",
        json={"source_resource_state_id": "rst_org_a"},
        headers=auth(token) | {"Idempotency-Key": "opp-scope"},
    )
    assert response.status_code == 403


def test_opportunity_rejects_tampered_candidate_set_and_stale_source():
    client, token, engine = make_client(
        scopes=["routes:compute", "opportunities:write", "opportunities:read"]
    )
    seed_direct(engine)
    candidate, fingerprint = route_provenance(client, token)
    payload = opportunity_payload(candidate, fingerprint)
    payload["candidate_set_fingerprint"] = "b" * 64
    tampered = client.post(
        "/v1/opportunities",
        json=payload,
        headers=auth(token) | {"Idempotency-Key": "opp-tampered"},
    )
    assert tampered.status_code == 409

    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        state = session.scalar(select(ResourceState).where(ResourceState.id == "rst_org_a"))
        state.resource_version = 2

    stale = client.post(
        "/v1/opportunities",
        json=opportunity_payload(candidate, fingerprint),
        headers=auth(token) | {"Idempotency-Key": "opp-stale"},
    )
    assert stale.status_code == 409
    assert stale.json()["error"]["code"] == "ROUTE_STALE"


def test_opportunity_lifecycle_uses_etag_and_rejects_illegal_transition():
    client, token, engine = make_client(
        scopes=["routes:compute", "opportunities:write", "opportunities:read"]
    )
    seed_direct(engine)
    candidate, fingerprint = route_provenance(client, token)
    create = client.post(
        "/v1/opportunities",
        json=opportunity_payload(candidate, fingerprint),
        headers=auth(token) | {"Idempotency-Key": "opp-lifecycle"},
    )
    assert create.status_code == 201

    transitioned = client.patch(
        "/v1/opportunities/opp_org_a",
        json={"status": "CLOSED"},
        headers=auth(token)
        | {"Idempotency-Key": "opp-close", "If-Match": '"version-1"'},
    )
    assert transitioned.status_code == 200
    assert transitioned.headers["etag"] == '"version-2"'

    illegal = client.patch(
        "/v1/opportunities/opp_org_a",
        json={"status": "OPEN"},
        headers=auth(token)
        | {"Idempotency-Key": "opp-reopen", "If-Match": '"version-2"'},
    )
    assert illegal.status_code == 409


def test_cross_tenant_opportunity_is_hidden():
    client_a, token_a, engine = make_client(
        org_id="org_a", scopes=["routes:compute", "opportunities:write", "opportunities:read"]
    )
    seed_direct(engine, "org_a")
    candidate, fingerprint = route_provenance(client_a, token_a)
    created = client_a.post(
        "/v1/opportunities",
        json=opportunity_payload(candidate, fingerprint),
        headers=auth(token_a) | {"Idempotency-Key": "opp-tenant-a"},
    )
    assert created.status_code == 201

    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        session.add(Organization(id="org_b", name="B", status="ACTIVE", created_at=NOW))
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
                secret_hash=sha256(b"other-secret").hexdigest(),
                scopes=["opportunities:read"],
                revoked=False,
                created_at=NOW,
            )
        )

    client_b = TestClient(create_app(factory))
    response = client_b.get("/v1/opportunities/opp_org_a", headers=auth("other-secret"))
    assert response.status_code == 404

    with factory() as session:
        assert (
            session.scalar(select(Opportunity).where(Opportunity.id == "opp_org_a"))
            is not None
        )
