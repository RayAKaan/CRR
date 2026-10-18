# CRR Phase 4B — Offer Foundation Plan

**Status:** Planned
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Base:** Phase 4A Opportunity foundation merged to `main`

## 1. Objective

Establish the next explicit commercial boundary: a durable, tenant-isolated, auditable `Offer` containing proposed commercial terms derived from an existing `Opportunity`.

An Offer is a proposal. It is not acceptance, an Agreement, a Transaction, a Reservation, physical execution, or evidence of completion.

## 2. Why this increment is required

The canonical commercial chain is:

`feasible Route → Opportunity → Offer → Agreement → Transaction → Execution → Evidence`

Phase 4A made Opportunity durable commercial intent. Phase 4B makes the first explicit proposal state executable while preserving the boundary between proposing terms and accepting them.

## 3. Architectural boundary

```text
Existing Opportunity
      ↓
Eligibility / freshness / tenant gate
      ↓
Immutable Offer terms snapshot
      ↓
Offer lifecycle
      ↓
Future Agreement acceptance
```

The Offer must reference canonical Opportunity state and snapshot the proposed terms required to reproduce what was proposed at creation time. Creating or mutating an Offer must never mutate ResourceState, Demand, Capability, Transformation, EconomicModel, or Opportunity canonical truth.

## 4. Scope

### 4.1 Offer domain contract

Implement an immutable-at-creation, versioned Offer with:

- organization/tenant;
- source Opportunity reference and version;
- proposer and recipient actors/organizations;
- exact quantity and canonical unit registry version;
- exact price and explicit currency;
- delivery terms;
- timing terms;
- route-assumption snapshot/provenance;
- conditions;
- validity/expiration window;
- explicit lifecycle status;
- attribution and provenance;
- optimistic-concurrency version.

The implementation must reject missing authority references, cross-tenant participants, invalid windows, negative quantities/prices where prohibited, malformed exact decimals, unknown units/currencies, and inconsistent Opportunity provenance.

### 4.2 Lifecycle

The implementation will use a bounded proposal lifecycle:

`DRAFT → OPEN → ACCEPTED / REJECTED / EXPIRED / WITHDRAWN`

Terminal states cannot transition further. Acceptance changes only Offer protocol state; it does not create an Agreement or Transaction in Phase 4B.

### 4.3 Canonical-reference gate

Offer creation must reference an existing Opportunity. The API must not accept authoritative ResourceState, Demand, route, quantity, regulatory, or economic facts inline as substitutes for canonical references.

Creation requires:

- same-tenant Opportunity;
- Opportunity in an eligible non-terminal proposal state;
- current Opportunity version;
- active underlying Demand where applicable;
- quantity/unit compatible with the Opportunity snapshot;
- explicit proposer/recipient authority;
- validity window bounded by the Opportunity validity window;
- explicit monetary context.

### 4.4 Persistence and API

Add tenant-isolated canonical persistence and reversible Alembic migration.

Expose:

- `POST /v1/offers`;
- `GET /v1/offers`;
- `GET /v1/offers/{id}`;
- lifecycle mutation through a version-checked endpoint using `If-Match`.

Mutating requests require `Idempotency-Key`. Reads and writes use least-privilege Offer scopes.

### 4.5 Outbox and concurrency

Offer creation and lifecycle mutation use the existing transactional outbox boundary. Replay with the same idempotency key and identical payload returns the original result; reuse with a different payload is a conflict. Lifecycle mutation requires the current ETag/version.

### 4.6 Security

Enforce organization isolation on every Offer read/write and participant reference. An actor must possess the required scope and belong to the authenticated organization. Cross-tenant Opportunity, proposer, recipient, or EconomicModel references are rejected.

## 5. Explicit non-goals

