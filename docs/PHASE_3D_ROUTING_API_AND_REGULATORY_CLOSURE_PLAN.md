# CRR Phase 3D — Routing API & Regulatory/Safety Closure Plan

**Status:** Complete
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Base:** Phase 3C logistics feasibility merged to `main`
**Merged implementation:** PR #15

## 1. Objective

Close the remaining executable gap between the Phase 3 routing domain contracts and the normative API boundary, while adding the deterministic regulatory, safety, certification, and eligibility checks required before a route can be considered fully feasible.

This increment is intentionally narrow. It does not implement economics, optimization, Jev/LLM decision support, reservations, commercial conversion, physical execution, shipment execution, evidence verification, or autonomous actions.

## 2. Why this increment is required

The repository's normative API contract defines `POST /v1/routes/compute` under the least-privilege `routes:compute` scope, while the merged Phase 3A implementation contained routing domain contracts but did not mount a routing API. The routing specification also requires regulatory/safety/eligibility validation before economics and optimization.

Phase 3D therefore establishes the externally callable deterministic routing boundary and closes the regulatory/safety gap without introducing a new persistence model or route reservation semantics.

## 3. Architectural boundary

```text
Canonical ResourceState + active Demand
        ↓
Deterministic candidate discovery
        ↓
Physical feasibility
        ↓
Logistics feasibility
        ↓
Regulatory / safety / eligibility
        ↓
Feasible / infeasible route candidates
```

Routing remains a computation over canonical state. Computing a route MUST NOT mutate ResourceState, Demand, Capability, Transformation, or Location.

## 4. Scope

### 4.1 Routing API

Implemented `POST /v1/routes/compute` using the existing authentication, tenant isolation, machine-readable error envelope, request/correlation identifiers, and least-privilege `routes:compute` scope.

The request references canonical `source_resource_state_id` and `target_demand_id` and does not accept authoritative source quantities, units, locations, capabilities, transformations, certifications, or regulatory facts inline.

The API is computation-only: it returns deterministic candidates and does not persist reservations or execution state.

### 4.2 Candidate discovery

The implementation loads source and target from the authenticated organization and discovers deterministic direct and transformation-backed candidates from existing canonical Demand, ResourceState, Capability, and Transformation records.

Candidate ordering is deterministic and independent of database row-order accidents.

### 4.3 Regulatory / safety / eligibility

Implemented an immutable deterministic evaluator for policy facts represented by CRR objects:

- required certifications;
- required capability eligibility;
- regulatory constraint key/value requirements;
- prohibited eligibility values;
- missing required controls;
- explicit regulatory uncertainty/escalation markers.

Missing required authorization/certification or an unresolved mandatory regulatory control is a hard blocker. The implementation does not infer legal permission or delegate regulatory authority to an AI provider.

### 4.4 Machine-readable rejection taxonomy

The implementation uses deterministic rejection reasons including:

- `REGULATORY_BLOCK`;
- `SAFETY_BLOCK`;
- `CAPABILITY_INACTIVE`;
- `TRANSFORMATION_UNAVAILABLE`;
- `LOCATION_INFEASIBLE`;
- `TIME_WINDOW_CONFLICT`;
- `CAPACITY_INSUFFICIENT`;
- `UNIT_INCOMPATIBLE`;
- `INSUFFICIENT_QUANTITY`;
- `DEMAND_EXPIRED`.

Every hard failure identifies the controlling object and a deterministic message.

### 4.5 Auditability and staleness

The response exposes source and target versions captured by `RouteCandidate` and retains capability/transformation versions in provenance. A route is a plan, not execution evidence. No route is reserved by computation.

## 5. Domain invariants

1. Cross-tenant source, target, capability, transformation, and location references are impossible.
2. Only ACTIVE Demand participates in ordinary routing.
3. Zero-quantity ResourceState is never routing supply.
4. Exact decimal/unit semantics remain authoritative.
5. Regulatory and safety blockers cannot be downgraded by scores or future AI providers.
6. Missing required authorization/certification is infeasible.
7. Regulatory uncertainty is represented as escalation/blocking, never guessed permission.
8. Route computation never mutates canonical physical state.
9. Candidate ordering is deterministic.
10. API clients cannot inject authoritative physical or regulatory facts.
11. The routing API requires `routes:compute` or `admin:*`.
12. The API returns machine-readable rejection reasons rather than opaque exceptions.
13. Repeated evaluation over unchanged canonical inputs is deterministic apart from evaluation timestamp.
14. Route existence never implies reservation, execution, or verification.

