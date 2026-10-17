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
    IdempotencyRecord,
    Organization,
    OutboxEvent,
    Resource,
    ResourceState,
)

NOW = datetime(2026, 10, 17, 12, 0, tzinfo=UTC)


def make_client(scopes: list[str] | None = None, *, org_id: str = "org_a"):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    token = f"secret-{org_id}"
    with factory.begin() as session:
        session.add(Organization(id=org_id, name="Factory A", status="ACTIVE", created_at=NOW))
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
    return TestClient(create_app(factory)), token, factory


def auth(token: str, key: str | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {token}"}
    if key is not None:
        headers["Idempotency-Key"] = key
    return headers


def test_least_privilege_scope_blocks_unrelated_mutation() -> None:
    client, token, _factory = make_client(["locations:read"])
    response = client.post(
        "/v1/locations",
        headers=auth(token, "scope-test"),
        json={"name": "Yard", "provenance": {"source_type": "MANUAL"}},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SCOPE_REQUIRED"


def test_revoked_key_and_inactive_actor_are_rejected() -> None:
    client, token, factory = make_client()
    with factory.begin() as session:
        key = session.scalar(select(APIKey).where(APIKey.id == "key_org_a"))
        assert key is not None
        key.revoked = True
    revoked = client.get("/v1/organizations/org_a", headers=auth(token))
    assert revoked.status_code == 401
    assert revoked.json()["error"]["code"] == "INVALID_CREDENTIAL"

    client, token, factory = make_client(org_id="org_c")
    with factory.begin() as session:
        actor = session.scalar(select(Actor).where(Actor.id == "act_org_c"))
        assert actor is not None
        actor.active = False
    inactive = client.get("/v1/organizations/org_c", headers=auth(token))
    assert inactive.status_code == 401
    assert inactive.json()["error"]["code"] == "INVALID_ACTOR"


def test_idempotency_key_reuse_with_different_payload_is_conflict() -> None:
    client, token, _factory = make_client()
    first = client.post(
        "/v1/locations",
        headers=auth(token, "same-key"),
        json={"name": "Yard A", "provenance": {"source_type": "MANUAL"}},
    )
    assert first.status_code == 201
    second = client.post(
        "/v1/locations",
        headers=auth(token, "same-key"),
        json={"name": "Yard B", "provenance": {"source_type": "MANUAL"}},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_missing_idempotency_key_is_rejected_for_mutation() -> None:
    client, token, _factory = make_client()
    response = client.post(
        "/v1/locations",
        headers=auth(token),
        json={"name": "Yard", "provenance": {"source_type": "MANUAL"}},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_canonical_quantity_preserves_exact_scientific_decimal_input() -> None:
    client, token, _factory = make_client()
    location = client.post(
        "/v1/locations",
        headers=auth(token, "location"),
        json={"name": "Yard", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]["id"]
    resource = client.post(
        "/v1/resources",
        headers=auth(token, "resource"),
        json={"resource_type": "ALUMINUM", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]["id"]
    response = client.post(
        "/v1/resource-states",
        headers=auth(token, "scientific"),
        json={
            "resource_id": resource,
            "state_type": "ALUMINUM",
            "quantity": {
                "value": "1e3",
                "unit": "t",
                "unit_registry_version": "CRR-UNITS-0.1",
            },
            "location_id": location,
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "MANUAL"},
        },
    )
    assert response.status_code == 201
    assert response.json()["data"]["quantity"]["value"] == "1E+3"


def test_transaction_rollback_preserves_canonical_state_when_outbox_conflicts() -> None:
    client, token, factory = make_client()
    resource_id = "res_rollback"
    with factory.begin() as session:
        session.add(
            OutboxEvent(
                id="evt_existing",
                event_type="resource.created",
                event_version=1,
                aggregate_type="Resource",
                aggregate_id=resource_id,
                aggregate_version=1,
                organization_id="org_a",
                actor_id="act_org_a",
                occurred_at=NOW,
                published_at=None,
                correlation_id="seed",
                causation_id=None,
                idempotency_key="seed",
                payload={"resource_id": resource_id},
                provenance={"source_type": "TEST"},
                schema_version="0.1",
            )
        )

    response = client.post(
        "/v1/resources",
        headers=auth(token, "rollback-resource"),
        json={
            "id": resource_id,
            "resource_type": "ALUMINUM",
            "provenance": {"source_type": "MANUAL"},
        },
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"

    with factory() as session:
        assert session.get(Resource, resource_id) is None
        assert session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.organization_id == "org_a",
                IdempotencyRecord.idempotency_key == "rollback-resource",
            )
        ) is None


def test_database_history_guards_reject_direct_transition_and_outbox_mutation() -> None:
    client, token, factory = make_client()
    location = client.post(
        "/v1/locations",
        headers=auth(token, "history-location"),
        json={"name": "Yard", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]["id"]
    resource = client.post(
        "/v1/resources",
        headers=auth(token, "history-resource"),
        json={"resource_type": "ALUMINUM", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]["id"]
    state = client.post(
        "/v1/resource-states",
        headers=auth(token, "history-state"),
        json={
            "resource_id": resource,
            "state_type": "SCRAP",
            "quantity": {"value": "1", "unit": "t", "unit_registry_version": "CRR-UNITS-0.1"},
            "location_id": location,
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "MANUAL"},
        },
    ).json()["data"]
    transition = client.post(
        f"/v1/resource-states/{state['id']}/transitions",
        headers=auth(token, "history-transition") | {"If-Match": '"version-1"'},
        json={
            "kind": "CORRECTION",
            "reason": "Audit correction",
            "occurred_at": "2026-10-17T13:00:00Z",
            "state_type": "SCRAP",
            "quantity": {"value": "1", "unit": "t", "unit_registry_version": "CRR-UNITS-0.1"},
            "location_id": location,
            "provenance": {"source_type": "MANUAL"},
        },
    )
    assert transition.status_code == 201

    with factory() as session:
        state_row = session.get(ResourceState, state["id"])
        event_row = session.scalar(
            select(OutboxEvent).where(OutboxEvent.idempotency_key == "history-transition")
        )
        assert state_row is not None and event_row is not None
        state_row.quantity_value = state_row.quantity_value + 1
        event_row.payload = {"tampered": True}
        try:
            session.commit()
        except Exception as exc:
            session.rollback()
            assert "immutable" in str(exc).lower()
        else:
            raise AssertionError("append-only database guards allowed history mutation")
