from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.optimization import (
    CandidateSet,
    OptimizationObjective,
    OptimizationPolicy,
    fingerprint_candidates,
    optimize_candidate_set,
)
from crr.domain.routing import RouteCandidate, RouteLeg, RouteStatus

NOW = datetime(2026, 10, 18, 12, tzinfo=UTC)


def candidate(candidate_id: str, status: RouteStatus = RouteStatus.FEASIBLE) -> RouteCandidate:
    return RouteCandidate(
        id=candidate_id,
        organization_id="org_a",
        source_resource_state_id="rst_a",
        target_demand_id="dem_a",
        legs=(RouteLeg("DIRECT", "rst_a", "A", "A"),),
        status=status,
        rejections=(),
        source_version=1,
        target_version=1,
        evaluated_at=NOW,
        provenance={"source": "TEST"},
    )


def policy(objective: OptimizationObjective, metric: str | None = None) -> OptimizationPolicy:
    return OptimizationPolicy(
        id="policy_1",
        version=1,
        objective=objective,
        calculation_version="1",
        metric=metric,
        weights=(),
        allow_negative=True,
        provenance={"source": "TEST"},
    )


def test_min_duration_is_deterministic_and_tie_breaks_by_id():
    items = (candidate("route_b"), candidate("route_a"))
    result = optimize_candidate_set(
        candidate_set=CandidateSet.from_candidates("org_a", items),
        policy=policy(OptimizationObjective.MIN_DURATION),
        metrics_by_candidate={
            "route_a": {"duration_seconds": Decimal("10")},
            "route_b": {"duration_seconds": Decimal("10")},
        },
        organization_id="org_a",
    )
    assert [item.candidate_id for item in result.ranked] == ["route_a", "route_b"]
    assert result.ranked[0].rank == 1


def test_infeasible_candidates_are_excluded():
    items = (candidate("route_a"), candidate("route_bad", RouteStatus.INFEASIBLE))
    result = optimize_candidate_set(
        candidate_set=CandidateSet.from_candidates("org_a", items),
        policy=policy(OptimizationObjective.MIN_DURATION),
        metrics_by_candidate={"route_a": {"duration_seconds": Decimal("10")}},
        organization_id="org_a",
    )
    assert [item.candidate_id for item in result.ranked] == ["route_a"]
    assert result.excluded_candidate_ids == ("route_bad",)


def test_max_metric_preserves_negative_values_when_allowed():
    result = optimize_candidate_set(
        candidate_set=CandidateSet.from_candidates(
            "org_a", (candidate("route_a"), candidate("route_b"))
        ),
        policy=policy(OptimizationObjective.MAX_METRIC, "economic_net"),
        metrics_by_candidate={
            "route_a": {"economic_net": Decimal("-10.00")},
            "route_b": {"economic_net": Decimal("-2.00")},
        },
        organization_id="org_a",
    )
    assert [item.candidate_id for item in result.ranked] == ["route_b", "route_a"]
    assert result.ranked[0].score == Decimal("-2.00")


def test_candidate_set_rejects_cross_tenant_and_tampering():
    foreign = RouteCandidate(
        id="foreign",
        organization_id="org_b",
        source_resource_state_id="rst_b",
        target_demand_id="dem_b",
        legs=(RouteLeg("DIRECT", "rst_b", "A", "A"),),
        status=RouteStatus.FEASIBLE,
        rejections=(),
        source_version=1,
        target_version=1,
        evaluated_at=NOW,
        provenance={"source": "TEST"},
    )
    with pytest.raises(TenantBoundaryError):
        CandidateSet.from_candidates("org_a", (foreign,))

    item = candidate("route_a")
    fingerprint = fingerprint_candidates((item,))
    with pytest.raises(DomainError):
        CandidateSet("org_a", (item,), fingerprint + "0")


def test_missing_or_non_finite_metric_is_rejected():
    item = candidate("route_a")
    with pytest.raises(DomainError):
        optimize_candidate_set(
            candidate_set=CandidateSet.from_candidates("org_a", (item,)),
            policy=policy(OptimizationObjective.MIN_DURATION),
            metrics_by_candidate={},
            organization_id="org_a",
        )

    with pytest.raises(DomainError):
        optimize_candidate_set(
            candidate_set=CandidateSet.from_candidates("org_a", (item,)),
            policy=policy(OptimizationObjective.MIN_DURATION),
            metrics_by_candidate={"route_a": {"duration_seconds": Decimal("NaN")}},
            organization_id="org_a",
        )


def test_wrong_tenant_cannot_optimize_candidate_set():
    with pytest.raises(TenantBoundaryError):
        optimize_candidate_set(
            candidate_set=CandidateSet.from_candidates("org_a", (candidate("route_a"),)),
            policy=policy(OptimizationObjective.MIN_DURATION),
            metrics_by_candidate={"route_a": {"duration_seconds": Decimal("1")}},
            organization_id="org_b",
        )