- Agreement creation or legal acceptance;
- Transaction creation;
- Reservation or capacity commitment;
- physical execution;
- evidence verification;
- autonomous acceptance;
- Jev/LLM decision authority;
- external pricing/geographic services;
- candidate rediscovery or route recomputation;
- mutation of canonical physical state;
- new infrastructure.

## 6. Domain invariants

1. Every Offer belongs to exactly one organization.
2. Every Offer references an existing same-tenant Opportunity.
3. The source Opportunity version is retained for auditability.
4. Offer terms are explicit and exact; authoritative floats are never accepted.
5. Quantity and unit are validated against the canonical unit registry.
6. Price is exact decimal and currency is explicit.
7. Validity cannot exceed the source Opportunity validity window.
8. Proposer and recipient authority is explicit and tenant-safe.
9. Route assumptions are provenance snapshots, not newly authoritative route facts.
10. Offer lifecycle transitions are explicit and optimistic-concurrency protected.
11. Idempotency keys are required for mutations; conflicting reuse is rejected.
12. Creation and lifecycle changes emit transactional outbox events.
13. Offer creation and mutation never alter Opportunity, ResourceState, Demand, Capability, Transformation, or EconomicModel canonical state.
14. An Offer is never evidence of acceptance, agreement, execution, settlement, or physical completion.
15. Cross-tenant references are rejected rather than silently filtered into an apparently valid proposal.

## 7. Testing strategy

Coverage must include:

- domain lifecycle and immutable/version invariants;
- valid Offer creation from a valid Opportunity;
- invalid Opportunity state/version;
- expired or over-broad validity window;
- exact-decimal quantity and price validation;
- zero/negative boundary behavior according to contract;
- unknown unit and invalid currency;
- cross-tenant Opportunity/participant/EconomicModel references;
- least-privilege scope rejection;
- idempotent create replay and conflicting key reuse;
- ETag optimistic-concurrency failure;
- illegal lifecycle transition;
- transactional outbox event;
- persistence rollback;
- API canonical-reference and inline-authority rejection;
- proof that Offer creation does not mutate Opportunity or physical canonical objects;
- SQLite migration lifecycle;
- PostgreSQL migration lifecycle, model alignment, and conformance;
- full existing Phase 1–4A regression suite.

## 8. Documentation synchronization

Before implementation, audit the canonical domain, protocol, API, validation/invariants, data-flow, conformance, specification-index, and normative-amendment documents. Phase 4B must not invent semantics that conflict with the canonical `Offer` definition. After behavior is proven, synchronize this plan and any required contract/conformance references with the exact implementation.

## 9. Definition of done

- Plan committed before implementation.
- Domain contract and lifecycle implemented.
- Canonical Opportunity reference and freshness gate implemented.
- Tenant isolation and least privilege implemented.
- Exact quantity/price/unit/currency semantics implemented.
- Idempotency, optimistic concurrency, attribution, provenance, and transactional outbox implemented.
- Reversible SQLite/PostgreSQL migration and SQLAlchemy alignment verified.
- API canonical-reference boundary implemented.
- Comprehensive domain/API/security/failure/conformance tests implemented.
- Ruff, format, mypy, pytest, migration lifecycle, SQLAlchemy alignment, PostgreSQL conformance, and all GitHub CI checks green.
- Documentation/conformance evidence matches actual behavior.
- PR opened for review; merge remains with repository owner.

## 10. Execution order

1. Commit this plan first.
2. Audit Phase 4A Opportunity implementation and all normative commercial/API documents.
3. Implement Offer domain contracts and invariants.
4. Implement persistence model and reversible migration.
5. Implement schemas/API/security/idempotency/concurrency/outbox.
6. Add domain, persistence, API, security, failure, and regression tests.
7. Run static, formatting, typing, full tests, migration lifecycle, and PostgreSQL conformance.
8. Diagnose and fix every CI failure without weakening tests or requirements.
9. Synchronize documentation only after executable behavior is proven.
10. Open the Phase 4B PR with closure evidence.
