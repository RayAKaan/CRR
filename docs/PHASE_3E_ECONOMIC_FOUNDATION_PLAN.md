# CRR Phase 3E — Economic Foundation Plan

**Status:** Planned for implementation
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Base:** Phase 3D routing API and regulatory/safety closure merged to `main`

## 1. Objective

Establish the deterministic economic foundation required between fully feasible routing and later optimization, decision support, and commercial conversion.

This increment introduces a canonical, versioned economic-model representation and a deterministic route-economic evaluation contract. It does **not** implement optimization, Jev/LLM decision support, opportunities, offers, agreements, transactions, reservations, physical execution, evidence verification, or autonomous actions.

## 2. Why this increment is required

The normative routing specification places economics after hard feasibility, physical feasibility, capacity/time, logistics, and regulatory/safety validation. The API contract already reserves `GET/POST /v1/economic-models` and route responses may reference an economic model, but the executable implementation currently has no economic-model foundation.

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

Define an immutable/versioned economic model containing:

- stable model identity;
- organization ownership;
- model version;
- currency;
- explicit participant perspectives;
- value/revenue assumptions;
- cost components;
- fees/taxes where represented;
- calculation assumptions and sources;
- rounding policy;
- validity window;
- provenance;
- creator and timestamps;
- lifecycle status.

Economic models are definitions of calculation assumptions, not transaction records.

### 4.2 Exact monetary semantics

All authoritative monetary values MUST use exact decimal representations. Binary floating point is prohibited for canonical money or authoritative economic calculations.

Every monetary amount must have an explicit currency. Currency mismatches MUST be rejected rather than silently converted.

Rounding MUST be explicit, deterministic, and versioned by the model.

### 4.3 Economic perspectives

The model MUST preserve labeled participant perspectives rather than collapsing all economics into an unlabeled total.

The initial evaluator supports the normative perspectives:

- supplier;
- processor;
- buyer;
- logistics;
- network/platform where explicitly configured.

Each perspective has explicit signed value/cost components and a reproducible net outcome.

### 4.4 Deterministic evaluation

Implement a pure evaluator that accepts a feasible route context plus an EconomicModel and returns an immutable result containing:

- model identity/version;
- calculation timestamp;
- input/context references;
- per-perspective components;
- net outcomes;
- currency;
- calculation version;
- deterministic assumptions/provenance.

The evaluator MUST NOT perform database mutation, external pricing calls, model inference, or hidden rounding.

### 4.5 API foundation

Implement the normative economic-model API boundary:

- `POST /v1/economic-models`;
- `GET /v1/economic-models`;
- `GET /v1/economic-models/{id}`.

Use existing authentication, tenant isolation, machine-readable errors, idempotency, attribution, provenance, and API envelopes.

Economic-model mutation requires a least-privilege economics write scope. Reads require an economics read scope. Existing route computation is not converted into economic optimization by this increment.

### 4.6 Persistence

Add the minimum canonical persistence needed for EconomicModel definitions. No route-result persistence is introduced.

The migration MUST be reversible and verified against PostgreSQL as well as SQLite.

### 4.7 Routing integration boundary

Phase 3D routing remains valid without an economic model. Phase 3E may expose a deterministic evaluation service/API that can evaluate a feasible candidate when a model is explicitly supplied.

It MUST NOT:

- rank routes;
- select a route;
- change route feasibility;
- turn economic negativity into physical infeasibility automatically;
- reserve capacity;
- create commercial objects.

## 5. Domain invariants

1. EconomicModel belongs to exactly one organization.
2. Cross-tenant model access is impossible.
3. Model versions are positive and immutable once published.
4. Monetary values are exact decimals, finite, and currency-qualified.
5. Currency mismatches are deterministic hard validation failures.
6. Component perspective labels are mandatory and stable.
7. Economic calculations are reproducible from declared inputs, model version, and calculation version.
8. Rounding policy is explicit; no implicit binary-float conversion is permitted.
9. Negative net economic outcome is mathematically valid and is not silently rewritten as zero.
10. Economic computation never mutates canonical physical state.
11. EconomicModel definitions are not evidence of actual economic settlement.
12. Economic results are derived/planned computation, not transaction truth.
13. Model validity windows are timezone-aware and deterministic.
14. Idempotent model creation cannot produce duplicate effects.
15. A reused idempotency key with a different payload is a conflict.