## 6. Testing strategy

Implemented tests covering:

- valid direct route through the API;
- deterministic candidate ordering;
- transformation-backed candidate discovery;
- missing source/target;
- cross-tenant source/target access;
- missing `routes:compute` scope;
- zero source quantity;
- inactive demand;
- unit incompatibility;
- capability inactive;
- transformation unavailable/mismatched;
- regulatory certification success/failure;
- regulatory key/value mismatch;
- unresolved mandatory regulatory control;
- machine-readable safety/regulatory rejection;
- exact-decimal request rejection for authoritative inline values;
- malformed request;
- repeated deterministic computation;
- canonical input immutability after routing;
- PostgreSQL migration and conformance behavior.

Tests exercise the real deterministic logic and do not mock away the constraints being proved.

## 7. API contract

Request shape:

```json
{
  "source_resource_state_id": "rst_123",
  "target_demand_id": "dem_123",
  "valid_until": "2026-10-18T18:00:00Z"
}
```

Response shape is the repository's standard envelope with a deterministic list of auditable route candidates. No route is persisted by this increment.

## 8. Documentation synchronization

Synchronized the implementation evidence with the affected routing/API/conformance documentation and retained explicit boundaries around later economics, optimization, decisions, commercial conversion, execution, and verification.

## 9. Database boundary

No new canonical persistence table was required for computation-only routing. Existing migrations and SQLAlchemy metadata remain unchanged.

PostgreSQL CI was run against the canonical Phase 1/2 schema and passed migration upgrade, downgrade, rebuild, model alignment, and conformance checks.

## 10. Definition of done

- Plan committed before implementation.
- `POST /v1/routes/compute` is mounted and protected by `routes:compute`.
- Deterministic candidate discovery is implemented over canonical data.
- Regulatory/safety/eligibility hard constraints are deterministic and machine-readable.
- Tenant isolation is enforced across every referenced object.
- Exact decimal/unit/time semantics are preserved.
- Routing cannot mutate canonical state.
- Comprehensive domain/API/security/failure/determinism tests pass.
- Ruff, format, mypy, pytest, migration lifecycle, SQLAlchemy alignment, PostgreSQL conformance, and full GitHub CI are green.
- Documentation and conformance evidence match actual behavior.
- PR, commit, and CI evidence are identifiable.

## 11. Explicit exclusions

- economics;
- optimization;
- scoring/ranking beyond deterministic candidate ordering;
- Jev/LLM decision support;
- reservations;
- opportunity/offer/agreement/transaction creation;
- physical shipment/execution;
- evidence verification;
- autonomous actions;
- graph database;
- external routing/network services.

## 12. Execution order

1. Commit this plan first. **Done.**
2. Audit current Phase 3A/3B/3C routing code and all affected normative documents. **Done.**
3. Implement regulatory/safety domain contracts. **Done.**
4. Implement deterministic route discovery over canonical SQLAlchemy models. **Done.**
5. Implement the `routes:compute` API boundary. **Done.**
6. Add comprehensive domain/API/security/failure/determinism tests. **Done.**
7. Run local static/test/migration checks where available. **Covered by CI verification.**
8. Synchronize documentation after behavior was proven. **Done.**
9. Open PR. **PR #15.**
10. Diagnose and fix every CI failure until every required GitHub job is green. **Done.**
11. Declare Phase 3D complete. **Done.**

## 13. Closure evidence

- PR: #15
- Final implementation commit: `9cfa7c9547549d5482ab9a1488cbb8da18858582`
- Final GitHub Actions CI run: `39140575051`
- Test job: Ruff check **PASS**, Ruff format **PASS**, mypy **PASS**, pytest **PASS**.
- PostgreSQL job: migration upgrade **PASS**, downgrade **PASS**, rebuild **PASS**, SQLAlchemy alignment **PASS**, PostgreSQL conformance **PASS**.
- Earlier failures were diagnosed from CI logs and corrected without weakening requirements or tests.
