# Phase 2C Transformation Foundation Plan

**Status:** Planned
**Base:** Phase 2B Capability foundation merged to `main`
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Branch:** `phase2/transformation-foundation`

## 1. Objective

Implement the canonical Transformation boundary defined by the CRR domain model and Phase 2 plan. A Transformation is a reusable, versioned definition of a permitted or known input/output relationship. It is not a physical execution record and does not prove that a transformation occurred.

The increment must establish a tenant-isolated, attributable, versioned Transformation object with explicit input/output state specifications, yield/loss semantics, duration, capacity, cost metadata, quality effects, regulatory requirements, eligible capability/location references, lifecycle and concurrency semantics, persistence, API behavior, idempotency, transactional outbox behavior, and executable conformance evidence.

## 2. Scope boundary

### Included

- Canonical Transformation domain object and invariants.
- Reversible SQLAlchemy/Alembic persistence and PostgreSQL compatibility.
- Input state specifications and output state specifications.
- Yield bounds and explicit loss/residual semantics without executing material accounting.
- Duration/operating timing semantics with timezone-aware timestamps or explicit duration representation.
- Capacity semantics using exact decimal quantities and unit-registry versions.
- Cost metadata as declared transformation requirements/metadata only; no economic calculation.
- Quality effects as declarative specifications only.
- Regulatory requirements as declarative constraints only.
- Eligible capability references and location references with same-tenant ownership validation.
- Lifecycle, attribution, provenance, timestamps, and optimistic versioning.
- Least-privilege `transformations:read` / `transformations:write` authorization and tenant isolation.
- `GET /v1/transformations`, `POST /v1/transformations`, `GET /v1/transformations/{id}`, `PATCH /v1/transformations/{id}`.
- Required idempotency for mutations and optimistic concurrency for mutable updates.
- Transactional immutable outbox events.
- Domain, persistence, API, authorization, tenant-isolation, idempotency, concurrency, rollback, migration, and PostgreSQL conformance tests.
- Documentation/conformance synchronization after executable behavior is proven.

### Explicitly excluded

- Executing a transformation.
- Creating or mutating ResourceState as a side effect of Transformation CRUD.
- Route computation, graph search, optimization, or allocation.
- Jev/LLM decision support.
- Commercial offers, agreements, or transactions.
- Physical execution records.
- Evidence verification.
- Autonomous actions.
- Graph-database infrastructure.
- Economic calculations or settlement.

## 3. Normative semantic model

Transformation remains distinct from:

- ResourceState: the authoritative physical state that exists.
- Demand: the requirement/acceptance condition.
- Capability: an organization's declared physical ability.
- Execution: the record of what actually happened.

A Transformation definition may reference eligible capabilities and locations, but those references do not establish availability, capacity at a particular time, or proof of execution. Transformation CRUD MUST NOT mutate Resource, ResourceState, Demand, or Capability state.

## 4. Canonical fields

The boundary should persist only fields justified by the normative model:

- stable `id`;
- owning `organization_id`;
- input state specifications;
- output state specifications;
- yield bounds;
- loss/residual semantics;
- duration/operating timing;
- capacity and capacity unit/registry version;
- cost metadata;
- quality effects;
- regulatory requirements;
- eligible capability references;
- eligible location references where applicable;
- lifecycle `status`;
- object `version`;
- `created_by` attribution;
- `provenance`;
- `created_at` / `updated_at`.

Authoritative quantities MUST use exact decimal string input at the API boundary. Timestamps MUST be timezone-aware and canonicalized to UTC.

## 5. Lifecycle and mutation semantics

Use an explicit lifecycle only where required by the Transformation contract. The implementation must not invent a universal physical-state machine. Any supported lifecycle transitions must be deterministic, version-incrementing, and auditable.

Mutable content/lifecycle changes require `If-Match`; mutation requests require `Idempotency-Key`. Terminal lifecycle states, if defined by the contract, cannot be silently reactivated.

## 6. Reference integrity and ownership

- A Transformation belongs to exactly one organization.
- Referenced Capability objects must belong to the same organization.
- Referenced Location objects must belong to the same organization where introduced.
- Capability references are declarations of eligibility, not execution proof.
- Cross-tenant reads must not disclose existence.
- Cross-tenant reference injection must fail before mutation.
- References must be validated against canonical relational state rather than a derived graph.

## 7. Validation rules

Executable evidence must cover, as applicable:

