from datetime import UTC, datetime
from hashlib import sha256

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.api import create_app
from crr.models import Actor, APIKey, Base, IdempotencyRecord, Location, Organization, OutboxEvent


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
            Location(
                id=f"loc_{org_id}",
                organization_id=org_id,
                name="Factory",
                address="Test",
                latitude=None,
                longitude=None,
                jurisdiction="SA-RYD",
                provenance={"source_type": "TEST"},
                created_at=now,
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
                created_at=now,
            )
        )
    return TestClient(create_app(factory)), token, engine


def headers(token: str, key: str | None = None) -> dict[str, str]:
    result = {"Authorization": f"Bearer {token}"}
    if key:
        result["Idempotency-Key"] = key
    return result


CAPABILITY = {
    "accepted_inputs": [{"state_type": "ALUMINUM_SCRAP", "quality": {"grade": "A"}}],
    "output_specifications": {"state_type": "ALUMINUM_BILLET", "quality": {"grade": "A"}},
    "transformation_ids": [],
    "capacity": "100.000",
    "unit": "t",
    "unit_registry_version": "CRR-UNITS-0.1",
    "minimum_batch": "10.000",
    "location_id": "loc_capability",
    "operating_window_start": "2026-10-18T08:00:00Z",
    "operating_window_end": "2026-10-18T18:00:00Z",
    "processing_cost": {"currency": "SAR"},
    "certifications": ["CERT-A"],
    "regulatory_constraints": {"eligible": True},
    "status": "DRAFT",
    "provenance": {"source_type": "TEST", "record_id": "capability-1"},
}


def prepare_location(engine, org_id: str) -> None:
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO locations (id, organization_id, name, address, latitude, longitude, "
            "jurisdiction, provenance, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "loc_capability",
                org_id,
                "Factory",
                "Test",
                None,
                None,
                "SA-RYD",
                '{"source_type":"TEST"}',
                datetime.now(UTC).isoformat(),
            ),
        )


