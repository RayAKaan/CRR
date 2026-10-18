# CRR Phase 3F — Optimization and Ranking Foundation Plan

**Status:** Complete  
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2  
**Base:** Phase 3E economic foundation merged to `main`

## 1. Objective

Establish the deterministic optimization/ranking layer that operates **only after hard-feasibility validation** and preserves candidate-set integrity.

This increment turns the Phase 3D candidate set plus Phase 3E economic computation into an auditable, computation-only ranking result. It does not create commercial commitments, reservations, execution records, or autonomous decisions.

## 2. Why this increment is required

The normative routing sequence is:

`candidate discovery → hard constraints → physical/capacity/time/logistics/regulatory feasibility → economics → optimization → decision support → ranked feasible routes`.

Phases 3A–3D establish deterministic candidate generation and hard feasibility. Phase 3E establishes exact, versioned economic computation. Phase 3F closes the executable optimization/ranking boundary without crossing into decision acceptance or execution.

## 3. Architectural boundary

```text
Canonical route candidates
        ↓
Hard-feasibility gate
        ↓
Fixed candidate set
        ↓
Declared optimization objective / weights
        ↓
Deterministic scoring
        ↓
Stable ranking + auditable explanation
        ↓
Future decision support
```

Optimization MUST NOT legalize or physically validate an infeasible candidate. Infeasible candidates are never ranked as feasible. Ranking scores are derived values and are not physical truth.

## 4. Scope

### 4.1 Optimization policy contract

Implemented as an immutable policy containing objective, explicit version, calculation version, optional metric, deterministic weights, negative-score policy, and provenance.

Supported deterministic objectives are:

- `MIN_DURATION`;
- `MAX_METRIC`;
- `MIN_METRIC`;
- `WEIGHTED`.

Objective direction is intrinsic to the objective. Weighted policies use signed exact-decimal weights, making minimization/maximization of individual dimensions explicit without hidden defaults.

### 4.2 Candidate-set integrity

Implemented as a fixed, content-addressable candidate-set representation containing:

- candidate IDs;
- source/target references and versions;
- feasibility status;
- rejection information;
- route legs;
- evaluation timestamp;
- provenance;
- reproducible SHA-256 fingerprint.

A ranking operation consumes the declared candidate set and cannot discover or silently add candidates during scoring.

### 4.3 Deterministic objectives

The domain optimizer supports explicit deterministic metrics, including economic metrics supplied by a trusted upstream computation and route duration supplied by canonical transformation data.

The Phase 3F routing API intentionally exposes the bounded `MIN_DURATION` objective from canonical transformation durations. It does not accept authoritative economic values inline and does not pretend that an economic score exists when the route does not have one.

No hidden defaults or external pricing/geographic services are introduced.

### 4.4 Feasibility gate

Only `FEASIBLE` candidates can receive a ranked position. Infeasible candidates remain visible as excluded inputs with their rejection reasons.

### 4.5 Stable tie-breaking

Equal scores are resolved deterministically by candidate ID after the declared objective/weights. No runtime ordering, database order, hash order, or model confidence affects ties.

### 4.6 API boundary

`POST /v1/routes/compute` accepts an optional optimization request. It continues to reference canonical route inputs and does not accept authoritative physical/economic facts inline.

The response exposes:

- fixed candidate-set fingerprint;
- optimization policy/version;
- ranked feasible candidates;
- score components;
- deterministic rank;
- excluded/infeasible candidate IDs;
- evaluation provenance.

No ranking result is persisted as canonical state.

## 5. Explicit non-goals

- Jev/LLM decision support;
- opportunities/offers/agreements/transactions;
- reservations or capacity commitment;
- physical execution;
- evidence verification;
- external market/pricing providers;
- graph database or new infrastructure;
- probabilistic scoring;
- autonomous route selection.

## 6. Domain invariants

