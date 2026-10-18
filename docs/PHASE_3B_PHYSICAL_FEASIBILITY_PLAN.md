# CRR Phase 3B — Physical Feasibility, Transformation, Capacity & Time Plan

**Status:** Planned for implementation
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Base:** Phase 3A routing foundation merged to `main`

## 1. Objective

Extend the deterministic routing foundation from direct source/demand compatibility into explicit physical feasibility for transformation-backed routes, while preserving CRR's separation between route computation and execution.

Phase 3B will add the smallest complete deterministic feasibility boundary for:

- transformation input/output compatibility;
- declared yield/loss bounds;
- capability eligibility and capacity;
- operating windows and route timing;
- machine-readable hard-constraint rejection reasons;
- auditable route versions and assumptions.

This increment does **not** implement economics, optimization, Jev, commercial conversion, reservations, physical execution, or evidence verification.

## 2. Architectural boundary

```text
ResourceState + active Demand
        ↓
Phase 3A candidate discovery
        ↓
Transformation / Capability feasibility
        ↓
Quantity / yield validation
        ↓
Capacity / time validation
        ↓
Feasible / infeasible route candidates
```

The router remains a pure computation over canonical facts. It must not mutate ResourceState, Demand, Capability, or Transformation.

## 3. Scope

### 3.1 Transformation-backed route evaluation

Add deterministic evaluation for a route containing a transformation leg. The evaluator must verify that the source state satisfies the transformation input specification and that the resulting output can satisfy the target demand specification.

### 3.2 Yield and quantity semantics

Use exact decimal quantities throughout. Evaluate declared transformation yield/loss bounds without inventing unrecorded losses. A route is infeasible when its deterministically calculable output cannot satisfy the demand minimum.

Zero-quantity ResourceState remains historical/reconciled state but is never eligible as routing supply.

### 3.3 Capability eligibility and capacity

A transformation-backed route must reference an eligible Capability owned by the same organization/tenant and in an execution-eligible status. Where capacity is represented deterministically, the route must verify that the required quantity fits within available capacity for the relevant operating interval.

Phase 3B does not create reservations or consume capacity.

### 3.4 Time feasibility

Validate source availability, demand timing, capability operating windows, and transformation duration where those canonical fields exist. Naive datetimes are invalid. A route outside an authoritative operating or demand window is infeasible.

### 3.5 Rejection taxonomy

Use the normative machine-readable routing rejection vocabulary where applicable, including:

- `CAPABILITY_INACTIVE`
- `CAPACITY_INSUFFICIENT`
- `TIME_WINDOW_CONFLICT`
- `TRANSFORMATION_UNAVAILABLE`
- `YIELD_INVALID`
- `STATE_MISMATCH`
- `INSUFFICIENT_QUANTITY`
- `UNIT_INCOMPATIBLE`

Do not silently convert hard failures into warnings.

### 3.6 Staleness and auditability

Route results must preserve the versions/timestamps of every authoritative input used by the feasibility calculation. No feasibility result implies a reservation or execution commitment.

## 4. Domain invariants

1. Transformation input and output specifications are authoritative references, not client-supplied physical facts.
2. A transformation cannot be used when it is inactive or otherwise ineligible.
3. Capability and transformation references cannot cross tenants.
4. Exact decimal arithmetic is mandatory for physical quantities.
5. Yield/loss calculations are deterministic and reproducible.
6. A route cannot claim feasibility when output is below the demand minimum.
7. Capacity is checked without silently reserving or mutating it.
8. Time-window violations are hard blockers.
9. Route evaluation cannot mutate physical state.
10. Repeated evaluation over unchanged inputs is deterministic apart from evaluation timestamp/correlation metadata.
11. AI/Jev cannot override physical feasibility failures.
12. Route output remains a plan, never execution evidence.

## 5. Testing strategy

Add tests for:

- valid transformation-backed route;
- incompatible transformation input state;
- incompatible transformation output state;
- inactive capability;
- missing/inactive transformation;
- insufficient transformation yield;
- invalid yield bounds;
- insufficient capability capacity;
- operating-window conflict;
- demand-window conflict;
- zero source quantity;
- unit incompatibility;
- cross-tenant capability/transformation references;
- exact-decimal calculations;
- deterministic repeated evaluation;
- immutability of canonical ResourceState/Demand/Capability/Transformation;
- PostgreSQL behavior where persistence is involved.

Tests must exercise real deterministic feasibility logic and must not mock away the constraints being proved.

## 6. Documentation synchronization

After implementation is proven, synchronize the routing specification, API contract where the existing endpoint exposes the new semantics, conformance matrix, data-flow architecture, and specification index. Documentation must identify exactly which Phase 3B semantics are implemented and must not imply economics, optimization, decision support, commercial conversion, reservation, execution, or verification are complete.

## 7. Definition of done

- Plan committed before implementation.
- Transformation-backed feasibility is implemented deterministically.
- Capability eligibility/capacity is enforced.
- Yield and exact quantity semantics are enforced.
- Time-window feasibility is enforced.
- Rejections are machine-readable and auditable.
- Tenant isolation and authorization boundaries remain intact.
- Canonical physical state is never mutated by routing.
- Comprehensive positive, negative, security, determinism, and regression tests pass.
- Ruff, format, mypy, pytest, migration checks, PostgreSQL conformance, and full GitHub CI are green.
- Documentation and conformance evidence match actual behavior.
- PR and CI evidence are identifiable before completion is declared.

## 8. Explicit exclusions

- economics;
- optimization;
- Jev/LLM decision support;
- commercial opportunities/offers/agreements/transactions;
- reservations;
- physical execution;
- shipment;
- evidence verification;
- autonomous actions;
- graph database or external graph infrastructure.

## 9. Execution order

1. Commit this plan first.
2. Audit Phase 3A routing code, Phase 2 domain contracts, and normative routing/validation specifications.
3. Implement the smallest transformation-backed feasibility contracts.
4. Implement yield, capacity, and time checks using existing canonical models.
5. Add comprehensive regression/security/determinism tests.
6. Run local static, unit, migration, and PostgreSQL checks.
7. Synchronize affected documentation only after behavior is proven.
8. Open PR.
9. Continue fixing every CI failure until every required job is green.
10. Only then declare Phase 3B complete.
