"""Cross-object Phase 2 conformance tests."""

from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.api import create_app
from crr.capability_model import Capability
from crr.models import Actor, APIKey, Base, Location, Organization, ResourceState
from crr.transformation_model import Transformation

NOW = datetime.now(UTC)
WINDOW_START = datetime(2026, 10, 18, 8, tzinfo=UTC)
WINDOW_END = datetime(2026, 10, 18, 18, tzinfo=UTC)


def make_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    token = "phase2-closure-secret"
    with factory.begin() as session:
        session.add(Organization(id="org_a", name="Factory A", status="ACTIVE", created_at=NOW))
        session.add(Organization(id="org_b", name="Factory B", status="ACTIVE", created_at=NOW))
        session.add(
            Actor(
                id="act_org_a",
                organization_id="org_a",
                name="Admin A",
                role="ORG_ADMIN",
                active=True,
                created_at=NOW,
            )
        )
        session.add(
            Actor(
                id="act_org_b",
                organization_id="org_b",
                name="Admin B",
                role="ORG_ADMIN",
                active=True,
                created_at=NOW,
            )
        )
        session.add(
            Location(
                id="loc_org_a",
                organization_id="org_a",
                name="Factory A",
                address="Test A",
                latitude=None,
                longitude=None,
                jurisdiction="SA-RYD",
                provenance={"source_type": "TEST"},
                created_at=NOW,
            )
        )
        session.add(
            Location(
                id="loc_org_b",
                organization_id="org_b",
                name="Factory B",
                address="Test B",
                latitude=None,
                longitude=None,
                jurisdiction="SA-RYD",
                provenance={"source_type": "TEST"},
                created_at=NOW,
            )
        )
        session.add(
            APIKey(
                id="key_org_a",
                organization_id="org_a",
                actor_id="act_org_a",
                secret_hash=sha256(token.encode()).hexdigest(),
                scopes=["admin:*"],
                revoked=False,
                created_at=NOW,
            )
        )
    return TestClient(create_app(factory)), token, engine, factory


def headers(token: str, key: str | None = None, etag: str | None = None) -> dict[str, str]:
    result = {"Authorization": f"Bearer {token}"}
    if key:
        result["Idempotency-Key"] = key
    if etag:
        result["If-Match"] = etag
    return result


def transformation_payload(**overrides):
    payload = {
        "input_specifications": [{"state_type": "SCRAP"}],
        "output_specifications": [{"state_type": "BILLET"}],
        "yield_min": "0.800",
        "yield_target": "0.900",
        "yield_max": "0.950",
        "loss_residuals": [{"type": "PROCESS_LOSS"}],
        "duration_seconds": 3600,
        "capacity": "25.000",
        "unit": "t",
        "unit_registry_version": "CRR-UNITS-0.1",
        "cost_metadata": {"basis": "DECLARATIVE"},
        "quality_effects": {},
        "regulatory_requirements": {},
        "eligible_capability_ids": [],
        "eligible_location_ids": [],
        "status": "DRAFT",
        "provenance": {"source_type": "TEST", "record_id": "closure"},
    }
    payload.update(overrides)
    return payload


def test_transformation_reference_cannot_cross_tenant():
    client, token, engine, factory = make_client()
    with factory.begin() as session:
        session.add(
            Capability(
                id="cap_org_b",
                organization_id="org_b",
                accepted_inputs=[{"state_type": "SCRAP"}],
                output_specifications={"state_type": "BILLET"},
                transformation_ids=[],
                capacity_value=Decimal("100.000"),
                unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                minimum_batch_value=None,
                location_id="loc_org_b",
                operating_window_start=WINDOW_START,
                operating_window_end=WINDOW_END,
                processing_cost={},
                certifications=[],
                regulatory_constraints={},
                status="ACTIVE",
                version=1,
                created_by="act_org_b",
                provenance={"source_type": "TEST"},
                created_at=NOW,
                updated_at=NOW,
            )
        )
    response = client.post(
        "/v1/transformations",
        headers=headers(token, "cross-tenant-capability"),
        json=transformation_payload(eligible_capability_ids=["cap_org_b"]),
    )
    assert response.status_code == 404

    response = client.post(
        "/v1/transformations",
        headers=headers(token, "cross-tenant-location"),
        json=transformation_payload(eligible_location_ids=["loc_org_b"]),
    )
    assert response.status_code == 404

    with engine.connect() as connection:
        assert connection.execute(select(Transformation)).all() == []


