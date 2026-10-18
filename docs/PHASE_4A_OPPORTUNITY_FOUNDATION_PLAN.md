# CRR Phase 4A — Opportunity Foundation Plan

**Status:** Planned  
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2  
**Base:** Phase 3G bounded decision-support foundation merged to `main`

## 1. Objective

Establish the first explicit commercial-conversion boundary in CRR: a tenant-isolated, auditable Opportunity object that can be created only from a currently feasible, non-stale, deterministically evaluated route result.

An Opportunity is a commercial-intent record derived from a validated route. It is **not** an Offer, Agreement, Transaction, Reservation, execution record, or evidence of physical completion.

## 2. Why this increment is next

The normative routing sequence now has executable coverage through bounded decision support:

`candidate discovery → hard constraints → physical/capacity/time/logistics/regulatory feasibility → economics → optimization → decision support → ranked feasible routes`.

The normative commercial boundary is then:

`FEASIBLE ROUTE → OPPORTUNITY → OFFER → AGREEMENT → TRANSACTION`.

Phase 4A closes only the first edge of that boundary. It must preserve the separation between computational recommendation and commercial commitment while creating a durable, traceable commercial-intent object.

## 3. Architectural boundary

```text
Canonical route / decision advisory
        ↓
Freshness + feasibility revalidation
        ↓
Opportunity creation
        ↓
Opportunity lifecycle
        ↓
Future Offer boundary
```

Opportunity creation MUST NOT silently reserve capacity, mutate ResourceState, change Demand, alter Capability/Transformation/EconomicModel truth, execute a transaction, or claim that physical execution occurred.

## 4. Scope

### 4.1 Opportunity domain contract

Implement an immutable-at-creation commercial-intent record containing at minimum:

- stable opportunity identity;
- organization ownership;
- source route candidate/reference and source versions;
- candidate-set fingerprint;
- source demand reference/version;
- source resource-state reference/version;
- optional advisory provenance;
- economic-model identity/version when economics are present;
- explicit currency and commercial perspective;
- quantity/unit snapshot;
- location references;
- valid-from/valid-until window;
- lifecycle status;
- creator/attribution;
- provenance and timestamps;
- optimistic version.

The object must preserve the exact source references and derived snapshots used to create it. It must never be mistaken for canonical physical state.

### 4.2 Lifecycle

Initial deterministic lifecycle:

`DRAFT → OPEN → EXPIRED`

with explicit terminal/cancellation paths where required by the implementation contract. Invalid transitions must fail deterministically and must never mutate the stored object.

Opportunity lifecycle is independent of ResourceState lifecycle. A closed or expired opportunity does not rewrite physical history.

### 4.3 Eligibility gate

Opportunity creation requires all of the following:

1. authenticated caller belongs to the source organization;
2. source candidate belongs to the same organization;
3. source candidate is `FEASIBLE` and present in the fixed candidate set;
4. source candidate-set fingerprint matches the supplied optimization/decision provenance;
5. source route inputs are still current enough for commercial conversion;
6. target Demand remains eligible under its authoritative lifecycle;
7. required economic context is internally consistent when present;
8. valid-until does not exceed the authoritative source validity window;
9. the request cannot inject authoritative physical/economic facts inline.

A stale or infeasible route must be rejected rather than converted.

### 4.4 API boundary

Implement the minimum commercial API surface:

- `POST /v1/opportunities` — create from canonical route provenance;
- `GET /v1/opportunities` — tenant-scoped listing/filtering;
- `GET /v1/opportunities/{id}` — tenant-scoped retrieval;
- lifecycle mutation only where explicitly required by the domain contract.

Mutation requires the repository's existing idempotency and optimistic-concurrency conventions. Creation requires least-privilege `opportunities:write`; reads require `opportunities:read`.

Requests reference canonical IDs and provenance rather than accepting authoritative route facts inline.

### 4.5 Persistence

Opportunity is durable commercial-intent state and therefore requires canonical persistence and a reversible migration. The migration must be verified on SQLite and PostgreSQL and remain aligned with SQLAlchemy metadata.

No Offer, Agreement, Transaction, Reservation, or Execution tables are introduced in this increment.

### 4.6 Transactional boundary

Opportunity creation is a single transactional state change with:

- canonical persistence;
- idempotency record;
- attribution/provenance;
- transactional outbox event.

A failed write must not leave a partial opportunity or orphaned outbox effect. Replaying the same idempotency key and payload must return the original result; reusing it with a different payload must be a conflict.

## 5. Explicit non-goals

- offers or price negotiation;
- agreements or signatures;
- transactions or settlement;
- capacity reservation/commitment;
- physical execution;
- evidence verification;
- autonomous acceptance;
- Jev/LLM decision making;
- external pricing/geographic providers;
- automatic candidate rediscovery;
- mutation of canonical physical reality;
- graph database or new infrastructure.

