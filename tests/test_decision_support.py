from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crr.domain.decision_support import DecisionMode, build_decision_advisory
from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.optimization import (
    CandidateSet,
    OptimizationObjective,
    OptimizationPolicy,
    optimize_candidate_set,
)
from crr.domain.routing import Rejection, RouteCandidate, RouteLeg, RouteStatus

NOW = datetime(2026, 10, 18, 12, tzinfo=UTC)


def candidate(candidate_id: str, status: RouteStatus = RouteStatus.FEASIBLE) -> RouteCandidate:
    rejections = (
        (Rejection("TEST_INFEASIBLE", candidate_id, "Test rejection"),)
        if status is RouteStatus.INFEASIBLE
        else ()
    )
    return RouteCandidate(
        id=candidate_id,
        organization_id="org_a",
        source_resource_state_id="rst_a",
        target_demand_id="dem_a",
        legs=(RouteLeg("DIRECT", "rst_a", "A", "A"),),
        status=status,
        rejections=rejections,
        source_version=1,
        target_version=1,
        evaluated_at=NOW,
        provenance={"source": "TEST"},
    )


def policy() -> OptimizationPolicy:
    return OptimizationPolicy(
        id="policy_1",
        version=1,
        objective=OptimizationObjective.MIN_DURATION,
        calculation_version="1",
        metric=None,
        weights=(),
        allow_negative=False,
        provenance={"source": "TEST"},
    )


def test_advisory_is_deterministic_and_requires_human_review():
    candidates = (candidate("route_b"), candidate("route_a"))
    candidate_set = CandidateSet.from_candidates("org_a", candidates)
    optimization_policy = policy()
    result = optimize_candidate_set(
        candidate_set=candidate_set,
        policy=optimization_policy,
        metrics_by_candidate={
            "route_a": {"duration_seconds": Decimal("10")},
            "route_b": {"duration_seconds": Decimal("20")},
        },
        organization_id="org_a",
    )

    advisory = build_decision_advisory(
        candidate_set=candidate_set,
        policy=optimization_policy,
        optimization_result=result,
        organization_id="org_a",
    )

    assert advisory.mode is DecisionMode.ADVISORY
    assert advisory.leading_candidate_id == "route_a"
    assert [item.candidate_id for item in advisory.alternatives] == ["route_a", "route_b"]
    assert advisory.alternatives[0].score == Decimal("10")
    assert advisory.human_review_required is True
    assert advisory.candidate_set_fingerprint == candidate_set.fingerprint
    assert "lowest validated duration" in advisory.rationale[0]


def test_empty_feasible_set_has_no_leading_candidate():
    candidates = (candidate("route_bad", RouteStatus.INFEASIBLE),)
    candidate_set = CandidateSet.from_candidates("org_a", candidates)
    optimization_policy = policy()
    result = optimize_candidate_set(
        candidate_set=candidate_set,
        policy=optimization_policy,
        metrics_by_candidate={},
        organization_id="org_a",
    )

    advisory = build_decision_advisory(
        candidate_set=candidate_set,
        policy=optimization_policy,
        optimization_result=result,
        organization_id="org_a",
    )

    assert advisory.leading_candidate_id is None
    assert advisory.alternatives == ()
    assert advisory.excluded_candidate_ids == ("route_bad",)
    assert "No feasible route" in advisory.rationale[0]


def test_advisory_rejects_cross_tenant_and_tampered_results():
    candidate_set = CandidateSet.from_candidates("org_a", (candidate("route_a"),))
    optimization_policy = policy()
    result = optimize_candidate_set(
        candidate_set=candidate_set,
        policy=optimization_policy,
        metrics_by_candidate={"route_a": {"duration_seconds": Decimal("10")}},
        organization_id="org_a",
    )

    with pytest.raises(TenantBoundaryError):
        build_decision_advisory(
            candidate_set=candidate_set,
            policy=optimization_policy,
            optimization_result=result,
            organization_id="org_b",
        )

    tampered = type(result)(
        candidate_set_fingerprint="tampered",
        policy_id=result.policy_id,
        policy_version=result.policy_version,
        calculation_version=result.calculation_version,
        ranked=result.ranked,
        excluded_candidate_ids=result.excluded_candidate_ids,
        provenance=result.provenance,
    )
    with pytest.raises(DomainError):
        build_decision_advisory(
            candidate_set=candidate_set,
            policy=optimization_policy,
            optimization_result=tampered,
            organization_id="org_a",
        )


def test_advisory_cannot_surface_infeasible_rank():
    candidate_set = CandidateSet.from_candidates("org_a", (candidate("route_a"),))
    optimization_policy = policy()
    result = optimize_candidate_set(
        candidate_set=candidate_set,
        policy=optimization_policy,
        metrics_by_candidate={"route_a": {"duration_seconds": Decimal("10")}},
        organization_id="org_a",
    )
    bad_result = type(result)(
        candidate_set_fingerprint=result.candidate_set_fingerprint,
        policy_id=result.policy_id,
        policy_version=result.policy_version,
        calculation_version=result.calculation_version,
        ranked=tuple(
            [
                type(result.ranked[0])(
                    candidate_id="route_bad",
                    rank=1,
                    score=Decimal("1"),
                    components=(("duration_seconds", Decimal("1")),),
                )
            ]
        ),
        excluded_candidate_ids=(),
        provenance=result.provenance,
    )
    with pytest.raises(DomainError):
        build_decision_advisory(
            candidate_set=candidate_set,
            policy=optimization_policy,
            optimization_result=bad_result,
            organization_id="org_a",
        )