def test_phase2_objects_do_not_create_physical_state():
    client, token, engine, _factory = make_client()
    with engine.connect() as connection:
        before = connection.execute(select(ResourceState.id)).all()
    assert before == []

    demand = client.post(
        "/v1/demands",
        headers=headers(token, "closure-demand"),
        json={
            "required_state": "ALUMINUM_SCRAP",
            "quantity_min": "10.000",
            "quantity_target": "20.000",
            "quantity_max": "25.000",
            "unit": "t",
            "unit_registry_version": "CRR-UNITS-0.1",
            "location_constraints": {},
            "timing_start": "2026-10-18T08:00:00Z",
            "timing_end": "2026-10-18T18:00:00Z",
            "quality_requirements": {},
            "pricing_constraints": {},
            "certifications": [],
            "regulatory_constraints": {},
            "substitutions": [],
            "recurrence": {},
            "status": "DRAFT",
            "provenance": {"source_type": "TEST"},
        },
    )
    assert demand.status_code == 201, demand.text

    capability = client.post(
        "/v1/capabilities",
        headers=headers(token, "closure-capability"),
        json={
            "accepted_inputs": [{"state_type": "ALUMINUM_SCRAP"}],
            "output_specifications": {"state_type": "ALUMINUM_BILLET"},
            "transformation_ids": [],
            "capacity": "100.000",
            "unit": "t",
            "unit_registry_version": "CRR-UNITS-0.1",
            "minimum_batch": "10.000",
            "location_id": "loc_org_a",
            "operating_window_start": "2026-10-18T08:00:00Z",
            "operating_window_end": "2026-10-18T18:00:00Z",
            "processing_cost": {},
            "certifications": [],
            "regulatory_constraints": {},
            "status": "DRAFT",
            "provenance": {"source_type": "TEST"},
        },
    )
    assert capability.status_code == 201, capability.text

    transformation = client.post(
        "/v1/transformations",
        headers=headers(token, "closure-transformation"),
        json=transformation_payload(),
    )
    assert transformation.status_code == 201, transformation.text

    with engine.connect() as connection:
        after = connection.execute(select(ResourceState.id)).all()
    assert after == []


def test_transformation_exact_decimal_boundary_rejects_float():
    client, token, _engine, _factory = make_client()
    floating = client.post(
        "/v1/transformations",
        headers=headers(token, "closure-float"),
        json=transformation_payload(capacity=25.0),
    )
    assert floating.status_code == 422


def test_phase2_lifecycle_terminal_states_remain_terminal():
    client, token, _engine, _factory = make_client()
    created = client.post(
        "/v1/transformations",
        headers=headers(token, "closure-lifecycle-create"),
        json=transformation_payload(),
    )
    assert created.status_code == 201
    transformation_id = created.json()["data"]["id"]

    active = client.patch(
        f"/v1/transformations/{transformation_id}",
        headers=headers(token, "closure-lifecycle-active", '"version-1"'),
        json={"status": "ACTIVE"},
    )
    assert active.status_code == 200

    revoked = client.patch(
        f"/v1/transformations/{transformation_id}",
        headers=headers(token, "closure-lifecycle-revoke", '"version-2"'),
        json={"status": "REVOKED"},
    )
    assert revoked.status_code == 200

    reactivated = client.patch(
        f"/v1/transformations/{transformation_id}",
        headers=headers(token, "closure-lifecycle-reactivate", '"version-3"'),
        json={"status": "ACTIVE"},
    )
    assert reactivated.status_code == 409