- missing required fields;
- unknown/invalid lifecycle status;
- illegal lifecycle transitions;
- negative/excessively precise/non-string authoritative quantities;
- unknown or incompatible units;
- invalid yield bounds;
- invalid loss/residual relationships;
- invalid or inconsistent capacity semantics;
- invalid duration/timing;
- missing or cross-tenant Capability/Location references;
- missing provenance;
- unauthorized actor/scope;
- revoked/inactive credentials;
- stale `If-Match` version;
- duplicate idempotency request;
- reused idempotency key with a different payload;
- persistence constraint failure;
- transactional rollback when state/event/idempotency persistence fails;
- migration upgrade/downgrade/rebuild;
- SQLite/PostgreSQL behavior where dialect differences matter.

Validation must precede canonical mutation. Declarative Transformation metadata must not be treated as observed physical fact.

## 8. API contract

Implement the documented v1 CRUD boundary:

- `GET /v1/transformations`
- `POST /v1/transformations`
- `GET /v1/transformations/{id}`
- `PATCH /v1/transformations/{id}`

Mutations require authentication, `transformations:write` or the existing administrative scope, tenant isolation, idempotency, and `If-Match` for updates. Reads require `transformations:read` and must not disclose another tenant's object.

Responses must preserve exact decimal representations, stable IDs, versions, attribution, provenance, and machine-readable errors consistent with the existing v1 API boundary.

## 9. Persistence and migration

Add a dedicated `transformations` table and reversible Alembic migration after the current Capability migration. Use existing exact-decimal and timezone-aware types and existing metadata registration patterns. Relational foreign keys/ownership constraints must prevent invalid canonical references where representable by the existing schema.

Migration lifecycle must be tested through upgrade, downgrade, rebuild, and SQLAlchemy metadata/model alignment on PostgreSQL.

## 10. Events and idempotency

Mutations emit immutable transactional outbox events:

- `transformation.created`
- `transformation.updated`

Events must identify transformation ID, organization, actor, aggregate version, event type/version, correlation/request context, idempotency context, and provenance. Retries with the same request return the same logical effect; key reuse with a different request conflicts; no event survives a rolled-back mutation.

## 11. Test strategy

Tests are layered across:

1. Domain invariants and lifecycle.
2. Exact-decimal/unit/duration validation.
3. Persistence and reference integrity.
4. API CRUD and serialization.
5. Authorization and tenant isolation.
6. Idempotency and optimistic concurrency.
7. Failure-path and rollback behavior.
8. Migration lifecycle and model alignment.
9. PostgreSQL-specific conformance.
10. Regression coverage for Phase 1, Demand, and Capability.

The final completion gate is full CI: Ruff check, Ruff format, mypy, full pytest, PostgreSQL migration lifecycle, migration/model alignment, and PostgreSQL conformance.

## 12. Documentation/conformance synchronization

After behavior is proven, synchronize the affected implementation/conformance evidence with the canonical protocol, domain model, API contract, validation/invariants, data-flow architecture, and Phase 2 plan. Documentation must describe observable behavior actually implemented; it must not be used as evidence in place of tests.

## 13. Definition of done

- Transformation domain semantics are implemented and tested.
- Persistence and migration are reversible and PostgreSQL-compatible.
- API endpoints conform to the established v1 boundary.
- Input/output specifications remain declarative and distinct from execution.
- Yield/loss, capacity, duration, quality, regulatory, and cost metadata are validated without inventing physical or economic execution semantics.
- Capability/Location references are tenant-safe.
- Least-privilege authorization is enforced.
- Idempotency and optimistic concurrency are executable and tested.
- Transactional outbox events are atomic with canonical mutations.
- Failure and rollback behavior is tested.
- SQLite and PostgreSQL CI are green.
- Documentation and conformance evidence match the proven implementation.
- Branch, commit, PR, and CI results are identifiable.

## 14. Execution order

1. Commit this plan first.
2. Audit current Phase 1/2A/2B code, migrations, tests, and API patterns before implementation.
3. Implement the smallest complete Transformation domain/persistence boundary.
4. Add schemas and API behavior.
5. Add domain/API/security/failure-path tests.
6. Add PostgreSQL-specific conformance evidence where SQLite is insufficient.
7. Run formatting, linting, type checking, migrations, and the complete test suite.
8. Diagnose and fix every CI failure; do not weaken tests or requirements to obtain green CI.
9. Synchronize documentation/conformance evidence only after executable behavior is proven.
10. Open the PR only after both CI jobs are green.
