# Phase 2C Transformation Foundation Plan

**Status:** Planned
**Base:** Phase 2B Capability foundation merged to `main`
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Branch:** `phase2c/transformation-foundation`

## Objective

Implement the canonical Transformation boundary defined by the CRR domain model and Phase 2 plan. A Transformation is a reusable, versioned definition of a permitted input/output relationship. It is not a physical execution record and does not prove that a transformation occurred.

## Included

- Canonical Transformation domain object and invariants.
- Reversible SQLAlchemy/Alembic persistence and PostgreSQL compatibility.
- Input and output state specifications.
- Yield bounds and explicit loss/residual metadata without executing material accounting.
- Positive duration semantics.
- Exact-decimal capacity with unit-registry validation.
- Cost metadata, quality effects, and regulatory requirements as declarative metadata only.
- Eligible Capability and Location references with same-tenant ownership validation.
- Lifecycle, attribution, provenance, timestamps, and optimistic versioning.
- Least-privilege `transformations:read` / `transformations:write` authorization and tenant isolation.
- `GET /v1/transformations`, `POST /v1/transformations`, `GET /v1/transformations/{id}`, `PATCH /v1/transformations/{id}`.
- Required idempotency, optimistic concurrency, and transactional immutable outbox events.
- Domain, persistence, API, authorization, tenant-isolation, failure-path, rollback, migration, and PostgreSQL conformance tests.
- Documentation/conformance synchronization after executable behavior is proven.

## Explicit exclusions

- Transformation execution or ResourceState mutation.
- Route computation, graph search, optimization, or allocation.
- Jev/LLM decision support.
- Commercial offers, agreements, transactions, or settlement.
- Physical execution records.
- Evidence verification.
- Autonomous actions or new graph infrastructure.

## Normative invariants

- Transformation remains distinct from ResourceState, Demand, Capability, and Execution.
- A Transformation definition is not execution proof and cannot mutate physical canonical state.
- All authoritative quantities are exact decimal values; float/non-string API input is rejected.
- Yield values are bounded to `[0,1]` and satisfy `min <= target <= max`.
- Capacity is validated against the configured unit registry.
- Duration is positive.
- Referenced Capability and Location objects must belong to the authenticated organization.
- Cross-tenant reads do not disclose existence.
- Lifecycle transitions are explicit and versioned; terminal states are not silently reactivated.
- Mutation requires `Idempotency-Key`; update requires `If-Match`.
- Canonical mutation and outbox event creation commit atomically.

## Persistence

Add a dedicated `transformations` table and reversible Alembic migration after Capability migration `c4a1b2c3d4e5`. Reuse `ExactDecimal` and `AwareDateTime`. Register the ORM model in `migrations/env.py` so PostgreSQL model/migration alignment remains executable.

## API semantics

Use the established v1 response envelope, machine-readable errors, pagination, ETags, authentication, least-privilege scopes, tenant filtering, idempotency replay, conflict detection, and optimistic concurrency behavior used by Demand and Capability.

## Test strategy

Cover domain invariants, lifecycle, exact decimal/unit validation, invalid yield/duration, reference ownership, CRUD/serialization, authorization, tenant isolation, idempotency replay/conflict, stale writes, outbox behavior, rollback/failure paths, migration lifecycle, SQLAlchemy alignment, PostgreSQL behavior, and regressions for Phase 1/2A/2B.

## Execution order

1. Commit this plan first.
2. Audit the current Phase 1/2A/2B code, migrations, tests, and API patterns.
3. Implement the smallest complete Transformation domain/persistence boundary.
4. Add schemas and API behavior.
5. Add comprehensive tests.
6. Run formatting, linting, type checking, migrations, and the complete suite.
7. Diagnose and fix every CI failure; never weaken requirements or tests to obtain green CI.
8. Synchronize documentation/conformance evidence only after executable behavior is proven.
9. Keep iterating on the branch until both standard and PostgreSQL CI jobs are green.