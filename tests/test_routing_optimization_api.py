from test_routing_api import auth, make_client, seed_direct


def test_route_compute_optimization_returns_fixed_candidate_set_and_rank():
    client, token, engine = make_client("org_opt")
    seed_direct(engine, "org_opt")

    response = client.post(
        "/v1/routes/compute",
        headers=auth(token),
        json={
            "source_resource_state_id": "rst_a",
            "target_demand_id": "dem_a",
            "optimization": {
                "objective": "MIN_DURATION",
                "policy_id": "route-time",
                "policy_version": 1,
                "calculation_version": "1",
            },
        },
    )
    assert response.status_code == 200, response.text
    optimization = response.json()["data"]["optimization"]
    assert len(optimization["candidate_set_fingerprint"]) == 64
    assert optimization["ranked"][0]["rank"] == 1
    assert optimization["ranked"][0]["score"] == "0"
    assert optimization["excluded_candidate_ids"] == []


def test_route_compute_rejects_unknown_optimization_objective():
    client, token, engine = make_client("org_opt_invalid")
    seed_direct(engine, "org_opt_invalid")
    response = client.post(
        "/v1/routes/compute",
        headers=auth(token),
        json={
            "source_resource_state_id": "rst_a",
            "target_demand_id": "dem_a",
            "optimization": {
                "objective": "MAGIC",
                "policy_id": "route-time",
                "policy_version": 1,
                "calculation_version": "1",
            },
        },
    )
    assert response.status_code == 422


def test_route_compute_optimization_keeps_existing_least_privilege_boundary():
    client, token, engine = make_client("org_opt_scope", scopes=["resources:read"])
    seed_direct(engine, "org_opt_scope")
    response = client.post(
        "/v1/routes/compute",
        headers=auth(token),
        json={
            "source_resource_state_id": "rst_a",
            "target_demand_id": "dem_a",
            "optimization": {
                "objective": "MIN_DURATION",
                "policy_id": "route-time",
                "policy_version": 1,
                "calculation_version": "1",
            },
        },
    )
    assert response.status_code == 403