## 6. Domain invariants

1. Every Opportunity belongs to exactly one organization.
2. Cross-tenant reads/writes/history are rejected or hidden.
3. An Opportunity must reference a feasible source candidate.
4. The source candidate must belong to the declared fixed candidate set.
5. Candidate-set fingerprint, route versions, and source provenance are immutable audit references.
6. Stale source routes cannot be converted without explicit revalidation.
7. Quantity/unit snapshots use exact decimal semantics and a declared unit registry version.
8. Monetary snapshots use exact decimals and explicit currency/perspective when present.
9. Validity windows are timezone-aware and deterministic.
10. Opportunity lifecycle transitions are explicit and versioned.
11. Mutations require least privilege and optimistic concurrency where applicable.
12. Creation is idempotent; payload reuse under another body is a conflict.
13. Opportunity creation never mutates ResourceState, Demand, Capability, Transformation, Location, or EconomicModel canonical truth.
14. Outbox publication is transactionally coupled to the Opportunity write.
15. Derived/commercial intent is never treated as proof of physical execution or settlement.
16. Provenance identifies the route candidate, candidate-set fingerprint, policy/calculation versions, and creator context used for conversion.

## 7. Testing strategy

Coverage MUST include:

- valid opportunity creation from a feasible route;
- infeasible candidate rejection;
- missing/stale/tampered candidate-set provenance rejection;
- cross-tenant isolation;
- demand lifecycle/eligibility rejection;
- exact decimal quantity and monetary semantics;
- invalid/naive validity windows;
- idempotent create/replay/conflict;
- optimistic-concurrency lifecycle mutation;
- illegal lifecycle transitions;
- persistence rollback;
- transactional outbox coupling;
- canonical source immutability;
- unauthorized and insufficient-scope requests;
- malformed inline-authority rejection;
- SQLite migration lifecycle;
- PostgreSQL migration lifecycle and real PostgreSQL conformance;
- SQLAlchemy/model alignment;
- full existing routing, economics, optimization, and decision-support regression suite.

Tests must exercise real database transactions and deterministic domain logic rather than mocking away the commercial boundary.

## 8. Database boundary

Unlike routing/optimization/decision-support, Opportunity is durable commercial-intent state and therefore requires persistence. The schema must preserve tenant ownership, source-route provenance, lifecycle/version fields, exact numeric snapshots, timestamps, and audit references.

The migration must be reversible and PostgreSQL-compatible. No downstream commercial or execution persistence is introduced yet.

## 9. Documentation synchronization

After behavior is proven, audit and synchronize only the normative documents whose executable semantics change:

- `docs/CRR_API_CONTRACT.md`;
- `docs/CRR_DECISION_AND_ROUTING_SPEC.md`;
- `docs/CRR_DOMAIN_MODEL.md`;
- `docs/CRR_VALIDATION_AND_INVARIANTS.md`;
- `docs/CRR_CONFORMANCE_MATRIX.md`;
- `docs/CRR_DATA_FLOW_ARCHITECTURE.md`;
- `docs/CRR_SPECIFICATION_INDEX.md`.

The Phase 4A plan itself becomes the implementation/closure evidence document.

## 10. Definition of done

- Plan committed before implementation.
- Opportunity domain contract implemented with explicit lifecycle and invariants.
- Source route freshness/feasibility gate enforced.
- Tenant isolation and least privilege enforced.
- Exact quantity/money semantics preserved.
- Idempotency, optimistic concurrency, attribution, provenance, and transactional outbox implemented.
- Reversible SQLite/PostgreSQL migration implemented and aligned with SQLAlchemy metadata.
- API is canonical-reference based and rejects inline authority injection.
- Comprehensive domain/API/security/failure/concurrency/rollback tests pass.
- Ruff, format, mypy, pytest, migration upgrade/downgrade/rebuild, SQLAlchemy alignment, PostgreSQL conformance, and all GitHub CI checks are green.
- Normative documentation matches the proven executable behavior.
- PR opened for review; merge remains with the repository owner.

## 11. Execution order

1. Commit this plan first.
2. Audit Phase 3D–3G executable contracts and all normative commercial-conversion sections.
3. Implement the smallest complete Opportunity domain contract.
4. Implement canonical persistence and reversible migration.
5. Implement schemas/API with tenant/scopes/idempotency/ETag semantics.
6. Implement transactional outbox and lifecycle/concurrency handling.
7. Add domain/API/security/failure/rollback/PostgreSQL conformance tests.
8. Run static, formatting, typing, full tests, migration lifecycle, SQLAlchemy alignment, and PostgreSQL conformance.
9. Diagnose and fix every CI failure without weakening requirements.
10. Synchronize normative documentation only after behavior is proven.
11. Add complete closure evidence to this plan.
12. Open the Phase 4A PR; do not merge it automatically.
