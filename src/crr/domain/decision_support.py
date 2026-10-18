"""Bounded deterministic decision support over validated ranked routes."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any

from crr.domain.errors import DomainError
from crr.domain.optimization import (
    CandidateSet,
    OptimizationObjective,
    OptimizationPolicy,
    OptimizationResult,
)
from crr.domain.routing import RouteStatus


class DecisionMode(StrEnum):
    """Supported decision-support presentation modes."""

    ADVISORY = "ADVISORY"


@dataclass(frozen=True, slots=True)
class AdvisoryAlternative:
    """A ranked feasible alternative surfaced for human comparison."""

    candidate_id: str
    rank: int
    score: Decimal
    components: tuple[tuple[str, Decimal], ...]

    def __post_init__(self) -> None:
        if not self.candidate_id or self.rank < 1:
            raise DomainError("Advisory alternative identity and positive rank are required.")
        if not isinstance(self.score, Decimal) or not self.score.is_finite():
            raise DomainError("Advisory scores must be finite exact decimals.")
        for name, value in self.components:
            if not name or not isinstance(value, Decimal) or not value.is_finite():
                raise DomainError("Advisory score components must be finite exact decimals.")


@dataclass(frozen=True, slots=True)
class DecisionAdvisory:
    """Immutable advisory presentation; never an authorization or execution decision."""

    mode: DecisionMode
    candidate_set_fingerprint: str
    policy_id: str
    policy_version: int
    calculation_version: str
    leading_candidate_id: str | None
    alternatives: tuple[AdvisoryAlternative, ...]
    excluded_candidate_ids: tuple[str, ...]
    rationale: tuple[str, ...]
    human_review_required: bool
    provenance: dict[str, Any]

    def __post_init__(self) -> None:
        if not self.candidate_set_fingerprint:
            raise DomainError("Decision advisory requires a candidate-set fingerprint.")
        if not self.policy_id or self.policy_version < 1:
            raise DomainError("Decision advisory requires a valid policy identity.")
        if not self.calculation_version.strip():
            raise DomainError("Decision advisory requires a calculation version.")
        if not self.human_review_required:
            raise DomainError("Decision advisory must require human review.")
        if self.leading_candidate_id is not None:
            if (
                not self.alternatives
                or self.alternatives[0].candidate_id != self.leading_candidate_id
            ):
                raise DomainError(
                    "The leading advisory candidate must be the first ranked alternative."
                )
        if len({item.candidate_id for item in self.alternatives}) != len(self.alternatives):
            raise DomainError("Advisory candidate IDs must be unique.")


def _objective_rationale(
    policy: OptimizationPolicy, leading: AdvisoryAlternative
) -> str:
    if policy.objective is OptimizationObjective.MIN_DURATION:
        return (
            f"{leading.candidate_id} ranks first because it has the lowest validated "
            f"duration score of {leading.score}."
        )
    if policy.objective is OptimizationObjective.MAX_METRIC:
        return (
            f"{leading.candidate_id} ranks first because it has the highest validated "
            f"{policy.metric} score of {leading.score}."
        )
    if policy.objective is OptimizationObjective.MIN_METRIC:
        return (
            f"{leading.candidate_id} ranks first because it has the lowest validated "
            f"{policy.metric} score of {leading.score}."
        )
    return (
        f"{leading.candidate_id} ranks first under the declared weighted policy "
        f"with a validated composite score of {leading.score}."
    )


def build_decision_advisory(
    *,
    candidate_set: CandidateSet,
    policy: OptimizationPolicy,
    optimization_result: OptimizationResult,
    organization_id: str,
) -> DecisionAdvisory:
    """Build deterministic advisory output from one fixed ranked candidate set."""
    candidate_set.validate_tenant(organization_id)
    if optimization_result.candidate_set_fingerprint != candidate_set.fingerprint:
        raise DomainError(
            "Decision advisory candidate-set fingerprint does not match optimization result."
        )
    if (
        optimization_result.policy_id != policy.id
        or optimization_result.policy_version != policy.version
    ):
        raise DomainError("Decision advisory policy does not match optimization result.")
    if optimization_result.calculation_version != policy.calculation_version:
        raise DomainError(
            "Decision advisory calculation version does not match optimization result."
        )

    candidates_by_id = {item.id: item for item in candidate_set.candidates}
    ranked_ids = {item.candidate_id for item in optimization_result.ranked}
    if any(
        item.candidate_id not in candidates_by_id
        or candidates_by_id[item.candidate_id].status is not RouteStatus.FEASIBLE
        for item in optimization_result.ranked
    ):
        raise DomainError("Decision advisory cannot surface a non-feasible candidate.")
    if set(optimization_result.excluded_candidate_ids) != {
        item.id for item in candidate_set.candidates if item.status is not RouteStatus.FEASIBLE
    }:
        raise DomainError("Decision advisory exclusions do not match the fixed candidate set.")
    if ranked_ids & set(optimization_result.excluded_candidate_ids):
        raise DomainError("Decision advisory ranked candidates overlap excluded candidates.")

    alternatives = tuple(
        AdvisoryAlternative(
            candidate_id=item.candidate_id,
            rank=item.rank,
            score=item.score,
            components=item.components,
        )
        for item in optimization_result.ranked
    )
    leading = alternatives[0] if alternatives else None
    if leading is None:
        rationale = (
            "No feasible route received a rank; the advisory cannot recommend a route.",
        )
        leading_id = None
    else:
        rationale = (
            _objective_rationale(policy, leading),
            f"{len(alternatives)} feasible route(s) were ranked deterministically.",
        )
        if len(alternatives) > 1:
            rationale += (
                f" {len(alternatives) - 1} alternative(s) remain available for human comparison.",
            )
        leading_id = leading.candidate_id

    return DecisionAdvisory(
        mode=DecisionMode.ADVISORY,
        candidate_set_fingerprint=candidate_set.fingerprint,
        policy_id=policy.id,
        policy_version=policy.version,
        calculation_version=policy.calculation_version,
        leading_candidate_id=leading_id,
        alternatives=alternatives,
        excluded_candidate_ids=optimization_result.excluded_candidate_ids,
        rationale=rationale,
        human_review_required=True,
        provenance={
            "source": "CRR_DETERMINISTIC_DECISION_SUPPORT",
            "decision_mode": DecisionMode.ADVISORY.value,
            "candidate_set_fingerprint": candidate_set.fingerprint,
            "policy_id": policy.id,
            "policy_version": policy.version,
            "calculation_version": policy.calculation_version,
        },
    )
