from datetime import UTC, datetime
from hashlib import sha256

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from crr.api import create_app
from crr.models import Actor, APIKey, Base, Organization


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


def test_api_creates_tenant_scoped_state_and_audited_transition() -> None:
    client, token, _engine = make_client()
    response = client.post(
        "/v1/locations",
        headers=headers(token, "loc-1"),
        json={"name": "Yard A", "provenance": {"source_type": "MANUAL"}},
    )
    assert response.status_code == 201
    location_id = response.json()["data"]["id"]

    response = client.post(
        "/v1/resources",
        headers=headers(token, "res-1"),
        json={"resource_type": "ALUMINUM", "provenance": {"source_type": "MANUAL"}},
    )
    assert response.status_code == 201
    resource_id = response.json()["data"]["id"]

    response = client.post(
        "/v1/resource-states",
        headers=headers(token, "state-1"),
        json={
            "resource_id": resource_id,
            "state_type": "MIXED_SCRAP",
            "quantity": {"value": "100.000", "unit": "t", "unit_registry_version": "CRR-UNITS-0.1"},
            "location_id": location_id,
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "MANUAL"},
        },
    )
    assert response.status_code == 201, response.text
    state = response.json()["data"]
    assert state["quantity"]["value"] == "100.000"

    transition_payload = {
        "kind": "PHYSICAL_CHANGE",
        "reason": "Sorted and weighed at facility",
        "occurred_at": "2026-10-17T13:00:00Z",
        "state_type": "MIXED_SCRAP",
        "quantity": {"value": "100.000", "unit": "t", "unit_registry_version": "CRR-UNITS-0.1"},
        "location_id": location_id,
        "provenance": {"source_type": "API", "record_id": "wb-1"},
    }
    response = client.post(
        f"/v1/resource-states/{state['id']}/transitions",
        headers=headers(token, "transition-1") | {"If-Match": '"version-1"'},
        json=transition_payload,
    )
    assert response.status_code == 201, response.text
    successor = response.json()["data"]
    assert successor["version"] == 2
    assert successor["predecessor_state_ids"] == [state["id"]]

    replay = client.post(
        f"/v1/resource-states/{state['id']}/transitions",
        headers=headers(token, "transition-1") | {"If-Match": '"version-1"'},
        json=transition_payload,
    )
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == successor["id"]

    history = client.get(
        f"/v1/resources/{resource_id}/resource-states",
        headers=headers(token),
    )
    assert [item["id"] for item in history.json()["data"]] == [state["id"], successor["id"]]