1. Optimization consumes only a fixed candidate set.
2. Infeasible candidates cannot receive a feasible rank.
3. Ranking cannot change hard-feasibility status.
4. Candidate input versions remain exposed for auditability.
5. Objective and calculation versions are mandatory.
6. Authoritative numeric inputs remain exact decimals or explicitly typed deterministic durations.
7. NaN, infinity, floats where exact decimals are required, and malformed weights are rejected.
8. Currency and economic perspective remain explicit when economic metrics are supplied by a trusted upstream result.
9. Negative economic outcomes remain mathematically visible; policy determines whether negative scores are eligible.
10. Equal scores resolve by stable candidate ID.
11. Ranking performs no canonical-state mutation.
12. Cross-tenant candidate sets are rejected.
13. Candidate-set fingerprints are reproducible from canonicalized content.
14. Ranking provenance identifies the policy and input set used.

## 7. Testing strategy and evidence

Implemented coverage includes:

- minimum-duration ranking;
- maximum metric ranking with negative economic values;
- weighted composite ranking with signed weights;
- deterministic tie-breaking;
- infeasible-candidate exclusion;
- empty feasible set;
- negative-score policy enforcement;
- invalid/non-finite metrics;
- candidate-set fingerprint tampering;
- cross-tenant candidate-set rejection;
- wrong-tenant optimization attempts;
- API unknown-objective validation;
- API least-privilege enforcement;
- API candidate-set fingerprint/rank response;
- canonical routing input preservation;
- existing full routing/regulatory regression suite.

## 8. Database boundary

No new persistence or migration is required. Candidate sets and ranking results are derived computation. Existing canonical ResourceState, Demand, Capability, Transformation, and EconomicModel data remain authoritative.

The PostgreSQL migration lifecycle and model-alignment gates remain part of CI and pass unchanged.

## 9. Documentation synchronization

Phase 3F behavior is documented by this closure plan and the executable routing/API contracts. The existing normative API contract already defines `/v1/routes/compute`, derived routing semantics, and optimization as downstream of feasibility. Phase 3F adds only the bounded deterministic ranking behavior implemented by the reference API; it does not introduce commercial or execution semantics.

## 10. Definition of done

- Plan committed before implementation: complete.
- Deterministic optimization domain contracts implemented: complete.
- Fixed candidate-set integrity and fingerprinting implemented: complete.
- Feasibility gate enforced: complete.
- Objective/version/weight semantics explicit and validated: complete.
- Stable deterministic ranking implemented: complete.
- Exact-decimal scoring semantics preserved: complete.
- Routing API exposes ranking without persistence or mutation: complete.
- Comprehensive domain/API/security/failure/regression tests pass: complete.
- Ruff, format, mypy, pytest, migration lifecycle, SQLAlchemy alignment, PostgreSQL conformance, and full GitHub CI are green: complete.
- Documentation and conformance evidence match actual behavior: complete.
- PR opened for review; merge remains with repository owner.

## 11. Execution order

1. Commit this plan first. **Complete.**
2. Audit Phase 3D routing and Phase 3E economic contracts against normative documents. **Complete.**
3. Implement deterministic optimization domain contracts. **Complete.**
4. Implement candidate-set canonicalization/fingerprinting and feasibility gate. **Complete.**
5. Add deterministic objectives and stable ranking. **Complete.**
6. Extend schemas/API without adding persistence. **Complete.**
7. Add domain/API/security/failure/conformance tests. **Complete.**
8. Run static, formatting, typing, full tests, migration lifecycle, and PostgreSQL conformance. **Complete.**
9. Diagnose and fix every CI failure without weakening tests or requirements. **Complete.**
10. Synchronize documentation after behavior was proven. **Complete.**
11. Open the Phase 3F PR with closure evidence. **Complete.**

## 12. Closure evidence

- Branch: `phase3f/optimization-ranking-foundation`
- PR: #17
- Final implementation commit before CI: `e649c7fe973e302a99960e1a8a0d1a2fbfee49bb`
- Final GitHub Actions run: `39143722547`
- Final CI conclusion: **success**
- Ruff check: PASS
- Ruff format check: PASS
- Mypy: PASS
- Pytest: PASS
- PostgreSQL migration upgrade: PASS
- PostgreSQL migration downgrade: PASS
- PostgreSQL rebuild: PASS
- SQLAlchemy/model alignment: PASS
- PostgreSQL conformance: PASS

An intermediate test failure was caused by a test fixture violating the existing RouteCandidate invariant that infeasible candidates must carry rejection reasons. The fixture was corrected to use a contractual rejection; no production invariant or test requirement was weakened.
