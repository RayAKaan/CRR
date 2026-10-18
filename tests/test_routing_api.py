from datetime import UTC, datetime
from hashlib import sha256

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.api import create_app
from crr.demand_model import Demand
from crr.models import Actor, APIKey, Base, Location, Organization, Resource, ResourceState

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
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        session.add(
            Resource(
                id="res_a",
                organization_id=org_id,
                resource_type=state_type,
                description=None,
                version=1,
                created_by=f"act_{org_id}",
                provenance={"source_type": "TEST"},
                created_at=NOW,
            )
        )
        session.add(
            ResourceState(
                id="rst_a",
                organization_id=org_id,
                resource_id="res_a",
                resource_version=1,
                state_type=state_type,
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
                id="dem_a",
                organization_id=org_id,
                required_state=state_type,
                quantity_min_value="10.000",
                quantity_target_value="20.000",
                quantity_max_value="30.000",
                remaining_quantity_value="20.000",
                unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                status="ACTIVE",
                location_constraints={},
                timing_start=NOW,
                timing_end=datetime(2026, 10, 18, 18, tzinfo=UTC),
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


def test_routes_compute_direct_candidate_and_is_read_only():
    client, token, engine = make_client()
    seed_direct(engine)

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
    assert str(state.quantity_value) == "100.000"
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
    rejection = zero.json()["data"]["candidates"][0]["rejections"][0]
    assert rejection["code"] == "INSUFFICIENT_QUANTITY"

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
