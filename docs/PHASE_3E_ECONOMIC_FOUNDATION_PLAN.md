# CRR Phase 3E — Economic Foundation Plan

**Status:** Complete
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Base:** Phase 3D routing API and regulatory/safety closure merged to `main`
**Implementation:** PR #16

## 1. Objective

Establish the deterministic economic foundation required between fully feasible routing and later optimization, decision support, and commercial conversion.

This increment introduces a canonical, versioned economic-model representation and a deterministic route-economic evaluation contract. It does **not** implement optimization, Jev/LLM decision support, opportunities, offers, agreements, transactions, reservations, physical execution, evidence verification, or autonomous actions.

## 2. Why this increment is required

The normative routing specification places economics after hard feasibility, physical feasibility, capacity/time, logistics, and regulatory/safety validation. The API contract already reserves `GET/POST /v1/economic-models` and route responses may reference an economic model, but the executable implementation had no economic-model foundation.

Phase 3E closes that gap while preserving the critical distinction between canonical physical reality, derived economic computation, and later commercial commitment.

## 3. Architectural boundary

```text
Canonical feasible route inputs
        ↓
Versioned EconomicModel
        ↓
Deterministic economic evaluation
        ↓
Auditable EconomicResult
        ↓
Future optimization / decision support
```

Economic evaluation is derived computation. It MUST NOT mutate ResourceState, Demand, Capability, Transformation, Location, or Route canonical state.

## 4. Scope

### 4.1 EconomicModel domain contract

Implemented an immutable/versioned economic model containing:

- stable model identity;
- organization ownership;
- model version;
- currency;
- explicit participant perspectives;
- value/revenue assumptions;
- cost components;
- calculation assumptions and sources;
- rounding policy;
- validity window;
- provenance;
- creator and timestamps;
- lifecycle status.

Economic models are definitions of calculation assumptions, not transaction records.

### 4.2 Exact monetary semantics

All authoritative monetary values use exact decimal representations. Binary floating point is rejected for canonical money inputs and authoritative economic calculations.

Every monetary amount has an explicit currency. Currency mismatches are rejected rather than silently converted.

Rounding is explicit, deterministic, and versioned by the model.

### 4.3 Economic perspectives

The model preserves labeled participant perspectives rather than collapsing all economics into an unlabeled total.

The evaluator supports:

- supplier;
- processor;
- buyer;
- logistics;
- network.

Each perspective has explicit value/cost components and a reproducible net outcome.

### 4.4 Deterministic evaluation

Implemented a pure evaluator that accepts an EconomicModel plus an explicit evaluation context and returns an immutable result containing:

- model identity/version;
- calculation timestamp;
- context references;
- per-perspective value/cost/net outcomes;
- currency;
- calculation version;
- deterministic provenance.

The evaluator performs no database mutation, external pricing call, model inference, or hidden rounding.

### 4.5 API foundation

Implemented:

- `POST /v1/economic-models`;
- `GET /v1/economic-models`;
- `GET /v1/economic-models/{id}`.

The API uses existing authentication, tenant isolation, machine-readable errors, idempotency, attribution, provenance, ETags, and API envelopes.

Economic-model mutation requires `economic_models:write`; reads require `economic_models:read`.

### 4.6 Persistence

Added the minimum canonical persistence required for EconomicModel definitions. No route-result persistence was introduced.

The migration is reversible and verified against PostgreSQL and SQLite-backed tests.

### 4.7 Routing integration boundary

Phase 3D routing remains valid without an economic model. Phase 3E provides deterministic evaluation as a separate domain capability.

It does NOT:

- rank routes;
- select a route;
- change route feasibility;
- turn economic negativity into physical infeasibility automatically;
- reserve capacity;
- create commercial objects.

## 5. Domain invariants

1. EconomicModel belongs to exactly one organization.
2. Cross-tenant model access is impossible.
3. Model versions are positive and immutable after creation.
4. Monetary values are exact decimals, finite, and currency-qualified.
5. Currency mismatches are deterministic hard validation failures.
6. Component perspective labels are mandatory and stable.
7. Economic calculations are reproducible from declared inputs, model version, and calculation version.
8. Rounding policy is explicit; no implicit binary-float conversion is permitted.
9. Negative net economic outcome is mathematically valid and is not silently rewritten as zero.
10. Economic computation never mutates canonical physical state.
11. EconomicModel definitions are not evidence of actual economic settlement.
12. Economic results are derived computation, not transaction truth.
13. Model validity windows are timezone-aware and deterministic.
14. Idempotent model creation cannot produce duplicate effects.
15. A reused idempotency key with a different payload is a conflict.

## 6. Testing strategy

Implemented tests covering:

