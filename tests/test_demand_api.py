from datetime import UTC, datetime
from hashlib import sha256

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.api import create_app
from crr.models import Actor, APIKey, Base, IdempotencyRecord, Organization, OutboxEvent


def make_client(org_id: str = "org_a", scopes: list[str] | None = None):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    token = "test-secret"
    now = datetime.now(UTC)
    with factory.begin() as session:
        session.add(Organization(id=org_id, name="Factory A", status="ACTIVE", created_at=now))
        session.add(
            Actor(
                id=f"act_{org_id}",
                organization_id=org_id,
                name="Admin",
                role="ORG_ADMIN",
                active=True,
                created_at=now,
            )
        )
        session.add(
            APIKey(
                id=f"key_{org_id}",
                organization_id=org_id,
                actor_id=f"act_{org_id}",
                secret_hash=sha256(token.encode()).hexdigest(),
                scopes=scopes or ["admin:*"] ,
                revoked=False,
                created_at=now,
            )
        )
    return TestClient(create_app(factory)), token, engine


def headers(token: str, key: str | None = None) -> dict[str, str]:
    result = {"Authorization": f"Bearer {token}"}
    if key:
        result["Idempotency-Key"] = key
    return result


DEMAND = {
    "required_state": "ALUMINUM_SCRAP",
    "quantity_min": "10.000",
    "quantity_target": "25.000",
    "quantity_max": "30.000",
    "unit": "t",
    "unit_registry_version": "CRR-UNITS-0.1",
    "location_constraints": {"jurisdiction": "SA-RYD"},
    "timing_start": "2026-10-18T08:00:00Z",
    "timing_end": "2026-10-19T18:00:00Z",
    "quality_requirements": {"grade": "A"},
    "pricing_constraints": {"currency": "SAR"},
    "certifications": ["CERT-A"],
    "regulatory_constraints": {"hazardous": False},
    "substitutions": ["ALUMINUM_MIXED"],
    "recurrence": {},
    "status": "DRAFT",
    "provenance": {"source_type": "TEST", "record_id": "demand-1"},
}


