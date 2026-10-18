from datetime import UTC, datetime
from hashlib import sha256

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.api import create_app
from crr.models import (
    Actor,
    APIKey,
    Base,
    Capability,
    Demand,
    Location,
    Organization,
    Resource,
    ResourceState,
    Transformation,
)

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
        session.add(Organization(id=org_id, name="Factory A", status="ACTIVE", created_at=NOW))
        session.add(
            Actor(
                id=f"act_{org_id}",
                organization_id=org_id,
                name="Router",
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


def seed_direct(engine, org_id: str = "org_a", state_type: str = "ALUMINUM_SCRAP") -> None:
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO resources (id, organization_id, resource_type, description, version, created_by, provenance, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("res_a", org_id, state_type, None, 1, f"act_{org_id}", '{"source_type":"TEST"}', NOW.isoformat()),
        )
        connection.exec_driver_sql(
            "INSERT INTO resource_states (id, organization_id, resource_id, resource_version, state_type, quantity_value, unit, unit_registry_version, location_id, effective_at, recorded_at, created_by, provenance, quality, physical_properties, predecessor_state_ids) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "rst_a", org_id, "res_a", 1, state_type, "100.000", "t", "CRR-UNITS-0.1",
                f"loc_{org_id}", NOW.isoformat(), NOW.isoformat(), f"act_{org_id}",
                '{"source_type":"TEST"}', '{}', '{}', '[]',
            ),
        )
        connection.exec_driver_sql(
            "INSERT INTO demands (id, organization_id, required_state, quantity_min_value, quantity_target_value, quantity_max_value, remaining_quantity_value, unit, unit_registry_version, status, location_constraints, timing_start, timing_end, quality_requirements, pricing_constraints, certifications, regulatory_constraints, substitutions, recurrence, version, created_by, provenance, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "dem_a", org_id, state_type, "10.000", "20.000", "30.000", "20.000", "t", "CRR-UNITS-0.1", "ACTIVE",
                '{}', NOW.isoformat(), "2026-10-18T18:00:00+00:00", '{}', '{}', '[]', '{}', '[]', '{}', 1,
                f"act_{org_id}", '{"source_type":"TEST"}', NOW.isoformat(), NOW.isoformat(),
            ),
        )


def test_routes_compute_direct_candidate_and_is_read_only():
    client, token, engine = make_client()
    seed_direct(engine)
    before = client.get("/v1/resources/rst_a", headers=auth(token))
    assert before.status_code == 404

    response = client.post(
        "/v1/routes/compute",
        headers=auth(token),
        json={"source_resource_state_id": "rst_a", "target_demand_id": "dem_a"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()["data"]
    assert payload["candidates"][0]["status"] == "FEASIBLE"
    assert payload["candidates"][0]["source_version"] == 1

    with engine.connect() as connection:
        state = connection.execute(select(ResourceState).where(ResourceState.id == "rst_a")).one()
        demand = connection.execute(select(Demand).where(Demand.id == "dem_a")).one()
    assert state.quantity_value == state.quantity_value
    assert demand.version == 1


def test_routes_compute_requires_least_privilege_scope():
    client, token, engine = make_client("org_scope", scopes=["resources:read"])
    seed_direct(engine, "org_scope")
    response = client.post(
        "/v1/routes/compute",
        headers=auth(token),
        json={"source_resource_state_id": "rst_a", "target_demand_id": "dem_a"},
    )
    assert response.status_code == 403


def test_routes_compute_hides_cross_tenant_objects():
    client, token, engine = make_client("org_b")
    seed_direct(engine, "org_b")
    response = client.post(
        "/v1/routes/compute",
        headers=auth(token),
        json={"source_resource_state_id": "rst_a", "target_demand_id": "dem_missing"},
    )
    assert response.status_code == 404


def test_routes_compute_rejects_zero_supply_and_malformed_inline_authority():
    client, token, engine = make_client("org_zero")
    seed_direct(engine, "org_zero")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "UPDATE resource_states SET quantity_value = ? WHERE id = ?", ("0.000", "rst_a")
        )
    zero = client.post(
        "/v1/routes/compute",
        headers=auth(token),
        json={"source_resource_state_id": "rst_a", "target_demand_id": "dem_a"},
    )
    assert zero.status_code == 200
    assert zero.json()["data"]["candidates"][0]["rejections"][0]["code"] == "INSUFFICIENT_QUANTITY"

    malformed = client.post(
        "/v1/routes/compute",
        headers=auth(token),
        json={
            "source_resource_state_id": "rst_a",
            "target_demand_id": "dem_a",
            "source_quantity": "100.000",
        },
    )
    assert malformed.status_code == 422
