# CRR Phase 2 Plan — Demand / Capability / Transformation Foundation

**Status:** Planned
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Base:** Phase 1 conformance closure merged to `main`

## 1. Objective

Extend the executable CRR foundation from physical resource identity/state into the minimum **resource-network reality** required before routing can be implemented safely: Demand, Capability, and Transformation.

Phase 2 will not implement route computation, optimization, Jev, commercial execution, economics, or verification. It establishes canonical, tenant-isolated, attributable, versioned definitions that a later routing phase can consume without inventing semantics.

## 2. Why these objects are the next boundary

The specification's first operational proof is:

```text
ResourceState
→ Demand
→ Capability
→ Transformation
→ Candidate Routes
```

Phase 1 already establishes the authoritative ResourceState side. Demand describes what can be accepted; Capability describes what an organization can physically do; Transformation defines the permitted input/output relationship. These must exist as canonical objects before route computation can be meaningful.

## 3. Phase 2 subphases

### 2A — Demand foundation

Implement the Demand canonical object, persistence, validation, lifecycle transitions, tenant isolation, API endpoints, idempotent creation, optimistic concurrency, attribution, provenance, and executable conformance tests.

### 2B — Capability foundation

Implement Capability with accepted input/output specifications, location, capacity representation, operating-window semantics, status, authorization, provenance, and lifecycle/concurrency rules.

### 2C — Transformation foundation

Implement versioned Transformation definitions connecting accepted input state specifications to output state specifications, including yield/loss semantics, duration, capacity, cost metadata, quality effects, regulatory requirements, and eligible capabilities/locations. This phase must not create physical execution records.

### 2D — Network-reality conformance closure

Audit the three objects together against the protocol, domain model, validation registry, API contract, data-flow architecture, and conformance matrix. Verify reference integrity, tenant boundaries, lifecycle eligibility, exact quantities, temporal rules, idempotency, optimistic concurrency, migration reversibility, and PostgreSQL behavior.

## 4. 2A scope — Demand

### Canonical semantics

Demand represents an organization's need and the conditions under which it will accept a resource state.

The implementation must preserve the specification's distinction between a **requirement** and an observed/available ResourceState. A Demand must never be treated as physical inventory.

The initial model will cover, as applicable to the normative contract:

- stable ID;
- owning organization;
- required state/material specification;
- quantity minimum/target/maximum using exact decimal semantics;
- quality requirements;
- location constraints;
- timing/active window;
- pricing constraints as requirements, not executable economics;
- certifications;
- regulatory constraints;
- substitutions;
- recurrence metadata where representable without inventing routing semantics;
- remaining quantity;
- lifecycle status;
- schema/object version;
- creator/update attribution;
- timestamps;
- provenance.

Do not add fields merely because they appear in a generic object template. Every persisted field must have a defined semantic role.

### Lifecycle

The normative lifecycle is:

```text
DRAFT
  ↓
ACTIVE
  ↓
PAUSED ↔ ACTIVE
  ↓
FULFILLED / EXPIRED / CANCELLED / DISPUTED
```

Only `ACTIVE` demand is eligible for later ordinary routing. Phase 2A will not implement routing selection; it will enforce lifecycle validity at the Demand boundary so later phases can rely on it.

### API

Implement the documented v1 endpoints:

- `GET /v1/demands`
- `POST /v1/demands`
- `GET /v1/demands/{id}`
- `PATCH /v1/demands/{id}`

Mutation semantics must include:

- authentication;
- least-privilege `demands:read` / `demands:write` scopes;
- tenant isolation;
- required idempotency for externally retriable creation/mutation effects;
- optimistic concurrency for mutable lifecycle/content changes;
- machine-readable validation/conflict errors;
- no cross-tenant existence disclosure.

### Persistence

Add an append-safe, versioned Demand table and migration. Mutable fields must use explicit validated mutation semantics. Historical versions/changes required by the specification must remain auditable; no generic update may silently rewrite protocol history.

Reference integrity must prevent a Demand from referencing objects belonging to another organization where such references are introduced.

