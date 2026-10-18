"""Transformation domain and API conformance tests."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.api import create_app
from crr.domain import DomainError, Quantity, Transformation, TransformationStatus
from crr.models import Actor, APIKey, Base, Organization, OutboxEvent
NOW = datetime.now(UTC)

TRANSFORMATION = {
    "input_specifications": [{"state_type": "SCRAP", "role": "feedstock"}],
    "output_specifications": [{"state_type": "ALUMINUM", "role": "product"}],
    "yield_min": "0.800",
    "yield_target": "0.900",
    "yield_max": "0.950",
    "loss_residuals": [{"type": "RESIDUAL", "declared": True}],
    "duration_seconds": 3600,
    "capacity": "25.000",
    "unit": "t",
    "unit_registry_version": "CRR-UNITS-0.1",
    "cost_metadata": {"basis": "DECLARATIVE"},
    "quality_effects": {"grade": "A"},
    "regulatory_requirements": {"jurisdiction": "SA-RYD"},
    "eligible_capability_ids": [],
    "eligible_location_ids": [],
    "status": "DRAFT",
    "provenance": {"source_type": "TEST", "record_id": "trn-1"},
}


def make_client(org_id: str = "org_t", scopes: list[str] | None = None):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    token = "test-secret"
    with factory.begin() as session:
        session.add(
            Organization(
                id=org_id,
                name="Factory",
                status="ACTIVE",
                created_at=NOW,
            )
        )
        session.add(
            Actor(
                id=f"act_{org_id}",
                organization_id=org_id,
                name="Admin",
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


def headers(token: str, key: str | None = None, etag: str | None = None):
    result = {"Authorization": f"Bearer {token}"}
    if key:
        result["Idempotency-Key"] = key
    if etag:
        result["If-Match"] = etag
    return result


def test_domain_invariants_and_lifecycle() -> None:
    transformation = Transformation(
        id="trn_1",
        organization_id="org_t",
        input_specifications=({"state_type": "A"},),
        output_specifications=({"state_type": "B"},),
        yield_min=Decimal("0.8"),
        yield_target=Decimal("0.9"),
        yield_max=Decimal("1.0"),
        loss_residuals=(),
        duration_seconds=60,
        capacity=Quantity(Decimal("10"), "t", "CRR-UNITS-0.1"),
        cost_metadata={},
        quality_effects={},
        regulatory_requirements={},
        eligible_capability_ids=(),
        eligible_location_ids=(),
        status=TransformationStatus.DRAFT,
        version=1,
        created_by="act_1",
        provenance={"source_type": "TEST"},
        created_at=NOW,
        updated_at=NOW,
    )
    active = transformation.transition(TransformationStatus.ACTIVE, NOW + timedelta(seconds=1))
    assert active.version == 2
    assert active.status is TransformationStatus.ACTIVE
    try:
        active.transition(TransformationStatus.DRAFT)
    except DomainError:
        pass
    else:
        raise AssertionError("invalid lifecycle transition was accepted")


def test_api_crud_idempotency_concurrency_and_outbox() -> None:
    client, token, engine = make_client()
    created = client.post(
        "/v1/transformations",
        headers=headers(token, "trn-create"),
        json=TRANSFORMATION,
    )
    assert created.status_code == 201, created.text
    data = created.json()["data"]
    assert data["capacity"]["value"] == "25.000"
    assert created.headers["ETag"] == '"version-1"'

    replay = client.post(
        "/v1/transformations",
        headers=headers(token, "trn-create"),
        json=TRANSFORMATION,
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == data["id"]

    listed = client.get("/v1/transformations", headers=headers(token))
    assert listed.status_code == 200
    assert listed.json()["data"][0]["id"] == data["id"]

    patched = client.patch(
        f"/v1/transformations/{data['id']}",
        headers=headers(token, "trn-patch", '"version-1"'),
        json={"status": "ACTIVE", "quality_effects": {"grade": "AA"}},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["data"]["version"] == 2

    stale = client.patch(
        f"/v1/transformations/{data['id']}",
        headers=headers(token, "trn-stale", '"version-1"'),
        json={"duration_seconds": 7200},
    )
    assert stale.status_code == 412

    with sessionmaker(bind=engine)() as session:
        events = session.scalars(
            select(OutboxEvent).where(OutboxEvent.aggregate_type == "Transformation")
        ).all()
        assert [event.event_type for event in events] == [
            "transformation.created",
            "transformation.updated",
        ]


def test_api_rejects_float_and_invalid_yield() -> None:
    client, token, _ = make_client("org_validation")
    float_payload = {**TRANSFORMATION, "capacity": 25.0}
    response = client.post(
        "/v1/transformations",
        headers=headers(token, "float"),
        json=float_payload,
    )
    assert response.status_code == 422
    invalid_yield = {
        **TRANSFORMATION,
        "yield_min": "0.9",
        "yield_target": "0.8",
        "yield_max": "0.95",
    }
    response = client.post(
        "/v1/transformations",
        headers=headers(token, "yield"),
        json=invalid_yield,
    )
    assert response.status_code == 422


def test_api_requires_transformation_scopes() -> None:
    client, token, _ = make_client("org_scope", ["demands:read"])
    response = client.get("/v1/transformations", headers=headers(token))
    assert response.status_code == 403
    response = client.post(
        "/v1/transformations",
        headers=headers(token, "scope-create"),
        json=TRANSFORMATION,
    )
    assert response.status_code == 403
