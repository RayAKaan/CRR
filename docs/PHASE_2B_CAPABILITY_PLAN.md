# Phase 2B Capability Foundation Plan

**Status:** Implemented — CI green
**Base:** Phase 2A Demand API merged to `main`
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Branch:** `phase2/capability-foundation`

## 1. Objective

Implement the canonical Capability boundary defined by the CRR domain model and Phase 2 plan. Capability describes what an organization can physically do; it is a reusable declaration of operational ability, not proof that an operation occurred and not an execution record.

The increment establishes a tenant-isolated, attributable, versioned Capability object with validated accepted input/output specifications, capacity, operating windows, location, authorization/certification metadata, provenance, lifecycle, persistence, API behavior, idempotency, optimistic concurrency, transactional outbox behavior, and executable conformance evidence.

## 2. Scope boundary

### Included

- Capability canonical domain object and invariants.
- Capability persistence model and reversible migration.
- Exact-decimal capacity semantics and unit-registry validation.
- Accepted input specifications.
- Output specifications.
- Transformation references as opaque/versioned references only; no Transformation implementation in 2B.
- Capability location reference with same-tenant ownership validation.
- Operating-window semantics using timezone-aware timestamps.
- Capacity representation including unit and operating constraints.
- Minimum batch where required by the normative model.
- Processing-cost metadata as a requirement/metadata field only; no economic calculation.
- Certifications and regulatory eligibility metadata.
- Capability lifecycle and validated transitions.
- Creator/update attribution, provenance, timestamps, and versioning.
- Tenant isolation and least-privilege `capabilities:read` / `capabilities:write` authorization.
- `GET /v1/capabilities`, `POST /v1/capabilities`, `GET /v1/capabilities/{id}`, `PATCH /v1/capabilities/{id}`.
- Required idempotency for mutations and optimistic concurrency for mutable updates.
- Transactional immutable outbox events.
- API, domain, persistence, security, failure-path, rollback, idempotency, concurrency, and PostgreSQL-specific tests.
- Synchronization of affected conformance evidence after executable behavior is proven.

### Explicitly excluded

- Transformation object implementation or execution.
- Route computation, graph search, or optimization.
- Jev/LLM decision support.
- Commercial offers, agreements, or transactions.
- Physical execution records.
- Evidence verification.
- Autonomous actions.
- New infrastructure unrelated to Capability semantics.
- Using Capability records as proof that an operation happened.

## 3. Normative semantic model

Capability describes an organization's physical ability. It remains distinct from:

- ResourceState: what physically exists.
- Demand: what is required/accepted.
- Transformation: the reusable input/output process definition.
- Execution: what actually happened.

Capability may reference Transformation definitions, but this increment does not manufacture or execute transformations.

A capability becoming `ACTIVE` does not make any ResourceState available and does not mutate Demand, Resource, or ResourceState.

## 4. Canonical fields

The implemented boundary persists:

- stable `id`;
- owning `organization_id`;
- accepted input specifications;
- output specifications;
- optional transformation references;
- capacity value/unit and unit-registry version;
- operating window start/end;
- location reference;
- minimum batch where applicable;
- processing-cost metadata without executable economics;
- certifications;
- regulatory eligibility/constraints;
- lifecycle `status`;
- object `version`;
- `created_by` attribution;
- `provenance`;
- `created_at` / `updated_at`.

The API representation uses exact decimal strings for authoritative quantities and timezone-aware timestamps.

## 5. Lifecycle

The implemented lifecycle is:

```text
DRAFT
  ↓
ACTIVE
  ↓
SUSPENDED / EXPIRED / REVOKED
```

Legal transitions are explicit. Terminal states are not silently reactivated. Only an `ACTIVE` capability is eligible for later execution/routing consideration; this increment does not implement selection.

## 6. Reference and ownership rules

- A Capability belongs to exactly one organization.
- Its Location reference must belong to the same organization.
- Transformation references are not execution proof.
- Actor attribution belongs to the authenticated organization.
- Cross-tenant reads behave as not-found/non-disclosure.
- Cross-tenant reference injection is rejected.

## 7. Validation rules

