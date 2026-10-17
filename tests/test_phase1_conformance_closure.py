from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.api import create_app
from crr.models import Actor, APIKey, Base, Location, Organization, Resource, ResourceState

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)


def _factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def _seed_tenant(session_factory, org_id: str, token: str, *, scope: str = "admin:*") -> None:
    with session_factory.begin() as session:
        session.add(Organization(id=org_id, name=org_id, status="ACTIVE", created_at=NOW))
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
                scopes=[scope],
                revoked=False,
                created_at=NOW,
            )
        )


def _auth(token: str, key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if key:
        headers["Idempotency-Key"] = key
    return headers


def _seed_base(client: TestClient, token: str, suffix: str) -> tuple[str, str]:
    location = client.post(
        "/v1/locations",
        headers=_auth(token, f"loc-{suffix}"),
        json={
            "id": f"loc_{suffix}",
            "name": "Yard",
            "provenance": {"source_type": "TEST"},
        },
    )
    assert location.status_code == 201, location.text
    resource = client.post(
        "/v1/resources",
        headers=_auth(token, f"res-{suffix}"),
        json={
            "id": f"res_{suffix}",
            "resource_type": "ALUMINUM",
            "provenance": {"source_type": "TEST"},
        },
    )
    assert resource.status_code == 201, resource.text
    return f"loc_{suffix}", f"res_{suffix}"


def _seed_resource(client: TestClient, token: str, suffix: str) -> tuple[str, str, str]:
    location_id, resource_id = _seed_base(client, token, suffix)
    state = client.post(
        "/v1/resource-states",
        headers=_auth(token, f"state-{suffix}"),
        json={
            "id": f"rst_{suffix}",
            "resource_id": resource_id,
            "state_type": "ALUMINUM",
            "quantity": {
                "value": "10.000",
                "unit": "t",
                "unit_registry_version": "CRR-UNITS-0.1",
            },
            "location_id": location_id,
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "TEST"},
        },
    )
    assert state.status_code == 201, state.text
    return location_id, resource_id, f"rst_{suffix}"


def test_cross_tenant_detail_collection_history_and_reference_writes_are_isolated() -> None:
    engine, factory = _factory()
    _seed_tenant(factory, "org_a", "token-a")
    _seed_tenant(factory, "org_b", "token-b")
    client = TestClient(create_app(factory))
    _, resource_id, state_id = _seed_resource(client, "token-a", "tenant_a")

    detail = client.get(f"/v1/resource-states/{state_id}", headers=_auth("token-b"))
    assert detail.status_code == 404

    collection = client.get(
        "/v1/resource-states",
        headers=_auth("token-b"),
        params={"resource_id": resource_id},
    )
    assert collection.status_code == 200
    assert collection.json()["data"] == []

    history = client.get(
        f"/v1/resources/{resource_id}/resource-states",
        headers=_auth("token-b"),
    )
    assert history.status_code == 404

    cross_tenant_state = client.post(
        "/v1/resource-states",
        headers=_auth("token-b", "cross-tenant-state"),
        json={
            "resource_id": resource_id,
            "state_type": "ALUMINUM",
            "quantity": {
                "value": "5.000",
                "unit": "t",
                "unit_registry_version": "CRR-UNITS-0.1",
            },
            "location_id": "loc_tenant_a",
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "TEST"},
        },
    )
    assert cross_tenant_state.status_code == 404

    own = client.get(f"/v1/resource-states/{state_id}", headers=_auth("token-a"))
    assert own.status_code == 200
    assert own.json()["data"]["organization_id"] == "org_a"
    engine.dispose()


@pytest.mark.parametrize(
    ("value", "expected_status"),
    [
        ("-1", 422),
        ("0", 201),
        ("1.234567890123456789012345678901", 201),
        ("not-a-number", 422),
        ("1e3", 201),
    ],
)
def test_quantity_validation_matrix(value: str, expected_status: int) -> None:
    _engine, factory = _factory()
    _seed_tenant(factory, "org_q", "token-q")
    client = TestClient(create_app(factory))
    suffix = uuid4().hex[:10]
    location_id, resource_id = _seed_base(client, "token-q", suffix)
    response = client.post(
        "/v1/resource-states",
        headers=_auth("token-q", f"quantity-{suffix}"),
        json={
            "resource_id": resource_id,
            "state_type": "ALUMINUM",
            "quantity": {
                "value": value,
                "unit": "t",
                "unit_registry_version": "CRR-UNITS-0.1",
            },
            "location_id": location_id,
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "TEST"},
        },
    )
    assert response.status_code == expected_status, response.text


