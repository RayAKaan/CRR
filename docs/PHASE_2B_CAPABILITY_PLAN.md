# Phase 2B Capability Foundation Plan

**Status:** Planned
**Base:** Phase 2A Demand API merged to `main`
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Branch:** `phase2/capability-foundation`

## 1. Objective

Implement the canonical Capability boundary defined by the CRR domain model and Phase 2 plan. Capability describes what an organization can physically do; it is a reusable declaration of operational ability, not proof that an operation occurred and not an execution record.

The increment must establish a tenant-isolated, attributable, versioned Capability object with validated accepted input/output specifications, capacity, operating windows, location, authorization/certification metadata, provenance, lifecycle, persistence, API behavior, idempotency, optimistic concurrency, transactional outbox behavior, and executable conformance evidence.

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

Capability describes an organization's physical ability. It must remain distinct from:

- ResourceState: what physically exists.
- Demand: what is required/accepted.
- Transformation: the reusable input/output process definition.
- Execution: what actually happened.

Capability may reference Transformation definitions, but this increment must not manufacture or execute transformations.

A capability becoming `ACTIVE` does not make any ResourceState available and does not mutate Demand, Resource, or ResourceState.

## 4. Canonical fields

The implementation must only persist fields with an explicit semantic role. The planned boundary is:

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
- `created_by` / update attribution as required by the existing API conventions;
- `provenance`;
- `created_at` / `updated_at`.

The API representation must use exact decimal strings for authoritative quantities and timezone-aware timestamps.

## 5. Lifecycle

The canonical lifecycle is:

```text
DRAFT
  ↓
ACTIVE
  ↓
SUSPENDED / EXPIRED / REVOKED
```

The implementation must explicitly define legal transitions rather than accepting arbitrary status changes. Terminal states must not be silently reactivated unless the normative contract explicitly permits it. Only an `ACTIVE` capability is eligible for later execution/routing consideration; this increment does not implement selection.

## 6. Reference and ownership rules

- A Capability belongs to exactly one organization.
- Its Location reference, when supplied, must belong to the same organization unless the canonical specification explicitly defines a separately authorized shared location model; do not invent cross-tenant semantics.
- Transformation references, when introduced, must not be interpreted as proof of transformation execution.
- Actor attribution must belong to the authenticated organization.
- Cross-tenant reads must behave as not-found/non-disclosure.
- Cross-tenant writes/reference injection must be rejected.

## 7. Validation rules

At minimum, executable tests must cover:

- missing required fields;
- unknown/invalid status;
- illegal lifecycle transitions;
- negative capacity;
- non-string/floating-point authoritative decimal input;
- malformed/excessive-precision decimal input where applicable;
- zero capacity semantics where permitted by the normative rules;
- unknown/incompatible units;
- inconsistent capacity/minimum-batch units;
- naive operating-window timestamps;
- end <= start;
- missing/invalid location ownership;
- missing provenance;
- unauthorized actor/scope;
- revoked/inactive credentials;
- cross-tenant reads/writes/reference injection;
- stale version;
- duplicate idempotency request;
- reused idempotency key with different payload;
- persistence constraint failure;
- rollback when canonical mutation, idempotency record, or outbox event cannot commit;
- PostgreSQL-specific behavior where SQLite cannot prove the invariant.

Validation must occur before canonical mutation. Database constraints must protect identity/reference integrity where appropriate; application/domain validation remains authoritative for semantic relationships not safely expressible as relational constraints.

## 8. API contract

Implement the documented v1 Capability endpoints:

- `GET /v1/capabilities`
- `POST /v1/capabilities`
- `GET /v1/capabilities/{id}`
- `PATCH /v1/capabilities/{id}`

Mutation requirements:

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

Reads require `capabilities:read` and must not disclose another organization's object existence.

## 9. Persistence and migration

Add an append-safe, versioned `capabilities` table and reversible Alembic migration based on the current migration head.

The schema must include:

- organization foreign key;
- location foreign key where represented;
- actor foreign key for creator attribution;
- exact decimal storage for authoritative quantities;
- timezone-aware timestamps;
- JSON fields only for genuinely structured semantic specifications/metadata;
- indexes needed for tenant/status/window queries;
- reference integrity constraints.

The migration must upgrade, downgrade, and rebuild cleanly. SQLAlchemy metadata must match the migration under PostgreSQL CI.

## 10. Events and idempotency

Capability mutations must use the established transactional outbox/idempotency infrastructure.

Event types:

- `capability.created`
- `capability.updated`

Each event must identify capability ID, organization, actor, aggregate version, request/correlation context, event type/version, and provenance. No event may survive a failed canonical mutation transaction.

Repeated equivalent idempotent mutations must return the existing logical effect without duplicate externally observable events. Reusing an idempotency key for a materially different request must return a conflict.

## 11. Test strategy

Tests must be layered:

1. Domain invariants and lifecycle.
2. Persistence/exact decimal/reference behavior.
3. API CRUD and serialization.
4. Authorization and tenant isolation.
5. Idempotency and optimistic concurrency.
6. Failure/rollback behavior.
7. Migration lifecycle and SQLAlchemy alignment.
8. PostgreSQL conformance for dialect/transaction/reference behavior.
9. Regression suite for all existing Phase 1/2A behavior.

Tests must prove intended behavior; no test may be weakened or removed to obtain green CI.

## 12. Documentation synchronization

After behavior is proven, synchronize only the affected documentation:

- `docs/PHASE_2_PLAN.md` status/evidence for 2B as appropriate;
- `docs/CRR_CONFORMANCE_MATRIX.md` implementation evidence if its structure supports it;
- `docs/CRR_API_CONTRACT.md` only if externally observable Capability behavior needs clarification;
- `docs/CRR_VALIDATION_AND_INVARIANTS.md` only where executable Capability validation needs explicit normative coverage.

Do not mark 2B complete before CI and PostgreSQL evidence are green.

## 13. Execution order

1. Commit this plan first.
2. Re-audit current Phase 1/2A auth, pagination, idempotency, outbox, exact-decimal, unit, migration, and error helpers.
3. Implement the Capability domain model and tests.
4. Implement persistence and migration.
5. Implement API schemas and endpoints by reusing established infrastructure.
6. Add security, reference-integrity, failure, idempotency, concurrency, and PostgreSQL tests.
7. Run local format/lint/typecheck/tests/migrations.
8. Open PR only after local checks are clean.
9. Monitor GitHub CI; diagnose and fix every failure until all required jobs pass.
10. Synchronize conformance documentation after behavior is proven.
11. Provide the final commit, PR, and CI evidence with explicit remaining limitations.