Executable coverage includes:

- missing required fields;
- unknown/invalid status;
- illegal lifecycle transitions;
- negative capacity;
- non-string/floating-point authoritative decimal input;
- zero-capacity semantics;
- unknown units;
- inconsistent capacity/minimum-batch units;
- naive operating-window timestamps;
- invalid operating windows;
- missing/invalid location ownership;
- missing provenance;
- insufficient authorization;
- cross-tenant reads/writes;
- stale versions;
- duplicate idempotency requests;
- idempotency-key reuse with different payloads;
- persistence and rollback behavior;
- PostgreSQL migration/model/conformance behavior.

Validation occurs before canonical mutation. Relational constraints protect identity/reference integrity while domain validation protects semantic relationships.

## 8. API contract

Implemented v1 endpoints:

- `GET /v1/capabilities`
- `POST /v1/capabilities`
- `GET /v1/capabilities/{id}`
- `PATCH /v1/capabilities/{id}`

Mutation requirements are enforced:

- authenticated principal;
- `capabilities:write` or admin scope;
- tenant isolation;
- `Idempotency-Key` required;
- `If-Match` required for mutable updates;
- machine-readable errors;
- ETag based on object version;
- immutable identity/ownership fields;
- lifecycle transitions delegated to the domain model;
- no unrestricted physical execution mutation.

Reads require `capabilities:read` and do not disclose another organization's object existence.

## 9. Persistence and migration

The `capabilities` table is implemented with reversible Alembic migration `c4a1b2c3d4e5`, following Demand migration `b7f0d8d1e2c3`.

The schema includes organization, location, and creator foreign keys; exact decimal capacity/minimum-batch storage; timezone-aware operating timestamps; structured JSON specifications/metadata; and tenant/status/window/location indexes.

PostgreSQL CI verifies upgrade, downgrade, rebuild, SQLAlchemy migration/model alignment, and PostgreSQL conformance.

## 10. Events and idempotency

Capability mutations use the established transactional outbox/idempotency infrastructure.

Event types:

- `capability.created`
- `capability.updated`

Events identify capability ID, organization, actor, aggregate version, request/correlation context, event type/version, and provenance. Idempotent replays return the existing logical effect without duplicate events; key reuse with a different payload conflicts.

## 11. Test strategy

Tests are layered across:

1. Domain invariants and lifecycle.
2. Persistence/exact decimal/reference behavior.
3. API CRUD and serialization.
4. Authorization and tenant isolation.
5. Idempotency and optimistic concurrency.
6. Failure-path behavior.
7. Migration lifecycle and SQLAlchemy alignment.
8. PostgreSQL conformance.
9. Regression coverage for existing Phase 1/2A behavior.

The final CI run proves Ruff check, Ruff format, mypy, pytest, PostgreSQL migration lifecycle, model alignment, and PostgreSQL conformance all pass.

## 12. Completion evidence

- **PR:** #7 — `Phase 2B: Capability foundation`
- **Final commit:** `d96baf83e7c209821e9bd4000d9105e8cb164161`
- **Final CI run:** `39073522326`
- **Test job:** `117515857902` — success
- **PostgreSQL job:** `117515858033` — success
- **Ruff check:** success
- **Ruff format:** success
- **mypy:** success
- **pytest:** success
- **PostgreSQL upgrade:** success
- **PostgreSQL downgrade:** success
- **PostgreSQL rebuild:** success
- **Migration/model alignment:** success
- **PostgreSQL conformance:** success

No 2B completion claim is based on documentation alone; executable behavior and both CI jobs are green.

## 13. Explicit exclusions from 2B

This increment does not implement:

- Transformation object implementation or execution;
- route computation;
- graph search;
- optimization;
- Jev/LLM decision support;
- commercial offers/agreements/transactions;
- physical execution;
- evidence verification;
- autonomous actions;
- a graph database;
- new infrastructure not required by Capability semantics.

## 14. Next phase

Proceed to Phase 2C Transformation foundation only after PR #7 is merged to `main`. Re-audit the canonical protocol, domain model, API contract, validation/invariants, conformance matrix, and current implementation before creating the next phase plan.