def test_capability_crud_idempotency_outbox_and_concurrency() -> None:
    client, token, engine = make_client("org_capability")
    prepare_location(engine, "org_capability")
    created = client.post("/v1/capabilities", headers=headers(token, "cap-create"), json=CAPABILITY)
    assert created.status_code == 201, created.text
    data = created.json()["data"]
    capability_id = data["id"]
    assert data["capacity"]["value"] == "100.000"
    assert data["version"] == 1
    assert created.headers["ETag"] == '"version-1"'

    replay = client.post("/v1/capabilities", headers=headers(token, "cap-create"), json=CAPABILITY)
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == capability_id

    conflict = client.post(
        "/v1/capabilities",
        headers=headers(token, "cap-create"),
        json=CAPABILITY | {"capacity": "200.000"},
    )
    assert conflict.status_code == 409

    fetched = client.get(f"/v1/capabilities/{capability_id}", headers=headers(token))
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == capability_id

    listed = client.get("/v1/capabilities?status=DRAFT&limit=10", headers=headers(token))
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [capability_id]

    activated = client.patch(
        f"/v1/capabilities/{capability_id}",
        headers=headers(token, "cap-activate") | {"If-Match": '"version-1"'},
        json={"status": "ACTIVE"},
    )
    assert activated.status_code == 200, activated.text
    assert activated.json()["data"]["status"] == "ACTIVE"
    assert activated.json()["data"]["version"] == 2

    updated = client.patch(
        f"/v1/capabilities/{capability_id}",
        headers=headers(token, "cap-update") | {"If-Match": '"version-2"'},
        json={"capacity": "120.000", "minimum_batch": "12.000"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["data"]["capacity"]["value"] == "120.000"
    assert updated.json()["data"]["version"] == 3

    stale = client.patch(
        f"/v1/capabilities/{capability_id}",
        headers=headers(token, "cap-stale") | {"If-Match": '"version-2"'},
        json={"status": "SUSPENDED"},
    )
    assert stale.status_code == 412

    with engine.connect() as connection:
        events = connection.execute(
            select(OutboxEvent).where(
                OutboxEvent.organization_id == "org_capability",
                OutboxEvent.aggregate_type == "Capability",
                OutboxEvent.aggregate_id == capability_id,
            )
        ).all()
        records = connection.execute(
            select(IdempotencyRecord).where(
                IdempotencyRecord.organization_id == "org_capability",
                IdempotencyRecord.object_type == "Capability",
            )
        ).all()
    assert [row.event_type for row in events] == [
        "capability.created",
        "capability.updated",
        "capability.updated",
    ]
    assert len(records) == 3


def test_capability_tenant_isolation_and_scope() -> None:
    client_a, token_a, engine_a = make_client("org_cap_a")
    prepare_location(engine_a, "org_cap_a")
    created = client_a.post(
        "/v1/capabilities",
        headers=headers(token_a, "tenant-cap"),
        json=CAPABILITY,
    )
    assert created.status_code == 201
    capability_id = created.json()["data"]["id"]

    client_b, token_b, _engine_b = make_client("org_cap_b")
    hidden = client_b.get(f"/v1/capabilities/{capability_id}", headers=headers(token_b))
    assert hidden.status_code == 404
    assert client_b.get("/v1/capabilities", headers=headers(token_b)).json()["data"] == []

    limited, limited_token, limited_engine = make_client(
        "org_cap_limited", scopes=["capabilities:read"]
    )
    prepare_location(limited_engine, "org_cap_limited")
    assert limited.get("/v1/capabilities", headers=headers(limited_token)).status_code == 200
    denied = limited.post(
        "/v1/capabilities",
        headers=headers(limited_token, "limited-cap-write"),
        json=CAPABILITY,
    )
    assert denied.status_code == 403


def test_capability_requires_idempotency_and_if_match() -> None:
    client, token, engine = make_client("org_cap_headers")
    prepare_location(engine, "org_cap_headers")
    missing_key = client.post("/v1/capabilities", headers=headers(token), json=CAPABILITY)
    assert missing_key.status_code == 400

    created = client.post("/v1/capabilities", headers=headers(token, "header-cap"), json=CAPABILITY)
    assert created.status_code == 201
    capability_id = created.json()["data"]["id"]
    missing_match = client.patch(
        f"/v1/capabilities/{capability_id}",
        headers=headers(token, "header-cap-patch"),
        json={"status": "ACTIVE"},
    )
    assert missing_match.status_code == 400


def test_capability_validation_and_lifecycle_fail_closed() -> None:
    client, token, engine = make_client("org_cap_validation")
    prepare_location(engine, "org_cap_validation")

    negative = client.post(
        "/v1/capabilities",
        headers=headers(token, "negative-cap"),
        json=CAPABILITY | {"capacity": "-1.000"},
    )
    assert negative.status_code == 422

    floating = client.post(
        "/v1/capabilities",
        headers=headers(token, "float-cap"),
        json=CAPABILITY | {"capacity": 100.0},
    )
    assert floating.status_code == 422

    bad_window = client.post(
        "/v1/capabilities",
        headers=headers(token, "window-cap"),
        json=CAPABILITY | {"operating_window_start": "2026-10-18T08:00:00"},
    )
    assert bad_window.status_code == 422

    bad_unit = client.post(
        "/v1/capabilities",
        headers=headers(token, "unit-cap"),
        json=CAPABILITY | {"unit": "unknown"},
    )
    assert bad_unit.status_code == 422

    missing_location = client.post(
        "/v1/capabilities",
        headers=headers(token, "location-cap"),
        json=CAPABILITY | {"location_id": "loc_other"},
    )
    assert missing_location.status_code == 404

    missing_transformation = client.post(
        "/v1/capabilities",
        headers=headers(token, "transformation-ref-cap"),
        json=CAPABILITY | {"transformation_ids": ["trn_missing"]},
    )
    assert missing_transformation.status_code == 404

    duplicate_transformation = client.post(
        "/v1/capabilities",
        headers=headers(token, "duplicate-transformation-cap"),
        json=CAPABILITY | {"transformation_ids": ["trn_missing", "trn_missing"]},
    )
    assert duplicate_transformation.status_code == 422

    created = client.post(
        "/v1/capabilities",
        headers=headers(token, "lifecycle-cap"),
        json=CAPABILITY,
    )
    capability_id = created.json()["data"]["id"]
    invalid_transition = client.patch(
        f"/v1/capabilities/{capability_id}",
        headers=headers(token, "illegal-cap-transition") | {"If-Match": '"version-1"'},
        json={"status": "SUSPENDED"},
    )
    assert invalid_transition.status_code == 409


def test_capability_patch_idempotency() -> None:
    client, token, engine = make_client("org_cap_patch")
    prepare_location(engine, "org_cap_patch")
    created = client.post(
        "/v1/capabilities",
        headers=headers(token, "create-cap"),
        json=CAPABILITY,
    )
    capability_id = created.json()["data"]["id"]
    first = client.patch(
        f"/v1/capabilities/{capability_id}",
        headers=headers(token, "same-cap-patch") | {"If-Match": '"version-1"'},
        json={"status": "ACTIVE"},
    )
    assert first.status_code == 200
    replay = client.patch(
        f"/v1/capabilities/{capability_id}",
        headers=headers(token, "same-cap-patch") | {"If-Match": '"version-1"'},
        json={"status": "ACTIVE"},
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["version"] == 2