def test_api_rejects_float_negative_and_cross_tenant_reads() -> None:
    client, token, _engine = make_client()
    location = client.post(
        "/v1/locations",
        headers=headers(token, "loc"),
        json={"name": "Yard", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]["id"]
    resource = client.post(
        "/v1/resources",
        headers=headers(token, "resource"),
        json={"resource_type": "ALUMINUM", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]["id"]
    invalid = client.post(
        "/v1/resource-states",
        headers=headers(token, "negative"),
        json={
            "resource_id": resource,
            "state_type": "ALUMINUM",
            "quantity": {"value": "-1", "unit": "t", "unit_registry_version": "CRR-UNITS-0.1"},
            "location_id": location,
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "MANUAL"},
        },
    )
    assert invalid.status_code == 422
    for key, value, unit in (("float", 1.25, "t"), ("unit", "1", "lb")):
        rejected = client.post(
            "/v1/resource-states",
            headers=headers(token, key),
            json={
                "resource_id": resource,
                "state_type": "ALUMINUM",
                "quantity": {
                    "value": value,
                    "unit": unit,
                    "unit_registry_version": "CRR-UNITS-0.1",
                },
                "location_id": location,
                "effective_at": "2026-10-17T12:00:00Z",
                "provenance": {"source_type": "MANUAL"},
            },
        )
        assert rejected.status_code == 422

    other, other_token, _other_engine = make_client("org_b")
    hidden = other.get(f"/v1/resources/{resource}/resource-states", headers=headers(other_token))
    assert hidden.status_code == 404


def test_actor_idempotency_authorization_and_key_reuse_conflict() -> None:
    client, token, _engine = make_client()
    actor_payload = {"name": "Operator", "role": "OPERATOR"}
    created = client.post("/v1/actors", headers=headers(token, "actor-1"), json=actor_payload)
    assert created.status_code == 201, created.text
    replay = client.post("/v1/actors", headers=headers(token, "actor-1"), json=actor_payload)
    assert replay.status_code == 200
    assert replay.json()["data"]["id"] == created.json()["data"]["id"]
    conflict = client.post(
        "/v1/actors",
        headers=headers(token, "actor-1"),
        json={"name": "Verifier", "role": "VERIFIER"},
    )
    assert conflict.status_code == 409
    assert client.get("/v1/organizations/org_a").status_code == 401


def test_transition_idempotency_is_bound_to_predecessor_and_stale_versions() -> None:
    client, token, _engine = make_client()
    location_id = client.post(
        "/v1/locations",
        headers=headers(token, "l"),
        json={"name": "Yard", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]["id"]
    resource_id = client.post(
        "/v1/resources",
        headers=headers(token, "r"),
        json={"resource_type": "ALUMINUM", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]["id"]
    state = client.post(
        "/v1/resource-states",
        headers=headers(token, "s"),
        json={
            "resource_id": resource_id,
            "state_type": "SCRAP",
            "quantity": {"value": "1", "unit": "t", "unit_registry_version": "CRR-UNITS-0.1"},
            "location_id": location_id,
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "MANUAL"},
        },
    ).json()["data"]
    payload = {
        "kind": "CORRECTION",
        "reason": "Scale check",
        "occurred_at": "2026-10-17T13:00:00Z",
        "state_type": "SCRAP",
        "quantity": {"value": "1", "unit": "t", "unit_registry_version": "CRR-UNITS-0.1"},
        "location_id": location_id,
        "provenance": {"source_type": "MANUAL"},
    }
    transition_headers = headers(token, "t1") | {"If-Match": '"version-1"'}
    success = client.post(
        f"/v1/resource-states/{state['id']}/transitions", headers=transition_headers, json=payload
    )
    assert success.status_code == 201, success.text
    other_target = client.post(
        "/v1/resource-states/rst_other/transitions", headers=transition_headers, json=payload
    )
    assert other_target.status_code == 409
    stale = client.post(
        f"/v1/resource-states/{state['id']}/transitions",
        headers=headers(token, "t2") | {"If-Match": '"version-1"'},
        json=payload,
    )
    assert stale.status_code == 412


def test_cross_tenant_references_are_rejected_on_creation() -> None:
    client_a, token_a, _engine_a = make_client("org_a")
    client_b, token_b, _engine_b = make_client("org_b")
    resource_id = client_a.post(
        "/v1/resources",
        headers=headers(token_a, "resource-a"),
        json={"resource_type": "ALUMINUM", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]["id"]
    location_id = client_b.post(
        "/v1/locations",
        headers=headers(token_b, "location-b"),
        json={"name": "Yard B", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]["id"]
    response = client_b.post(
        "/v1/resource-states",
        headers=headers(token_b, "state-b"),
        json={
            "resource_id": resource_id,
            "state_type": "ALUMINUM",
            "quantity": {
                "value": "1",
                "unit": "t",
                "unit_registry_version": "CRR-UNITS-0.1",
            },
            "location_id": location_id,
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "MANUAL"},
        },
    )
    assert response.status_code == 404


def test_zero_quantity_historical_state_is_accepted() -> None:
    client, token, _engine = make_client()
    location_id = client.post(
        "/v1/locations",
        headers=headers(token, "location-zero"),
        json={"name": "Empty Yard", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]["id"]
    resource_id = client.post(
        "/v1/resources",
        headers=headers(token, "resource-zero"),
        json={"resource_type": "ALUMINUM", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]["id"]
    response = client.post(
        "/v1/resource-states",
        headers=headers(token, "state-zero"),
        json={
            "resource_id": resource_id,
            "state_type": "DEPLETED",
            "quantity": {
                "value": "0",
                "unit": "t",
                "unit_registry_version": "CRR-UNITS-0.1",
            },
            "location_id": location_id,
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "MANUAL"},
        },
    )
    assert response.status_code == 201, response.text
    assert response.json()["data"]["quantity"]["value"] == "0"


def test_untrusted_request_id_is_replaced_with_safe_generated_id() -> None:
    client, token, _engine = make_client()
    response = client.get(
        "/v1/organizations/org_a",
        headers=headers(token) | {"X-Request-ID": "x" * 300},
    )
    assert response.status_code == 200
    request_id = response.headers["X-Request-ID"]
    assert request_id.startswith("req_")
    assert len(request_id) <= 40


def test_foundation_objects_have_tenant_scoped_detail_reads() -> None:
    client, token, _engine = make_client()
    actor = client.post(
        "/v1/actors",
        headers=headers(token, "actor-read-create"),
        json={"name": "Operator", "role": "OPERATOR"},
    ).json()["data"]
    location = client.post(
        "/v1/locations",
        headers=headers(token, "location-read-create"),
        json={"name": "Yard", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]
    resource = client.post(
        "/v1/resources",
        headers=headers(token, "resource-read-create"),
        json={"resource_type": "ALUMINUM", "provenance": {"source_type": "MANUAL"}},
    ).json()["data"]
    state = client.post(
        "/v1/resource-states",
        headers=headers(token, "state-read-create"),
        json={
            "resource_id": resource["id"],
            "state_type": "SCRAP",
            "quantity": {
                "value": "2.5",
                "unit": "t",
                "unit_registry_version": "CRR-UNITS-0.1",
            },
            "location_id": location["id"],
            "effective_at": "2026-10-17T12:00:00Z",
            "provenance": {"source_type": "MANUAL"},
        },
    ).json()["data"]
    for path, object_id in (
        ("actors", actor["id"]),
        ("locations", location["id"]),
        ("resources", resource["id"]),
        ("resource-states", state["id"]),
    ):
        response = client.get(f"/v1/{path}/{object_id}", headers=headers(token))
        assert response.status_code == 200, response.text
    wrong_tenant, other_token, _other_engine = make_client("org_b")
    hidden = wrong_tenant.get(f"/v1/resource-states/{state['id']}", headers=headers(other_token))
    assert hidden.status_code == 404


def test_collection_reads_are_tenant_scoped_and_cursor_paged() -> None:
    client_a, token_a, _engine_a = make_client("org_a")
    client_b, token_b, _engine_b = make_client("org_b")
    for key, name in (("loc-a1", "Yard A1"), ("loc-a2", "Yard A2")):
        created = client_a.post(
            "/v1/locations",
            headers=headers(token_a, key),
            json={"name": name, "provenance": {"source_type": "MANUAL"}},
        )
        assert created.status_code == 201
    client_b.post(
        "/v1/locations",
        headers=headers(token_b, "loc-b"),
        json={"name": "Yard B", "provenance": {"source_type": "MANUAL"}},
    )
    first = client_a.get("/v1/locations?limit=1", headers=headers(token_a))
    assert first.status_code == 200
    first_page = first.json()
    assert len(first_page["data"]) == 1
    assert first_page["pagination"]["has_more"] is True
    second = client_a.get(
        "/v1/locations",
        params={"limit": 1, "cursor": first_page["pagination"]["cursor"]},
        headers=headers(token_a),
    )
    assert second.status_code == 200
    second_page = second.json()
    assert len(second_page["data"]) == 1
    assert second_page["data"][0]["id"] != first_page["data"][0]["id"]
    assert second_page["pagination"]["has_more"] is False
    resources_b = client_b.get("/v1/resources", headers=headers(token_b))
    assert resources_b.json()["data"] == []


def test_api_key_scopes_are_least_privilege() -> None:
    client, token, _engine = make_client("org_limited", scopes=["resources:read"])
    assert client.get("/v1/resources", headers=headers(token)).status_code == 200
    assert client.get("/v1/locations", headers=headers(token)).status_code == 403
    denied_write = client.post(
        "/v1/resources",
        headers=headers(token, "resource-write"),
        json={"resource_type": "ALUMINUM", "provenance": {"source_type": "MANUAL"}},
    )
    assert denied_write.status_code == 403