## 6. Testing strategy

Add tests covering:

- valid model creation;
- tenant isolation;
- read/write scope enforcement;
- idempotent create/replay/conflict;
- invalid currency and currency mismatch;
- negative/zero monetary values where permitted;
- binary float rejection;
- non-finite values;
- explicit rounding behavior;
- deterministic calculation repeatability;
- perspective separation;
- negative net outcome preservation;
- expired/not-yet-valid model behavior;
- missing required economic inputs;
- immutable published model behavior;
- route feasibility remaining independent from economics;
- canonical state immutability after economic evaluation;
- database rollback/error paths;
- PostgreSQL migration and persistence conformance.

Tests MUST exercise the real evaluator and database behavior and MUST NOT mock away the invariants being proved.

## 7. API contract

Conceptual EconomicModel request:

```json
{
  "id": "eco_123",
  "currency": "SAR",
  "valid_from": "2026-10-18T00:00:00Z",
  "valid_until": "2026-12-31T23:59:59Z",
  "calculation_version": "1",
  "rounding": {
    "mode": "HALF_EVEN",
    "scale": 2
  },
  "components": [
    {
      "perspective": "SUPPLIER",
      "kind": "VALUE",
      "amount": "125000.00"
    },
    {
      "perspective": "SUPPLIER",
      "kind": "COST",
      "amount": "10000.00"
    }
  ]
}
```

The actual executable schema MUST remain aligned with the repository's common envelope, authentication, attribution, and exact-decimal conventions.

## 8. Database boundary

EconomicModel is canonical configuration/definition data and therefore requires persistence. EconomicResult remains derived computation in this increment and is not persisted as a canonical physical object.

No change is permitted to the existing Phase 1/2 migration semantics.

## 9. Documentation synchronization

After implementation is proven, synchronize only where required:

- `docs/CRR_API_CONTRACT.md`;
- `docs/CRR_DECISION_AND_ROUTING_SPEC.md`;
- `docs/CRR_VALIDATION_AND_INVARIANTS.md`;
- `docs/CRR_DOMAIN_MODEL.md`;
- `docs/CRR_CONFORMANCE_MATRIX.md`;
- `docs/CRR_DATA_FLOW_ARCHITECTURE.md`;
- `docs/CRR_SPECIFICATION_INDEX.md`;
- this Phase 3E plan with closure evidence.

Documentation MUST distinguish economic calculation from optimization, decision support, commercial pricing/offer acceptance, and actual settlement.

## 10. Definition of done

- Plan committed before implementation.
- EconomicModel domain and persistence contracts are implemented.
- EconomicModel API is tenant-isolated and least-privilege protected.
- Exact monetary semantics are enforced.
- Deterministic economic evaluator is implemented and independently testable.
- Economic perspectives remain explicit.
- Economic calculation is reproducible and auditable.
- Canonical physical state is immutable during evaluation.
- Idempotency and failure/rollback paths are covered.
- SQLite and PostgreSQL migration/persistence checks pass.
- Ruff, format, mypy, pytest, migration lifecycle, SQLAlchemy alignment, PostgreSQL conformance, and full GitHub CI are green.
- Documentation and conformance evidence match actual behavior.
- PR and CI evidence are identifiable before completion is declared.

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

## 12. Execution order

1. Commit this plan first.
2. Audit current Phase 3D routing code and normative economic/API/domain documents.
3. Implement exact monetary primitives and EconomicModel domain contracts.
4. Implement persistence and reversible migration.
5. Implement schemas and least-privilege EconomicModel API.
6. Implement deterministic economic evaluation without mutation.
7. Add comprehensive domain/API/security/idempotency/failure/determinism tests.
8. Run static, formatting, typing, unit/API, migration, and PostgreSQL checks.
9. Synchronize documentation only after behavior is proven.
10. Open PR.
11. Diagnose and fix every CI failure until every required GitHub job is green.
12. Only then declare Phase 3E complete.
