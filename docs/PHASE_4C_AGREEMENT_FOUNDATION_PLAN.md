# CRR Phase 4C — Agreement Foundation

**Status:** Complete — domain contract and lifecycle increments implemented; persistence/API closure pending  
**Base:** Phase 4B Offer Foundation on `main`

## Objective

Create the canonical Agreement boundary: an auditable record of the exact commercial terms accepted from an Offer. Agreement creation must not reserve resources, create a Transaction, mutate ResourceState, initiate payment, or imply physical execution.

## Normative decisions

1. An Agreement may only be created from an Offer in `ACCEPTED` state.
2. The accepting actor must be the Offer recipient.
3. Agreement stores the source Offer ID and version and a canonical immutable-at-creation terms snapshot.
4. The snapshot includes exact quantity, unit registry version, exact price, currency, delivery/timing terms, route assumptions, conditions, and validity window.
5. Agreement lifecycle changes are explicit, versioned, attributed, idempotent, and concurrency-protected.
6. Tenant boundaries and least-privilege authorization apply to all Agreement reads and mutations.
7. Agreement is not a Reservation, Transaction, Execution, Evidence, settlement, or proof of legal enforceability.

## Planned PR sequence

- PR #21 — Agreement domain contract and immutable accepted-terms snapshot.
- PR #22 — Agreement lifecycle, transition rules, expiry/cancellation and domain conformance.
- PR #23 — Tenant-isolated Agreement API, scopes, idempotency, ETags and transactional outbox.
- PR #24 — SQLAlchemy persistence, reversible migration, API/domain integration tests, documentation and full regression closure.

## Definition of done

- Accepted Offer is the only creation source; arbitrary client-supplied commercial terms are never accepted as Agreement truth.
- Recipient acceptance is explicitly attributed and timestamped.
- The accepted terms snapshot is stable and reproducible.
- All lifecycle changes are explicit and versioned.
- Cross-tenant reads/references are rejected.
- Mutations are idempotent and protected by optimistic concurrency.
- Events are written transactionally with canonical state.
- SQLite and PostgreSQL migration upgrade/downgrade/rebuild and model alignment pass.
- Ruff, formatting, mypy, pytest and PostgreSQL CI pass without weakening tests.
- API contract, domain model, conformance matrix and README describe only implemented behavior.

## PR 21 scope

This increment introduces the immutable domain contract and focused domain tests only. Persistence and HTTP behavior are intentionally deferred to subsequent PRs.


## Implementation record

| PR | Scope | State |
|---|---|---|
| #21 | Accepted-Offer Agreement domain contract and immutable terms snapshot | Merged |
| #22 | Explicit Agreement lifecycle and domain tests | Merged |
| #23 | Tenant-scoped persistence and reversible Alembic migration | Merged |
| #24 | Agreement API, idempotency, acceptance provenance, outbox, ETags, integration tests and documentation | Merged |

The Agreement API reads acceptance provenance from the Offer's immutable outbox event at the accepted aggregate version. It does not trust client-supplied acceptance actor/time or commercial terms.

## Final acceptance boundary

Phase 4C is complete. PR #24 was merged as `8f819cac2fb696a26414f5a8820138053d690383` after CI run `41585369305` passed. The run reported 171 passed, 1 expected PostgreSQL-only skip, Ruff, formatting, mypy, PostgreSQL migration upgrade/downgrade/rebuild, Alembic model alignment, and PostgreSQL conformance all successful. The next phases remain Reservation and Transaction; this phase does not claim a complete physical-resource lifecycle or commercial production readiness.