### Validation

At minimum, executable evidence must cover:

- missing required fields;
- unknown/invalid status;
- illegal lifecycle transitions;
- negative quantity;
- non-string/floating-point authoritative quantity input;
- malformed/excessive-precision quantity where applicable;
- zero quantity semantics according to the 0.1.2 amendment;
- invalid or incompatible units where a quantity unit is supplied;
- invalid timezone/temporal window;
- invalid min/target/max relationships;
- invalid remaining quantity relationships;
- invalid location/reference ownership;
- missing provenance;
- unauthorized actor/scope;
- revoked/inactive credentials;
- cross-tenant reads/writes/reference injection;
- stale version;
- duplicate idempotency request;
- reused idempotency key with different payload;
- rollback when persistence/outbox/event creation fails;
- database constraint failure.

### Events

Demand mutations must emit immutable outbox events transactionally with canonical state changes. Event payloads must identify the Demand, organization, actor, version, request/correlation context, and semantic event type. No event may be published for a mutation that did not commit.

## 5. Cross-phase invariants

Phase 2 must preserve all Phase 1 guarantees:

1. exact decimal authoritative quantities;
2. no authoritative float path;
3. tenant isolation;
4. least-privilege authorization;
5. attributable mutations;
6. provenance;
7. idempotency;
8. optimistic concurrency;
9. transactional outbox behavior;
10. reversible SQLite/PostgreSQL migrations;
11. database-level protections where required;
12. machine-readable API errors;
13. ResourceState physical history remains immutable;
14. Demand does not mutate Resource or ResourceState merely by being created or updated.

## 6. Testing strategy

Every increment must include unit/domain tests, API tests, persistence/migration tests, security tests, failure-path tests, and PostgreSQL-specific conformance where SQLite cannot establish the required behavior.

The PostgreSQL CI job remains mandatory. A passing SQLite suite is not sufficient evidence for database concurrency or dialect-specific behavior.

The test matrix must include happy paths and negative cases; tests must validate the intended implementation rather than weaken requirements to obtain green CI.

## 7. Documentation/conformance synchronization

Before implementation, affected normative documents are re-read. After implementation, the API contract, domain model, validation/invariants document, data-flow architecture, conformance matrix, and Phase 2 plan must agree with externally observable behavior.

The conformance matrix must identify evidence for every implemented Phase 2 requirement. No Phase 2 subphase is complete merely because code exists; the relevant tests and CI evidence must be green.

## 8. Definition of done for 2A

- Demand model/domain semantics implemented.
- Database migration is reversible and PostgreSQL-compatible.
- API endpoints conform to the v1 contract.
- Lifecycle transitions are explicit and validated.
- Tenant isolation and least-privilege scopes are enforced.
- Exact quantity/unit/time validation is enforced at canonical boundaries.
- Idempotency and optimistic concurrency are executable and tested.
- Transactional outbox events are emitted atomically.
- Failure/rollback behavior is tested.
- SQLite and PostgreSQL CI are green.
- Documentation and conformance evidence are synchronized.
- Git working state, commit SHA, PR, and CI results are identifiable.

## 9. Explicit exclusions from 2A

Do not implement:

- route computation;
- graph search;
- optimization;
- Jev/LLM decision support;
- commercial offers/agreements/transactions;
- physical execution;
- evidence verification;
- autonomous actions;
- a graph database;
- new infrastructure not required by Demand semantics.

## 10. Execution order

1. Commit this plan first.
2. Audit the existing Phase 1 implementation and migrations before adding Demand.
3. Implement the smallest complete Demand domain/persistence boundary.
4. Add schemas and API behavior.
5. Add unit/API/security/failure tests.
6. Add PostgreSQL-specific conformance evidence where required.
7. Run formatting, linting, type-checking, migrations, tests, and CI.
8. Fix every failure before declaring 2A complete.
9. Synchronize documentation/conformance evidence only after behavior is proven.
10. Open the PR with the plan and evidence clearly recorded.
