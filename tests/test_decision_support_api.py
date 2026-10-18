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


def seed_direct(engine, org_id: str = "org_a") -> None:
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    with factory.begin() as session:
        session.add(
            Resource(
                id="res_a",
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
                id="rst_a",
                organization_id=org_id,
                resource_id="res_a",
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
                id="dem_a",
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


def optimization_payload(decision_mode: str | None = None) -> dict[str, object]:
    payload: dict[str, object] = {
        "source_resource_state_id": "rst_a",
        "target_demand_id": "dem_a",
        "optimization": {
            "objective": "MIN_DURATION",
            "policy_id": "policy_api",
            "policy_version": 1,
            "calculation_version": "1",
        },
    }
    if decision_mode is not None:
        payload["decision_mode"] = decision_mode
    return payload


def test_advisory_mode_returns_ranked_human_review_output_without_mutation():
    client, token, engine = make_client()
    seed_direct(engine)

    response = client.post(
        "/v1/routes/compute",
        headers=auth(token),
        json=optimization_payload("ADVISORY"),
    )

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["optimization"]["ranked"][0]["candidate_id"] == "route_rst_a_dem_a"
    advisory = data["decision_support"]
    assert advisory["mode"] == "ADVISORY"
    assert advisory["leading_candidate_id"] == "route_rst_a_dem_a"
    assert advisory["human_review_required"] is True
    assert advisory["candidate_set_fingerprint"] == data["optimization"]["candidate_set_fingerprint"]
    assert advisory["alternatives"][0]["score"] == "0"

    with engine.connect() as connection:
        state = connection.execute(select(ResourceState).where(ResourceState.id == "rst_a")).one()
        demand = connection.execute(select(Demand).where(Demand.id == "dem_a")).one()
    assert str(state.quantity_value) == "100.000"
    assert demand.version == 1


def test_advisory_mode_requires_optimization():
    client, token, engine = make_client("org_no_opt")
    seed_direct(engine, "org_no_opt")
    response = client.post(
        "/v1/routes/compute",
        headers=auth(token),
        json={
            "source_resource_state_id": "rst_a",
            "target_demand_id": "dem_a",
            "decision_mode": "ADVISORY",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "DECISION_MODE_REQUIRES_OPTIMIZATION"


def test_unknown_decision_mode_is_rejected_by_schema():
    client, token, engine = make_client("org_bad_mode")
    seed_direct(engine, "org_bad_mode")
    response = client.post(
        "/v1/routes/compute",
        headers=auth(token),
        json=optimization_payload("AUTONOMOUS"),
    )
    assert response.status_code == 422
