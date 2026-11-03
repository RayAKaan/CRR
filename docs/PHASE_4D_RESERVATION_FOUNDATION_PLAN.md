# CRR Phase 4D — Reservation Foundation

**Status:** Implementation complete; final CI validation  
**Base:** Phase 4C Agreement Foundation on `main`

## Objective

Introduce a tenant-scoped, auditable reservation that places a temporary hold on an exact quantity of an immutable ResourceState under an active Agreement. A reservation is an allocation record only: it does not mutate ResourceState, transfer ownership/custody, create a Transaction, or prove physical execution.

## Normative decisions

1. Every reservation references one active Agreement, one Resource identity, and one immutable ResourceState version.
2. The reserved quantity must be positive, exact, and use the exact canonical unit and unit-registry version of both the Agreement quantity and ResourceState quantity. No implicit conversion or rounding is permitted.
3. The reserved quantity cannot exceed the Agreement's accepted quantity.
4. The sum of active, unexpired reservations against a ResourceState plus a new reservation cannot exceed that state's quantity.
5. Released and expired reservations do not consume available allocation.
6. Reservation expiry is explicit and timezone-aware. Expiry never changes physical state.
7. All mutations are tenant-isolated, actor-attributed, idempotent, versioned, and concurrency-protected.
8. The Resource row is the serialization lock for allocations against any state of that Resource. PostgreSQL uses row-level locking; SQLite remains a test/development backend and must not be represented as providing equivalent concurrent-writer guarantees.
9. Reservation lifecycle is distinct from Agreement and ResourceState lifecycle.
10. Reservation does not imply dispatch, custody transfer, delivery, payment, or execution.

## Planned PR sequence

- PR #25 — Reservation domain contract, exact allocation invariants, SQLAlchemy persistence, reversible migration, and domain/migration tests.
- PR #26 — Reservation lifecycle, expiry/release semantics, capacity accounting, locking strategy, and concurrency/domain tests.
- PR #27 — Tenant-isolated Reservation API, Agreement/ResourceState validation, idempotency, ETags, transactional outbox, and end-to-end integration/conformance tests.

## Definition of done

- Only active Agreements can be reserved against.
- ResourceState is read-only and reservations never mutate its quantity or history.
- Exact decimal and unit semantics are preserved end-to-end.
- Over-allocation and stale ResourceState references are rejected.
- Active allocation is calculated from canonical reservation rows, not cached counters.
- Concurrent allocation is serialized on the owning Resource row and tested against PostgreSQL.
- Release and expiry are explicit, idempotent lifecycle transitions.
- Cross-tenant references and reads are rejected.
- Events are written transactionally with reservation mutations.
- SQLite and PostgreSQL migration upgrade/downgrade/rebuild and model alignment pass.
- Ruff, formatting, mypy, pytest, and PostgreSQL CI pass without weakening tests.
- Documentation describes only implemented behavior.

## PR 25 — Domain and persistence

This PR establishes the canonical Reservation object and database representation. Lifecycle mutation and HTTP behavior are intentionally deferred to PRs #26 and #27.


## Implementation record

| PR | Scope | State |
|---|---|---|
| #25 | Reservation domain contract, exact capacity validation, tenant-matched persistence and migration | Merged |
| #26 | Release/expiry lifecycle and active allocation accounting | Merged |
| #27 | Tenant-isolated API, transactional outbox, idempotency, ETags and integration coverage | Open; CI validation |

## PR 27 API contract

- `POST /v1/reservations` creates an exact-quantity hold under an active Agreement.
- `GET /v1/reservations` and `GET /v1/reservations/{id}` return tenant-scoped records.
- `PATCH /v1/reservations/{id}` supports participant release and separately scoped expiry.
- Reservation creation locks the owning Resource row in PostgreSQL, then re-reads active allocations before inserting.
- The same Resource lock is used by ResourceState transition handling. A ResourceState with active unexpired reservations cannot be physically transitioned until those holds are released or expire.
- Allocation is bounded both by the source ResourceState quantity and by the cumulative active quantity under the Agreement.


## Final acceptance record

The implementation is complete pending final PR #27 merge. PR #25 merged as `4ae35f48de56375b872b517adc3cc23cf5e27d66`; PR #26 merged as `d3ad738083c6f193fbe9954eb8f85d25b66863cd`. PR #27's CI run `41587457987` passed all required checks: Ruff, formatting, mypy, pytest, PostgreSQL migration upgrade/downgrade/rebuild, Alembic model alignment, and PostgreSQL conformance.

The implemented boundary provides a complete allocation hold and release/expiry API. It does not create a Transaction, mutate physical inventory, or prove physical execution. Phase 5 Transaction Foundation is the next increment.
