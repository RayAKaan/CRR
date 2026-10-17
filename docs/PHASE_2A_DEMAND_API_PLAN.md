# Phase 2A Demand API Increment Plan

**Status:** Implementation in progress
**Base:** Phase 2A Demand foundation merged to `main`
**Scope:** Complete the documented Demand API boundary without introducing routing or execution semantics.

## Objective

Expose the existing canonical Demand domain and persistence model through the v1 API while preserving the guarantees already established by Phase 1 and the Phase 2 plan: tenant isolation, least-privilege authorization, exact quantities, validated lifecycle transitions, idempotency, optimistic concurrency, attribution, provenance, transactional outbox behavior, and PostgreSQL compatibility.

## Implementation order

1. Audit the existing API authentication, scope, idempotency, outbox, error-envelope, pagination, and concurrency helpers.
2. Add only the Demand-specific API adapter required to reuse those established semantics; do not duplicate authentication or persistence policy.
3. Implement `GET /v1/demands` with tenant-scoped pagination and documented filters that are already representable by the Demand model.
4. Implement `POST /v1/demands` with exact-decimal input validation, unit-registry validation, provenance, creator attribution, required idempotency, and atomic outbox creation.
5. Implement `GET /v1/demands/{id}` with cross-tenant non-disclosure.
6. Implement `PATCH /v1/demands/{id}` with `If-Match`, validated lifecycle transitions, immutable identity/ownership, exact quantity/unit validation, and atomic outbox creation.
7. Ensure repeated equivalent idempotent mutations return the existing logical effect without emitting duplicate events; reused keys with different payloads return conflict.
8. Add API, security, failure, rollback, idempotency, concurrency, and PostgreSQL tests.
9. Audit the Demand schemas/domain model for any API-boundary validation gap exposed by the implementation, especially patch cross-field quantity/timing invariants and unit compatibility.
10. Synchronize affected conformance evidence only after executable behavior is proven.
11. Run formatting, linting, type checking, full pytest, migration lifecycle, model alignment, and PostgreSQL conformance; fix every failure before opening/completing the PR.

## Explicit non-goals

- Capability
- Transformation
- Routing or optimization
- Jev/LLM decision support
- Commercial execution
- Physical execution
- Evidence verification
- New infrastructure unrelated to Demand

## Acceptance criteria

- All four documented Demand endpoints are implemented.
- Protected data is tenant-isolated and requires the correct Demand scope.
- Invalid credentials/scopes are rejected before protected disclosure.
- Creation and mutation require valid idempotency keys.
- Same key + same request is idempotent; same key + different request conflicts.
- Mutable changes require a matching `If-Match` version.
- Illegal lifecycle transitions are rejected.
- Exact decimal and unit-registry rules remain authoritative.
- Demand mutations and outbox events commit atomically.
- Persistence failures roll back both the Demand mutation and event/idempotency records.
- SQLite and PostgreSQL tests are green.
- CI is green before the increment is considered complete.