def test_float_quantity_is_rejected_at_canonical_boundary() -> None:
    _engine, factory = _factory()
    _seed_tenant(factory, "org_float", "token-float")
    client = TestClient(create_app(factory))
    suffix = uuid4().hex[:10]
    location_id, resource_id = _seed_base(client, "token-float", suffix)
    response = client.post(
        "/v1/resource-states",
        headers=_auth("token-float", "float-value"),
        json={
            "resource_id": resource_id,
            "state_type": "ALUMINUM",
            "quantity": {
                "value": 1.25,
                "unit": "t",
                "unit_registry_version": "CRR-UNITS-0.1",
            },
            "location_id": location_id,
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "TEST"},
        },
    )
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("unit", "registry_version", "expected_status"),
    [
        ("unknown-unit", "CRR-UNITS-0.1", 422),
        ("kg", "CRR-UNITS-0.1", 201),
        ("t", "unknown-registry", 422),
    ],
)
def test_unit_validation_matrix(unit: str, registry_version: str, expected_status: int) -> None:
    _engine, factory = _factory()
    _seed_tenant(factory, "org_unit", "token-unit")
    client = TestClient(create_app(factory))
    suffix = uuid4().hex[:10]
    location_id, resource_id = _seed_base(client, "token-unit", suffix)
    response = client.post(
        "/v1/resource-states",
        headers=_auth("token-unit", f"unit-{suffix}"),
        json={
            "resource_id": resource_id,
            "state_type": "ALUMINUM",
            "quantity": {
                "value": "1",
                "unit": unit,
                "unit_registry_version": registry_version,
            },
            "location_id": location_id,
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "TEST"},
        },
    )
    assert response.status_code == expected_status, response.text


@pytest.mark.skipif(not os.getenv("CRR_DATABASE_URL"), reason="requires PostgreSQL CI database")
def test_postgresql_parallel_successor_creation_has_one_winner() -> None:
    database_url = os.environ["CRR_DATABASE_URL"]
    engine = create_engine(database_url, pool_size=5, max_overflow=5)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    suffix = uuid4().hex[:12]
    org_id = f"org_concurrency_{suffix}"
    actor_id = f"act_{org_id}"
    token = f"token-{suffix}"
    with factory.begin() as session:
        session.add(Organization(id=org_id, name=org_id, status="ACTIVE", created_at=NOW))
        session.flush()
        session.add(
            Actor(
                id=actor_id,
                organization_id=org_id,
                name="Admin",
                role="ORG_ADMIN",
                active=True,
                created_at=NOW,
            )
        )
        session.flush()
        session.add(
            APIKey(
                id=f"key_{suffix}",
                organization_id=org_id,
                actor_id=actor_id,
                secret_hash=sha256(token.encode()).hexdigest(),
                scopes=["admin:*"],
                revoked=False,
                created_at=NOW,
            )
        )
        session.flush()
        session.add(
            Location(
                id=f"loc_{suffix}",
                organization_id=org_id,
                name="Yard",
                provenance={"source_type": "TEST"},
                created_at=NOW,
            )
        )
        session.flush()
        session.add(
            Resource(
                id=f"res_{suffix}",
                organization_id=org_id,
                resource_type="ALUMINUM",
                version=1,
                created_by=actor_id,
                provenance={"source_type": "TEST"},
                created_at=NOW,
            )
        )
        session.flush()
        session.add(
            ResourceState(
                id=f"rst_{suffix}",
                organization_id=org_id,
                resource_id=f"res_{suffix}",
                resource_version=1,
                state_type="ALUMINUM",
                quantity_value=Decimal("10.000"),
                unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                location_id=f"loc_{suffix}",
                effective_at=NOW,
                recorded_at=NOW,
                created_by=actor_id,
                provenance={"source_type": "TEST"},
                quality={},
                physical_properties={},
                predecessor_state_ids=[],
            )
        )
    client = TestClient(create_app(factory))
    body = {
        "kind": "PHYSICAL_CHANGE",
        "reason": "parallel conformance test",
        "occurred_at": "2026-10-17T12:01:00Z",
        "state_type": "ALUMINUM",
        "quantity": {
            "value": "10.000",
            "unit": "t",
            "unit_registry_version": "CRR-UNITS-0.1",
        },
        "location_id": f"loc_{suffix}",
        "provenance": {"source_type": "TEST"},
    }

    def transition(index: int):
        response = client.post(
            f"/v1/resource-states/rst_{suffix}/transitions",
            headers={
                **_auth(token, f"parallel-{index}-{suffix}"),
                "If-Match": '"version-1"',
            },
            json=body,
        )
        return response.status_code, response.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(transition, [1, 2]))

    statuses = sorted(result[0] for result in results)
    assert statuses == [201, 412]
    with factory() as session:
        states = session.scalars(
            select(ResourceState).where(ResourceState.resource_id == f"res_{suffix}")
        ).all()
        assert len(states) == 2
        resource = session.get(Resource, f"res_{suffix}")
        assert resource is not None
        assert resource.version == 2
    engine.dispose()
