# CRR Phase 3F — Optimization and Ranking Foundation Plan

**Status:** Planned  
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2  
**Base:** Phase 3E economic foundation merged to `main`

## 1. Objective

Establish the deterministic optimization/ranking layer that operates **only after hard-feasibility validation** and preserves candidate-set integrity.

This increment turns the Phase 3D candidate set plus Phase 3E economic computation into an auditable, computation-only ranking result. It does not create commercial commitments, reservations, execution records, or autonomous decisions.

## 2. Why this increment is required

The normative routing specification defines the sequence:

`candidate discovery → hard constraints → physical/capacity/time/logistics/regulatory feasibility → economics → optimization → decision support → ranked feasible routes`.

Phases 3A–3D establish deterministic candidate generation and hard feasibility. Phase 3E establishes exact, versioned economic computation. The remaining executable gap before bounded decision support is a deterministic optimization/ranking contract.

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

Implement an immutable optimization policy containing:

- objective identifier;
- objective direction;
- explicit version;
- deterministic weight configuration where applicable;
- calculation version;
- provenance.

Unknown objectives, invalid weights, non-finite numeric values, and ambiguous configuration are rejected.

### 4.2 Candidate-set integrity

Implement a fixed, content-addressable candidate-set representation containing:

- candidate IDs;
- candidate input versions;
- feasibility status;
- rejection information;
- economic-result references/values where supplied;
- set fingerprint;
- creation/evaluation timestamp.

A ranking operation must consume the declared candidate set and cannot discover or silently add candidates during scoring.

### 4.3 Deterministic objectives

Initial deterministic objectives are deliberately narrow and auditable:

- maximum economic net outcome when an explicit economic value is supplied;
- minimum total cost when an explicit cost is supplied;
- minimum elapsed route duration when route timing is supplied;
- deterministic weighted composite over explicitly supplied metrics.

No hidden defaults or external pricing/geographic services are introduced.

### 4.4 Feasibility gate

Only `FEASIBLE` candidates can receive a ranked position. Infeasible candidates remain visible as rejected inputs but cannot outrank feasible routes.

### 4.5 Stable tie-breaking

Equal scores MUST be resolved deterministically by candidate ID after the declared objective/weights. No runtime ordering, database order, hash order, or model confidence may affect ties.

### 4.6 API boundary

Extend the computation-only routing contract with an optional optimization request. The API continues to reference canonical route inputs and must not accept authoritative physical/economic facts inline.

The response exposes:

- fixed candidate-set fingerprint;
- optimization policy/version;
- ranked feasible candidates;
- score components;
- deterministic rank;
- excluded/infeasible candidates with reasons;
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
4. All candidate input versions remain exposed for auditability.
5. Objective and calculation versions are mandatory.
6. All authoritative numeric inputs remain exact decimals or explicitly typed deterministic durations.
7. NaN, infinity, floats where exact decimals are required, and malformed weights are rejected.
8. Currency and economic perspective are explicit when economics are ranked.
9. Negative economic outcomes remain mathematically visible; policy determines whether they are eligible.
10. Equal scores resolve by stable candidate ID.
11. Ranking performs no canonical-state mutation.
12. Cross-tenant candidate sets are rejected.
13. Candidate-set fingerprints are reproducible from canonicalized content.
14. Ranking provenance identifies the policy and input set used.

## 7. Testing strategy

Cover:

- valid single-objective ranking;
- weighted composite ranking;
- deterministic tie-breaking;
- infeasible-candidate exclusion;
- empty feasible set;
- negative economic outcomes;
- economic perspective/currency validation;
- invalid weights and non-finite values;
- candidate-set tampering/fingerprint mismatch;
- stale candidate versions;
- cross-tenant isolation;
- API least privilege and malformed optimization input;
- canonical input immutability;
- repeatability across identical requests;
- PostgreSQL/SQLite regression suite with existing migration/conformance gates.

## 8. Database boundary

No new persistence is required. Candidate sets and ranking results are derived computation. Existing canonical ResourceState, Demand, Capability, Transformation, and EconomicModel data remain authoritative.

## 9. Documentation synchronization

After implementation, audit and synchronize:

- `docs/CRR_DECISION_AND_ROUTING_SPEC.md`;
- `docs/CRR_API_CONTRACT.md`;
- `docs/CRR_VALIDATION_AND_INVARIANTS.md`;
- `docs/CRR_DOMAIN_MODEL.md`;
- `docs/CRR_CONFORMANCE_MATRIX.md`;
- `docs/CRR_DATA_FLOW_ARCHITECTURE.md`;
- `docs/CRR_SPECIFICATION_INDEX.md`.

Only normative changes required by the executable behavior will be made.

## 10. Definition of done

- Plan committed before implementation.
- Deterministic optimization domain contracts implemented.
- Fixed candidate-set integrity and fingerprinting implemented.
- Feasibility gate enforced.
- Objective/version/weight semantics explicit and validated.
- Stable deterministic ranking implemented.
- Economic perspective/currency semantics preserved.
- Routing API exposes ranking without persistence or mutation.
- Comprehensive domain/API/security/failure/regression tests pass.
- Ruff, format, mypy, pytest, migration lifecycle, SQLAlchemy alignment, PostgreSQL conformance, and full GitHub CI are green.
- Documentation and conformance evidence match actual behavior.
- PR opened for review; merge is left to the repository owner.

## 11. Execution order

1. Commit this plan first.
2. Audit Phase 3D routing and Phase 3E economic contracts against normative documents.
3. Implement the smallest complete optimization domain contracts.
4. Implement candidate-set canonicalization/fingerprinting and feasibility gate.
5. Add deterministic objectives and stable ranking.
6. Extend schemas/API without adding persistence.
7. Add domain/API/security/failure/conformance tests.
8. Run static, formatting, typing, full tests, migration lifecycle, and PostgreSQL conformance.
9. Diagnose and fix every CI failure without weakening tests or requirements.
10. Synchronize documentation only after behavior is proven.
11. Open the Phase 3F PR with complete closure evidence.
