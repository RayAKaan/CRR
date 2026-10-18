# CRR Phase 4B — Offer Foundation Plan

**Status:** Complete
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

Implemented as an immutable-at-creation, versioned Offer with:

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

The implementation rejects missing authority references, cross-tenant participants, invalid windows, negative quantities/prices where prohibited, malformed exact decimals, unknown units, and inconsistent Opportunity monetary/unit context.

### 4.2 Lifecycle

The implementation uses the bounded proposal lifecycle:

`DRAFT → OPEN → ACCEPTED / REJECTED / EXPIRED / WITHDRAWN`

Terminal states cannot transition further. Acceptance changes only Offer protocol state; it does not create an Agreement or Transaction in Phase 4B.

### 4.3 Canonical-reference gate

Offer creation references an existing Opportunity. The API does not accept authoritative ResourceState, Demand, route, quantity, regulatory, or economic facts inline as substitutes for canonical references.

Creation enforces:

- same-tenant Opportunity;
- current Opportunity version;
- open Opportunity state and freshness;
- compatible quantity/unit snapshot;
- explicit proposer/recipient authority;
- validity window bounded by the Opportunity validity window;
- explicit monetary context.

### 4.4 Persistence and API

Implemented tenant-isolated canonical persistence and a reversible Alembic migration.

Exposed:

- `POST /v1/offers`;
- `GET /v1/offers`;
- `GET /v1/offers/{id}`;
- lifecycle mutation through `PATCH /v1/offers/{id}` with `If-Match`.

Mutating requests require `Idempotency-Key`. Reads and writes use least-privilege Offer scopes.

### 4.5 Outbox and concurrency

Offer creation and lifecycle mutation use the existing transactional outbox boundary. Replay with the same idempotency key and identical payload returns the original result; reuse with a different payload is a conflict. Lifecycle mutation requires the current ETag/version.

### 4.6 Security

Organization isolation is enforced on every Offer read/write and participant reference. The authenticated actor must possess the required scope and belong to the authenticated organization. Cross-tenant Opportunity and participant references are rejected.

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

## 7. Testing strategy and evidence

Coverage includes:

- domain lifecycle and immutable/version invariants;
- valid Offer creation from a valid Opportunity;
- invalid Opportunity state/version;
- expired or over-broad validity window;
- exact-decimal quantity and price validation;
- invalid unit/currency context;
- cross-tenant participant references;
- least-privilege scope rejection;
- idempotent create replay;
- ETag optimistic-concurrency behavior;
- illegal lifecycle transition;
- transactional outbox event;
- API canonical-reference boundary;
- proof that Offer creation does not mutate Opportunity state;
- SQLite migration lifecycle;
- PostgreSQL migration lifecycle, model alignment, and conformance;
- full existing Phase 1–4A regression suite.

Final CI run: `39148506841` on commit `22bbbb8f38839ab8205484ac8c7242e085bc08bb`.

- Ruff check: PASS
- Ruff format check: PASS
- Mypy: PASS
- Pytest: PASS — 162 passed, 1 skipped (the expected PostgreSQL-only test)
- PostgreSQL migration upgrade: PASS
- PostgreSQL migration downgrade: PASS
- PostgreSQL rebuild: PASS
- SQLAlchemy/model alignment: PASS
- PostgreSQL conformance: PASS
- GitHub Actions test job: SUCCESS
- GitHub Actions PostgreSQL job: SUCCESS

Intermediate CI failures were diagnosed and corrected without weakening requirements or tests: import/lint formatting, API formatting, and an incorrect lifecycle fixture that attempted to reopen an already-open Offer.

## 8. Documentation synchronization

The Phase 4B plan is the implementation/closure record for the new commercial boundary. It preserves the existing normative separation between Opportunity, Offer, Agreement, Transaction, Execution, and Evidence and introduces no execution or acceptance semantics. The executable API surface, domain contracts, validation behavior, migration, tests, and conformance evidence are aligned with the implementation on this branch.

## 9. Definition of done

- Plan committed before implementation: complete.
- Domain contract and lifecycle implemented: complete.
- Canonical Opportunity reference and freshness gate implemented: complete.
- Tenant isolation and least privilege implemented: complete.
- Exact quantity/price/unit/currency semantics implemented: complete.
- Idempotency, optimistic concurrency, attribution, provenance, and transactional outbox implemented: complete.
- Reversible SQLite/PostgreSQL migration and SQLAlchemy alignment verified: complete.
- API canonical-reference boundary implemented: complete.
- Comprehensive domain/API/security/failure/regression tests implemented: complete.
- Ruff, format, mypy, pytest, migration lifecycle, SQLAlchemy alignment, PostgreSQL conformance, and all GitHub CI checks green: complete.
- Documentation/conformance evidence matches actual behavior: complete.
- PR opened for review; merge remains with repository owner: complete.

## 10. Execution order

1. Commit this plan first. **Complete.**
2. Audit Phase 4A Opportunity implementation and normative commercial/API documents. **Complete.**
3. Implement Offer domain contracts and invariants. **Complete.**
4. Implement persistence model and reversible migration. **Complete.**
5. Implement schemas/API/security/idempotency/concurrency/outbox. **Complete.**
6. Add domain, persistence, API, security, failure, and regression tests. **Complete.**
7. Run static, formatting, typing, full tests, migration lifecycle, and PostgreSQL conformance. **Complete.**
8. Diagnose and fix every CI failure without weakening tests or requirements. **Complete.**
9. Synchronize documentation after executable behavior was proven. **Complete.**
10. Open the Phase 4B PR with closure evidence. **Complete.**

## 11. Closure

- Branch: `phase4b/offer-foundation`
- PR: #20
- Implementation/closure commit: `22bbbb8f38839ab8205484ac8c7242e085bc08bb`
- Final fully green CI run: `39148506841`
- Merge remains with the repository owner.
