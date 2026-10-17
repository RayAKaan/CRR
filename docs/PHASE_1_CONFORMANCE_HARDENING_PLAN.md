# Phase 1 Conformance Hardening Plan

**Status:** Planned before implementation
**Base:** `main` after Phase 1 verification-hardening merge
**Scope:** Close the remaining Phase 1 verification gap without entering Phase 2.

## Objective

Raise Phase 1 from CI-green verification to a stronger conformance baseline by proving that the migration lifecycle is reversible/rebuildable and that the authoritative history protections exercised by the implementation are continuously tested.

## Why this is the next part

Phase 1 already has the foundation objects, exact quantity boundary, tenant authorization, explicit ResourceState transitions, optimistic concurrency, idempotency, transactional outbox, append-only history protection, and PostgreSQL CI. The remaining gap is verification depth: the migration job currently proves upgrade and model alignment, but not downgrade/re-upgrade compatibility; the migration test similarly does not prove a complete lifecycle round trip.

The next increment therefore strengthens verification rather than adding later-phase domain objects or routing behavior.

## Implementation plan

### 1. Migration lifecycle verification

- Extend PostgreSQL CI to execute `alembic downgrade base`.
- Re-run `alembic upgrade head` from an empty schema.
- Run `alembic check` after the round trip.
- Keep PostgreSQL 16 as the authoritative migration dialect in CI.

### 2. SQLite migration lifecycle test

- Extend the existing migration test to downgrade to `base`.
- Verify the Phase 1 tables are removed.
- Upgrade back to `head`.
- Re-run `alembic check`.
- Re-verify immutable-history protections after the rebuilt schema is populated.

### 3. History protection verification

- Continue testing ResourceState, StateTransition, and OutboxEvent immutability at the database layer.
- Ensure tests exercise the migration-created protections rather than only ORM behavior.

### 4. Documentation synchronization

- Record the migration round-trip requirement in the Phase 1 plan.
- Keep the conformance matrix aligned with the actual evidence level.
- Do not mark Phase 1 fully complete merely because a single CI run is green; the documented remaining invariant/concurrency gaps must still be evaluated separately.

## Explicit non-goals

This increment MUST NOT introduce:

- routing;
- optimization;
- Jev decision authority;
- demand/capability/transformation implementation;
- commercial lifecycle;
- execution;
- evidence verification;
- graph infrastructure;
- microservices or brokers.

## Acceptance criteria

1. Ruff passes.
2. Formatting passes.
3. Mypy passes for the configured Phase 1 typed surface.
4. Full pytest suite passes.
5. SQLite migration upgrade/downgrade/re-upgrade passes.
6. PostgreSQL 16 migration upgrade/downgrade/re-upgrade passes.
7. `alembic check` passes after the rebuilt schema.
8. Database-level append-only history protections remain enforced.
9. No Phase 1 API or domain semantics regress.
10. GitHub Actions is green on the final commit before the PR is considered ready.
