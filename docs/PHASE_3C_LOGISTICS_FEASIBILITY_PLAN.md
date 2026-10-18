# CRR Phase 3C — Logistics & Geographic Feasibility Plan

**Status:** Complete
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Base:** Phase 3B physical-feasibility routing merged to `main`
**Merged implementation:** PR #13

## 1. Objective

Extend the deterministic routing boundary with an explicit, auditable logistics feasibility layer for movement between authoritative locations. This increment establishes the smallest complete logistics computation without introducing commercial execution, reservations, shipment execution, or verification.

## 2. Architectural boundary

```text
ResourceState / Demand
        ↓
Phase 3A candidate discovery
        ↓
Phase 3B physical feasibility
        ↓
Phase 3C logistics feasibility
        ↓
Feasible / infeasible route candidate
```

Logistics is a plan. It is not evidence that transport occurred.

## 3. Scope

### 3.1 Explicit logistics inputs

Represent deterministic transport assumptions as immutable inputs rather than inventing routing facts. A logistics evaluation must explicitly identify source location, destination location, transport mode, distance, travel duration, payload capacity, and evaluation time.

### 3.2 Geographic feasibility

Reject a route when the supplied authoritative location identifiers do not match the route endpoints, when a required distance is invalid, or when configured maximum distance constraints are exceeded. Location coordinates remain canonical data owned by the Location model; Phase 3C does not rewrite them.

### 3.3 Transport capacity

Verify that the physical quantity being moved is compatible with the declared transport payload capacity using the existing versioned UnitRegistry and exact decimal arithmetic. No reservation or capacity consumption occurs.

### 3.4 Timing

Calculate arrival deterministically from the route start and declared travel duration. Reject routes that cannot fit the destination demand window or other explicitly supplied authoritative timing constraints. Naive datetimes remain invalid.

### 3.5 Rejection taxonomy

Use existing normative machine-readable reasons where applicable:

- `LOCATION_INFEASIBLE`
- `CAPACITY_INSUFFICIENT`
- `TIME_WINDOW_CONFLICT`
- `UNIT_INCOMPATIBLE`
- `INSUFFICIENT_QUANTITY`

No logistics hard failure may be downgraded to a warning.

### 3.6 Auditability

Logistics results must retain deterministic input assumptions, versions, and evaluation time. Repeated evaluation over unchanged inputs must produce identical feasibility and rejection results.

## 4. Domain invariants

1. Logistics never mutates ResourceState, Demand, Capability, or Transformation.
2. Exact decimal quantities are mandatory.
3. Transport capacity uses the versioned unit registry.
4. Distance and duration are explicit assumptions, not hidden network calls.
5. Negative distance, duration, or capacity is invalid.
6. Zero source quantity is never routing supply.
7. Timing violations are hard blockers.
8. A route cannot claim transport feasibility when payload exceeds transport capacity.
9. A logistics result never implies reservation or shipment execution.
10. Cross-tenant source/destination references are rejected.
11. Authoritative location data is never rewritten by routing.
12. Logistics calculations are deterministic and reproducible.

## 5. Testing strategy

Add tests for:

- feasible logistics leg;
- location mismatch;
- cross-tenant location boundary;
- negative distance/duration/capacity;
- insufficient transport capacity;
- unit incompatibility;
- zero quantity;
- demand-window conflict;
- exact-decimal capacity comparison;
- deterministic repeated evaluation;
- immutable canonical inputs;
- machine-readable rejection reasons.

Tests must exercise real deterministic logic and must not mock away constraints being proved.

## 6. Documentation synchronization

The Phase 3C implementation is documented in the phase plan, the conformance matrix, and the specification index. The existing normative routing specification already defines logistics as a hard-feasibility layer and the API contract has no Phase 3C endpoint requiring a contract change. The implementation does not introduce a persistence model or migration, so migration/schema semantics remain unchanged.

Documentation states exactly what Phase 3C implements and does not imply economics, optimization, reservations, commercial conversion, execution, shipment proof, evidence, or verification are complete.

## 7. Definition of done

- Plan committed before implementation.
- Deterministic logistics feasibility contracts implemented.
- Geographic, transport-capacity, unit, and timing checks enforced.
- Tenant boundaries preserved.
- Canonical inputs remain immutable.
- Comprehensive positive, negative, security, determinism, and regression tests pass.
- Ruff, format, mypy, pytest, migration checks, PostgreSQL conformance, and full GitHub CI are green.
- Documentation and conformance evidence match actual behavior.
- PR and CI evidence are identifiable before completion is declared.

## 8. Explicit exclusions

- economics;
- optimization;
- Jev/LLM decision support;
- reservations;
- commercial opportunities/offers/agreements/transactions;
- physical shipment execution;
- evidence verification;
- autonomous actions;
- external routing/network services;
- graph database infrastructure.

## 9. Execution order

1. Commit this plan first.
2. Audit the merged Phase 3B routing contracts and canonical Location/Quantity semantics.
3. Implement the smallest immutable logistics domain contracts.
4. Add deterministic feasibility and rejection logic.
5. Add comprehensive regression, security, determinism, and immutability tests.
6. Run local static and test checks.
7. Synchronize affected documentation only after behavior is proven.
8. Open PR.
9. Fix every CI failure until every required GitHub job is green.
10. Only then declare Phase 3C complete.

## 10. Closure evidence

- PR #13 merged successfully at merge commit `8d936ed98518dd3e2192a6185467633ad936b12e`.
- Final pre-merge CI run: `39135176826`.
- Test job: Ruff, format, mypy, and pytest all passed.
- PostgreSQL job: migration upgrade, downgrade, rebuild, SQLAlchemy alignment, and PostgreSQL conformance all passed.
- An earlier CI run failed only on one Ruff line-length violation; it was corrected without weakening tests or requirements, and the corrected run was fully green.
