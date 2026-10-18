# CRR Phase 3G — Bounded Decision Support Foundation Plan

**Status:** Complete
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Base:** Phase 3F deterministic optimization and ranking foundation merged to `main`

## 1. Objective

Establish the first executable decision-support boundary over the already validated, economically evaluated, and deterministically ranked route candidate set.

The increment MUST remain advisory and computation-only. It may explain the leading feasible route and meaningful alternatives, but it MUST NOT create a commitment, reservation, transaction, execution record, physical action, or autonomous route selection.

## 2. Why this increment is next

The normative routing sequence is:

`candidate discovery → hard constraints → physical/capacity/time/logistics/regulatory feasibility → economics → optimization → decision support → ranked feasible routes`.

Phases 3A–3D establish candidate generation and hard feasibility, Phase 3E establishes deterministic economic computation, and Phase 3F establishes deterministic optimization/ranking. The remaining boundary before commercial/execution semantics is bounded decision support.

## 3. Architectural boundary

```text
Canonical route candidates
        ↓
Hard-feasibility gate
        ↓
Economic computation
        ↓
Deterministic optimization/ranking
        ↓
Bounded decision support
        ↓
Human decision / future execution boundary
```

Decision support consumes an immutable optimization result and its fixed candidate-set fingerprint. It MUST NOT rediscover candidates, alter feasibility, recompute authoritative physical facts, mutate canonical state, or bypass hard constraints.

## 4. Scope

### 4.1 Decision mode contract

Add an explicit optional `decision_mode` to the routing computation request. The initial supported mode is `ADVISORY`. Omission preserves the existing ranking-only response.

### 4.2 Advisory result

The advisory result exposes:

- candidate-set fingerprint;
- selected policy and calculation version;
- leading feasible candidate, if one exists;
- ordered alternatives already present in the ranked result;
- deterministic rationale derived only from rank and score components;
- explicit trade-off information for alternatives;
- hard-feasibility exclusions and their reasons;
- human-review requirement;
- provenance identifying the source ranking and advisory calculation version.

The word “leading” is an advisory presentation of the first deterministic rank, not an authorization or execution decision.

### 4.3 Deterministic rationale

Rationale generation MUST be deterministic. It may state that a candidate ranked first under the declared objective, identify its score/components, and identify alternative candidates with their relative scores. It MUST NOT invent facts, infer legal permission, fabricate confidence, or claim execution readiness beyond the validated candidate state.

### 4.4 Safety and uncertainty boundary

Any infeasible candidate remains excluded. Missing ranked candidates, stale/tampered candidate-set fingerprints, cross-tenant inputs, or invalid optimization results are hard failures. Advisory output MUST carry an explicit human-review requirement.

No probability or model confidence is introduced in this increment.

### 4.5 API boundary

`POST /v1/routes/compute` remains computation-only. When `decision_mode=ADVISORY`, the response adds an advisory object derived from the same optimization result already returned by the endpoint.

No new persistence or migration is introduced.

## 5. Explicit non-goals

- Jev/LLM inference or model-generated decisions;
- autonomous route selection;
- opportunities, offers, agreements, transactions, reservations, or commitments;
- physical execution;
- evidence verification;
- external pricing, geographic, or market services;
- probabilistic confidence scoring;
- mutation of ResourceState, Demand, Capability, Transformation, or economic models;
- new infrastructure or persistence.

## 6. Domain invariants

1. Advisory output consumes only the declared optimization result.
2. A candidate can be advisory only if it already has a feasible rank.
3. Advisory output cannot change feasibility or ranking.
4. Candidate-set fingerprint, policy ID/version, and calculation version remain attached to the advisory.
5. No advisory result crosses organization boundaries.
6. The leading candidate is presentation-level guidance, not an authorization or commitment.
7. All numeric values remain exact decimals.
8. Rationale is deterministic and derived from validated ranking data.
9. Infeasible candidates remain excluded and their rejection reasons remain visible.
10. Human review is mandatory for the advisory mode.
11. No canonical-state mutation occurs.
12. No external facts are silently introduced.

## 7. Testing strategy

Coverage MUST include:

- advisory result for a ranked feasible set;
- empty feasible set produces an explicit no-feasible-route advisory;
- deterministic rationale and alternative ordering;
- exact score/component preservation;
- infeasible candidates never become advisory candidates;
- candidate-set fingerprint and optimization provenance preservation;
- cross-tenant rejection;
- invalid/tampered optimization result rejection;
- API advisory-mode response;
- API omission preserves existing behavior;
- least-privilege `routes:compute` enforcement;
- canonical routing input remains unchanged;
- full existing routing, regulatory, economic, and optimization regression suite.

PostgreSQL migration lifecycle and SQLAlchemy alignment remain mandatory CI gates even though this increment adds no persistence.

## 8. Database boundary

No new persistence or migration is required. Decision advisories are derived computation and are not canonical state.

## 9. Documentation synchronization

The existing decision/routing specification already places decision support after optimization and before future execution semantics. This increment adds no conflicting normative semantics; it implements the bounded deterministic advisory boundary already implied by the routing architecture.

## 10. Definition of done

- Plan committed before implementation.
- Immutable bounded decision-support domain contract implemented.
- Advisory result preserves candidate-set and optimization provenance.
- Deterministic rationale and alternatives implemented.
- Human-review requirement explicit.
- API extension is computation-only and backward-compatible when decision mode is omitted.
- No canonical mutation, persistence, execution, or autonomous selection introduced.
- Comprehensive domain/API/security/failure/regression tests pass.
- Ruff, format, mypy, pytest, migration lifecycle, SQLAlchemy alignment, PostgreSQL conformance, and full GitHub CI are green.
- Documentation closure evidence matches actual behavior.
- PR opened for review; merge remains with repository owner.

## 11. Execution order

1. Commit this plan first.
2. Audit Phase 3D–3F routing, regulatory, economic, and optimization contracts against the normative documents.
3. Implement immutable decision-support domain contracts.
4. Add deterministic advisory construction over `OptimizationResult`.
5. Extend routing request/response schemas without persistence.
6. Add domain/API/security/failure/conformance tests.
7. Run static, formatting, typing, full tests, migration lifecycle, and PostgreSQL conformance.
8. Diagnose and fix every CI failure without weakening requirements.
9. Synchronize documentation after behavior is proven.
10. Open the Phase 3G PR with closure evidence.

## 12. Closure evidence

**PR:** #18 — Phase 3G: bounded deterministic decision support

**Final implementation commit:** `b717b9eb61717705a7a464487437dc49619d831e`

**Final fully green GitHub Actions run:** `39146549405`

### Test job

- Ruff check: PASS
- Ruff format check: PASS
- mypy: PASS
- pytest: PASS

### PostgreSQL job

- migration upgrade: PASS
- migration downgrade: PASS
- database rebuild: PASS
- SQLAlchemy/model alignment: PASS
- PostgreSQL conformance: PASS

### Closure notes

Intermediate CI failures were diagnosed and corrected without weakening requirements or removing tests:

1. Ruff import/line-length issues in the new decision-support and API test surface were corrected.
2. Ruff formatter differences were corrected to the repository's canonical formatting.
3. mypy correctly identified the need for an explicitly variadic rationale tuple type; the domain contract was corrected rather than suppressing the error.
4. The final run `39146549405` is fully green across both test and PostgreSQL jobs.

No migration, persistence, canonical-state mutation, reservation, transaction, execution, autonomous route selection, external factual source, probabilistic confidence, or Jev/LLM inference was introduced.