def test_demand_crud_idempotency_outbox_and_patch_concurrency() -> None:
    client, token, engine = make_client("org_demand")
    created = client.post(
        "/v1/demands", headers=headers(token, "demand-create"), json=DEMAND
    )
    assert created.status_code == 201, created.text
    data = created.json()["data"]
    demand_id = data["id"]
    assert data["remaining_quantity"]["value"] == "25.000"
    assert data["version"] == 1
    assert created.headers["ETag"] == '"version-1"'

    replay = client.post(
        "/v1/demands", headers=headers(token, "demand-create"), json=DEMAND
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == demand_id

    conflict = client.post(
        "/v1/demands",
        headers=headers(token, "demand-create"),
        json=DEMAND | {"required_state": "COPPER_SCRAP"},
    )
    assert conflict.status_code == 409

    fetched = client.get(f"/v1/demands/{demand_id}", headers=headers(token))
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == demand_id

    listed = client.get("/v1/demands?status=DRAFT&limit=10", headers=headers(token))
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [demand_id]

    activated = client.patch(
        f"/v1/demands/{demand_id}",
        headers=headers(token, "demand-activate") | {"If-Match": '"version-1"'},
        json={"status": "ACTIVE"},
    )
    assert activated.status_code == 200, activated.text
    assert activated.json()["data"]["status"] == "ACTIVE"
    assert activated.json()["data"]["version"] == 2
    assert activated.headers["ETag"] == '"version-2"'

    stale = client.patch(
        f"/v1/demands/{demand_id}",
        headers=headers(token, "demand-stale") | {"If-Match": '"version-1"'},
        json={"status": "PAUSED"},
    )
    assert stale.status_code == 412

    updated = client.patch(
        f"/v1/demands/{demand_id}",
        headers=headers(token, "demand-patch") | {"If-Match": '"version-2"'},
        json={"quantity_target": "20.000", "quantity_max": "25.000"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["quantity_target"]["value"] == "20.000"
    assert updated.json()["data"]["quantity_max"]["value"] == "25.000"
    assert updated.json()["data"]["remaining_quantity"]["value"] == "25.000"

    with engine.connect() as connection:
        events = connection.execute(
            select(OutboxEvent).where(
                OutboxEvent.organization_id == "org_demand",
                OutboxEvent.aggregate_type == "Demand",
                OutboxEvent.aggregate_id == demand_id,
            )
        ).all()
        idempotency = connection.execute(
            select(IdempotencyRecord).where(
                IdempotencyRecord.organization_id == "org_demand",
                IdempotencyRecord.object_type == "Demand",
            )
        ).all()
    assert [row.event_type for row in events] == [
        "demand.created",
        "demand.updated",
        "demand.updated",
    ]
    assert len(idempotency) == 3


def test_demand_tenant_isolation_and_scope_boundary() -> None:
    client_a, token_a, _engine_a = make_client("org_demand_a")
    client_b, token_b, _engine_b = make_client("org_demand_b")
    created = client_a.post(
        "/v1/demands", headers=headers(token_a, "tenant-demand"), json=DEMAND
    )
    assert created.status_code == 201
    demand_id = created.json()["data"]["id"]

    hidden = client_b.get(f"/v1/demands/{demand_id}", headers=headers(token_b))
    assert hidden.status_code == 404
    collection = client_b.get("/v1/demands", headers=headers(token_b))
    assert collection.status_code == 200
    assert collection.json()["data"] == []

    limited, limited_token, _engine = make_client(
        "org_demand_limited", scopes=["demands:read"]
    )
    assert limited.get("/v1/demands", headers=headers(limited_token)).status_code == 200
    denied = limited.post(
        "/v1/demands",
        headers=headers(limited_token, "limited-write"),
        json=DEMAND,
    )
    assert denied.status_code == 403


def test_demand_requires_idempotency_and_if_match() -> None:
    client, token, _engine = make_client("org_demand_headers")
    missing_key = client.post("/v1/demands", headers=headers(token), json=DEMAND)
    assert missing_key.status_code == 400

    created = client.post(
        "/v1/demands", headers=headers(token, "header-demand"), json=DEMAND
    )
    assert created.status_code == 201
    demand_id = created.json()["data"]["id"]
    missing_match = client.patch(
        f"/v1/demands/{demand_id}",
        headers=headers(token, "header-patch"),
        json={"status": "ACTIVE"},
    )
    assert missing_match.status_code == 400


def test_demand_validation_and_lifecycle_fail_closed() -> None:
    client, token, _engine = make_client("org_demand_validation")

    negative = client.post(
        "/v1/demands",
        headers=headers(token, "negative-demand"),
        json=DEMAND | {"quantity_min": "-1.000"},
    )
    assert negative.status_code == 422

    floating = client.post(
        "/v1/demands",
        headers=headers(token, "float-demand"),
        json=DEMAND | {"quantity_target": 25.0},
    )
    assert floating.status_code == 422

    bad_bounds = client.post(
        "/v1/demands",
        headers=headers(token, "bounds-demand"),
        json=DEMAND | {"quantity_min": "30.000", "quantity_target": "20.000"},
    )
    assert bad_bounds.status_code == 422

    naive = client.post(
        "/v1/demands",
        headers=headers(token, "naive-demand"),
        json=DEMAND | {"timing_start": "2026-10-18T08:00:00"},
    )
    assert naive.status_code == 422

    unknown_unit = client.post(
        "/v1/demands",
        headers=headers(token, "unit-demand"),
        json=DEMAND | {"unit": "unknown"},
    )
    assert unknown_unit.status_code == 422

    created = client.post(
        "/v1/demands", headers=headers(token, "lifecycle-demand"), json=DEMAND
    )
    demand_id = created.json()["data"]["id"]
    invalid_transition = client.patch(
        f"/v1/demands/{demand_id}",
        headers=headers(token, "illegal-transition") | {"If-Match": '"version-1"'},
        json={"status": "FULFILLED"},
    )
    assert invalid_transition.status_code == 409


def test_zero_quantity_demand_is_valid_historical_requirement() -> None:
    client, token, _engine = make_client("org_zero_demand")
    zero = client.post(
        "/v1/demands",
        headers=headers(token, "zero-demand"),
        json=DEMAND
        | {"quantity_min": "0", "quantity_target": "0", "quantity_max": "0"},
    )
    assert zero.status_code == 201, zero.text
    assert zero.json()["data"]["remaining_quantity"]["value"] == "0"


def test_demand_patch_is_idempotent() -> None:
    client, token, _engine = make_client("org_patch_idempotent")
    created = client.post(
        "/v1/demands", headers=headers(token, "create-patch-demand"), json=DEMAND
    )
    demand_id = created.json()["data"]["id"]
    patch = {"status": "ACTIVE"}
    first = client.patch(
        f"/v1/demands/{demand_id}",
        headers=headers(token, "same-patch") | {"If-Match": '"version-1"'},
        json=patch,
    )
    assert first.status_code == 200
    replay = client.patch(
        f"/v1/demands/{demand_id}",
        headers=headers(token, "same-patch") | {"If-Match": '"version-1"'},
        json=patch,
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["version"] == first.json()["data"]["version"]
