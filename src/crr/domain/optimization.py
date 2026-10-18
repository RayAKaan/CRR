"""Deterministic optimization and ranking contracts over validated routes."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any

from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.routing import RouteCandidate, RouteStatus


class OptimizationObjective(StrEnum):
    MIN_DURATION = "MIN_DURATION"
    MAX_METRIC = "MAX_METRIC"
    MIN_METRIC = "MIN_METRIC"
    WEIGHTED = "WEIGHTED"


@dataclass(frozen=True, slots=True)
class OptimizationPolicy:
    id: str
    version: int
    objective: OptimizationObjective
    calculation_version: str
    metric: str | None
    weights: tuple[tuple[str, Decimal], ...]
    allow_negative: bool
    provenance: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.id or self.version < 1:
            raise DomainError("Optimization policy identity and positive version are required.")
        if not self.calculation_version.strip():
            raise DomainError("Optimization calculation version is required.")
        if self.objective is OptimizationObjective.MIN_DURATION:
            if self.metric not in (None, "duration_seconds"):
                raise DomainError("MIN_DURATION uses the duration_seconds metric.")
        elif self.objective in {OptimizationObjective.MAX_METRIC, OptimizationObjective.MIN_METRIC}:
            if not self.metric or not self.metric.strip():
                raise DomainError("A metric is required for metric optimization.")
        if self.objective is OptimizationObjective.WEIGHTED and not self.weights:
            raise DomainError("Weighted optimization requires at least one weight.")
        seen: set[str] = set()
        for name, weight in self.weights:
            if not name.strip() or name in seen:
                raise DomainError("Optimization weights must use unique non-empty metric names.")
            if (
                isinstance(weight, bool)
                or not isinstance(weight, Decimal)
                or not weight.is_finite()
            ):
                raise DomainError("Optimization weights must be finite exact decimals.")
            seen.add(name)


@dataclass(frozen=True, slots=True)
class CandidateSet:
    organization_id: str
    candidates: tuple[RouteCandidate, ...]
    fingerprint: str

    def __post_init__(self) -> None:
        if not self.organization_id:
            raise DomainError("Candidate set organization is required.")
        if len({candidate.id for candidate in self.candidates}) != len(self.candidates):
            raise DomainError("Candidate IDs must be unique.")
        if any(candidate.organization_id != self.organization_id for candidate in self.candidates):
            raise TenantBoundaryError("Candidate set contains another organization's route.")
        expected = fingerprint_candidates(self.candidates)
        if self.fingerprint != expected:
            raise DomainError("Candidate set fingerprint does not match its contents.")

    @classmethod
    def from_candidates(
        cls, organization_id: str, candidates: tuple[RouteCandidate, ...]
    ) -> CandidateSet:
        if any(candidate.organization_id != organization_id for candidate in candidates):
            raise TenantBoundaryError("Candidate set contains another organization's route.")
        return cls(organization_id, candidates, fingerprint_candidates(candidates))

    def validate_tenant(self, organization_id: str) -> None:
        if self.organization_id != organization_id:
            raise TenantBoundaryError("Candidate set belongs to another organization.")


def fingerprint_candidates(candidates: tuple[RouteCandidate, ...]) -> str:
    """Return a stable SHA-256 fingerprint over canonical candidate content."""
    canonical = []
    for candidate in sorted(candidates, key=lambda item: item.id):
        canonical.append(
            {
                "id": candidate.id,
                "organization_id": candidate.organization_id,
                "source_resource_state_id": candidate.source_resource_state_id,
                "target_demand_id": candidate.target_demand_id,
                "legs": [
                    {
                        "kind": leg.kind,
                        "object_id": leg.object_id,
                        "input_state_type": leg.input_state_type,
                        "output_state_type": leg.output_state_type,
                    }
                    for leg in candidate.legs
                ],
                "status": candidate.status.value,
                "rejections": [
                    {"code": item.code, "object_id": item.object_id, "message": item.message}
                    for item in candidate.rejections
                ],
                "source_version": candidate.source_version,
                "target_version": candidate.target_version,
                "evaluated_at": candidate.evaluated_at.isoformat(),
                "provenance": candidate.provenance,
            }
        )
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    candidate_id: str
    rank: int
    score: Decimal
    components: tuple[tuple[str, Decimal], ...]


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    candidate_set_fingerprint: str
    policy_id: str
    policy_version: int
    calculation_version: str
    ranked: tuple[RankedCandidate, ...]
    excluded_candidate_ids: tuple[str, ...]
    provenance: dict[str, Any]


def _score(
    policy: OptimizationPolicy, metrics: Mapping[str, Decimal]
) -> tuple[Decimal, tuple[tuple[str, Decimal], ...]]:
    metric_name = (
        "duration_seconds"
        if policy.objective is OptimizationObjective.MIN_DURATION
        else policy.metric
    )
    if policy.objective is OptimizationObjective.WEIGHTED:
        components = tuple((name, metrics[name] * weight) for name, weight in policy.weights)
        return sum((value for _, value in components), Decimal("0")), components
    if metric_name is None:
        raise DomainError("Optimization metric is required.")
    if metric_name not in metrics:
        raise DomainError(f"Optimization metric is unavailable: {metric_name}.")
    value = metrics[metric_name]
    return value, ((metric_name, value),)


def _excluded_ids(candidates: tuple[RouteCandidate, ...]) -> tuple[str, ...]:
    ids = [
        candidate.id
        for candidate in candidates
        if candidate.status is not RouteStatus.FEASIBLE
    ]
    return tuple(sorted(ids))


def optimize_candidate_set(
    *,
    candidate_set: CandidateSet,
    policy: OptimizationPolicy,
    metrics_by_candidate: Mapping[str, Mapping[str, Decimal]],
    organization_id: str,
) -> OptimizationResult:
    """Rank only feasible candidates using explicit deterministic metrics."""
    candidate_set.validate_tenant(organization_id)
    feasible = [item for item in candidate_set.candidates if item.status is RouteStatus.FEASIBLE]
    excluded = _excluded_ids(candidate_set.candidates)

    scored: list[tuple[str, Decimal, tuple[tuple[str, Decimal], ...]]] = []
    for candidate in feasible:
        raw_metrics = metrics_by_candidate.get(candidate.id)
        if raw_metrics is None:
            raise DomainError(f"Optimization metrics are missing for candidate: {candidate.id}.")
        metrics = dict(raw_metrics)
        for name, value in metrics.items():
            if isinstance(value, bool) or not isinstance(value, Decimal) or not value.is_finite():
                raise DomainError(f"Optimization metric must be a finite Decimal: {name}.")
        score, components = _score(policy, metrics)
        if not policy.allow_negative and score < 0:
            raise DomainError("Optimization policy does not allow negative scores.")
        scored.append((candidate.id, score, components))

    reverse = policy.objective in {OptimizationObjective.MAX_METRIC, OptimizationObjective.WEIGHTED}
    scored.sort(key=lambda item: ((-item[1]) if reverse else item[1], item[0]))

    ranked = tuple(
        RankedCandidate(candidate_id=item[0], rank=index, score=item[1], components=item[2])
        for index, item in enumerate(scored, start=1)
    )
    return OptimizationResult(
        candidate_set_fingerprint=candidate_set.fingerprint,
        policy_id=policy.id,
        policy_version=policy.version,
        calculation_version=policy.calculation_version,
        ranked=ranked,
        excluded_candidate_ids=excluded,
        provenance={
            "source": "CRR_DETERMINISTIC_OPTIMIZER",
            "policy_id": policy.id,
            "policy_version": policy.version,
            "candidate_set_fingerprint": candidate_set.fingerprint,
        },
    )
