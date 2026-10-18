# CRR Phase 3A — Routing Foundation Plan

**Status:** Planned for implementation
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Base:** Phase 2 network-reality conformance closure merged to `main`

## 1. Objective

Establish the smallest complete deterministic routing boundary that can consume the canonical Phase 1/2 objects without inventing physical truth. Phase 3A will implement a routing request, canonical route candidate representation, deterministic source/target loading, candidate discovery from existing Demand/ResourceState/Capability/Transformation data, and hard-constraint feasibility evaluation.

This increment does **not** implement optimization, economics, Jev, commercial conversion, reservations, physical execution, or evidence verification.

## 2. Architectural boundary

The routing engine operates over canonical state:

```text
ResourceState + active Demand
        ↓
Candidate discovery
        ↓
Hard-constraint validation
        ↓
Feasible / infeasible candidates
```

Routing output is a plan/computation result. It must never mutate ResourceState merely because a route was calculated.

## 3. Phase 3A scope

### 3.1 Routing request

The request must reference canonical `source_resource_state_id` and `target_demand_id`. Optional routing constraints and `valid_until` may be supplied, but clients may not inject authoritative source/target quantities, units, locations, capabilities, or transformations inline.

### 3.2 Candidate route model

Represent an auditable candidate with:

- stable route/candidate identifier;
- source ResourceState reference;
- target Demand reference;
- ordered deterministic legs;
- referenced Capability/Transformation objects where applicable;
- feasibility status;
- machine-readable rejection reasons;
- evaluated-at timestamp;
- input/version references sufficient to detect stale assumptions;
- provenance/correlation context.

No candidate represents actual execution.

### 3.3 Deterministic discovery

Initial discovery is deliberately bounded and deterministic. It may use existing canonical indexes/queries but must not depend on embeddings, external graph infrastructure, or an LLM. Discovery may return candidates that later fail hard constraints.

### 3.4 Hard constraints

At minimum, evaluate:

- source existence and tenant ownership;
- target existence and tenant ownership;
- target Demand must be ACTIVE;
- source quantity must be positive for routing eligibility;
- source and demand units must be compatible;
- required state/material specification compatibility;
- source availability at the routing time;
- candidate Capability eligibility/status where a transformation path is used;
- Transformation existence and declared input/output compatibility;
- transformation yield bounds sufficient to satisfy the target requirement where deterministically calculable;
- capability capacity where deterministically calculable;
- target timing window validity;
- no cross-tenant references.

A failed hard constraint makes a candidate infeasible. Scores or future decision providers cannot override this result.

### 3.5 Staleness

The route result must capture versions/timestamps of authoritative inputs used during evaluation. Phase 3A does not commit reservations. A later commitment operation must revalidate material assumptions.

## 4. API boundary

Implement a documented v1 routing endpoint only after the request/result contract is defined by the implementation and tests. The endpoint must use existing authentication, tenant isolation, machine-readable errors, correlation/request identifiers, and least-privilege routing scope.

Mutating/persisting route calculations are out of scope unless required by the existing contract; the initial boundary should prefer deterministic computation over canonical inputs without creating physical state.

## 5. Domain invariants

1. A route always has a canonical source and target.
2. A route cannot be feasible when the target Demand is inactive.
3. Zero-quantity ResourceState is never routing supply.
4. Authoritative quantities remain exact decimals.
5. Unit compatibility is deterministic.
6. Every route leg has explicit input/output semantics.
7. Every failed hard constraint is machine-readable.
8. Feasibility cannot be overridden by ranking or AI.
9. Route computation cannot mutate Resource/ResourceState.
10. Cross-tenant source/target/reference access is impossible.
11. Results expose the authoritative versions/timestamps used for evaluation.
12. A route is a plan, not execution evidence.

## 6. Testing strategy

Add domain, API, security, failure-path, and integration tests covering:

- valid direct candidate;
- missing source/target;
- inactive/expired/cancelled demand;
- zero source quantity;
- insufficient quantity;
- unit incompatibility;
- state mismatch;
- capability inactive/missing;
- transformation mismatch;
- yield insufficiency;
- capacity insufficiency;
- invalid timing;
- cross-tenant access;
- malformed request;
- exact-decimal handling;
- ResourceState immutability after routing;
- deterministic repeated evaluation;
- PostgreSQL behavior where SQLite is insufficient.

No tests may weaken requirements or mock away the hard-constraint implementation.

## 7. Documentation synchronization

After behavior is proven, synchronize the affected routing/API/conformance documentation and explicitly record the Phase 3A evidence. Do not mark broader routing, optimization, decision, commercial, reservation, execution, or verification semantics as implemented.

## 8. Definition of done

- Plan committed before implementation.
- Canonical routing domain boundary implemented.
- Deterministic candidate discovery implemented.
- Hard constraints implemented and machine-readable.
- Tenant isolation and authorization enforced.
- Exact decimal/unit/time semantics preserved.
- Routing cannot mutate physical state.
- Tests cover positive, negative, security, and failure paths.
- PostgreSQL CI is green alongside standard CI.
- Documentation/conformance evidence matches actual behavior.
- PR, commit, and CI evidence are identifiable.

## 9. Explicit exclusions

- optimization;
- economic ranking;
- Jev/LLM decision support;
- graph database;
- external semantic search/embeddings;
- commercial opportunities/offers/agreements/transactions;
- capacity reservation;
- physical execution;
- evidence verification;
- autonomous actions.

## 10. Execution order

1. Commit this plan first.
2. Audit current Phase 1/2 code and routing specification.
3. Implement domain contracts.
4. Implement deterministic discovery and feasibility checks.
5. Implement API boundary only where contractually justified.
6. Add comprehensive tests.
7. Run local/static/migration/PostgreSQL checks.
8. Open PR.
9. Continue fixing every CI failure until all required jobs are green.
10. Only then declare Phase 3A complete.