- valid model creation;
- tenant isolation;
- read/write scope enforcement;
- idempotent create/replay/conflict;
- invalid currency and currency mismatch;
- binary float rejection at the API boundary;
- non-finite monetary values;
- explicit rounding behavior;
- deterministic calculation repeatability;
- perspective separation;
- negative net outcome preservation;
- inactive/expired model behavior;
- canonical model validation;
- PostgreSQL migration and persistence conformance.

The tests exercise real deterministic logic and database behavior and do not mock away the invariants being proved.

## 7. API contract

Implemented request shape follows the repository's common exact-decimal and provenance conventions. The canonical persisted representation additionally carries `model_key`, `version`, component labels/sources, lifecycle status, creator, and provenance.

No economic result is persisted as canonical physical state.

## 8. Database boundary

EconomicModel is canonical configuration/definition data and therefore requires persistence. EconomicResult remains derived computation and is not persisted as a canonical physical object.

The Phase 1/2 migration semantics remain unchanged. The Phase 3E migration is reversible and passes PostgreSQL upgrade, downgrade, rebuild, and SQLAlchemy alignment checks.

## 9. Documentation synchronization

The implementation was audited against:

- `docs/CRR_API_CONTRACT.md`;
- `docs/CRR_DECISION_AND_ROUTING_SPEC.md`;
- `docs/CRR_VALIDATION_AND_INVARIANTS.md`;
- `docs/CRR_DOMAIN_MODEL.md`;
- `docs/CRR_CONFORMANCE_MATRIX.md`;
- `docs/CRR_DATA_FLOW_ARCHITECTURE.md`;
- `docs/CRR_SPECIFICATION_INDEX.md`.

Those documents already establish the economics-after-feasibility boundary, canonical-versus-derived authority separation, exact monetary semantics, and separation from later optimization/decision/commercial execution. No conflicting normative text or new protocol semantics were required; this plan records the executable closure evidence.

## 10. Definition of done

- Plan committed before implementation. **Done.**
- EconomicModel domain and persistence contracts implemented. **Done.**
- EconomicModel API tenant-isolated and least-privilege protected. **Done.**
- Exact monetary semantics enforced. **Done.**
- Deterministic economic evaluator independently testable. **Done.**
- Economic perspectives remain explicit. **Done.**
- Economic calculation reproducible and auditable. **Done.**
- Canonical physical state immutable during evaluation. **Done.**
- Idempotency and failure/rollback paths covered. **Done.**
- SQLite and PostgreSQL migration/persistence checks pass. **Done.**
- Ruff, format, mypy, pytest, migration lifecycle, SQLAlchemy alignment, PostgreSQL conformance, and full GitHub CI green. **Done.**
- Documentation and conformance evidence match actual behavior. **Done.**
- PR and CI evidence identifiable. **Done.**

## 11. Explicit exclusions

- route optimization;
- multi-objective ranking;
- Jev/LLM decision support;
- opportunity/offer/agreement creation;
- transaction settlement;
- reservation/commitment;
- physical execution;
- evidence verification;
- external pricing services;
- autonomous actions;
- graph database or new infrastructure.

## 12. Closure evidence

- PR: #16
- Implementation/closure branch: `phase3e/economic-foundation`
- Final implementation commit verified by CI: `4499de0985bb4b26fd28444183f292358c547089`
- Final green GitHub Actions run: `39141593262`
- Test job: Ruff **PASS**, Ruff format **PASS**, mypy **PASS**, pytest **PASS**.
- Pytest result: **125 passed, 1 skipped**; the single skip is the pre-existing PostgreSQL-only test that is executed separately by the PostgreSQL job.
- PostgreSQL job: migration upgrade **PASS**, downgrade **PASS**, rebuild **PASS**, SQLAlchemy alignment **PASS**, PostgreSQL conformance **PASS**.
- PostgreSQL parallel successor conformance test: **PASS**.
- Intermediate CI failures were diagnosed and corrected without weakening tests or requirements.

## 13. Execution order

1. Commit this plan first. **Done.**
2. Audit current Phase 3D routing code and normative economic/API/domain documents. **Done.**
3. Implement exact monetary primitives and EconomicModel domain contracts. **Done.**
4. Implement persistence and reversible migration. **Done.**
5. Implement schemas and least-privilege EconomicModel API. **Done.**
6. Implement deterministic economic evaluation without mutation. **Done.**
7. Add comprehensive domain/API/security/idempotency/failure/determinism tests. **Done.**
8. Run static, formatting, typing, unit/API, migration, and PostgreSQL checks. **Done.**
9. Synchronize/audit documentation after behavior was proven. **Done.**
10. Open PR. **PR #16.**
11. Diagnose and fix every CI failure until every required GitHub job is green. **Done.**
12. Declare Phase 3E complete. **Done.**
