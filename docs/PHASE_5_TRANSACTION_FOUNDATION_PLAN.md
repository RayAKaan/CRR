# Phase 5 — Transaction Foundation

**Status:** In progress  
**Scope:** PRs #28–#30  
**Predecessor:** Phase 4D Reservation Foundation

## Objective

Create the canonical commercial Transaction that binds one accepted Agreement to the complete set of active Reservations covering its agreed quantity. A Transaction records the commercial commitment and its provenance. It does not claim dispatch, custody transfer, delivery, payment settlement, execution, or verification.

## Required invariants

1. A Transaction belongs to one organization and references an Agreement and Opportunity in that same organization.
2. One Agreement produces at most one Transaction in this reference implementation.
3. The Transaction snapshots the accepted Agreement terms, Offer ID/version, Opportunity ID/version and route candidate; later Offer or Opportunity changes cannot rewrite that snapshot.
4. A Transaction references one or more Reservations. Every linked Reservation must belong to the same Agreement, organization, resource, ResourceState and ResourceState version.
5. The sum of linked Reservation quantities must exactly equal the agreed quantity before a Transaction can be created.
6. All linked Reservations must be active and unexpired at creation.
7. Quantities and prices use exact decimal storage; quantities retain their canonical unit and unit-registry version.
8. The two commercial parties are the parties captured by the Agreement; the creating actor must be one of them.
9. Tenant-scoped composite foreign keys protect Agreement, Opportunity, Resource, ResourceState, actors and Reservation links.
10. Transaction creation and lifecycle events use idempotency and the transactional outbox.
11. A Transaction is a commercial record only. It does not mutate ResourceState or assert physical execution or verified outcomes.

## PR plan

| PR | Scope | State |
|---|---|---|
| #28 | Transaction domain contract, persistence model, Agreement/Opportunity/Resource/Reservation references and migration | Merged |
| #29 | Transaction lifecycle, commercial obligation validation and cross-object lifecycle safeguards | Open; final CI validation |
| #30 | Tenant-isolated Transaction API, idempotency, ETags, outbox and end-to-end integration tests | In progress |

## Lifecycle boundary

A Transaction is created in `AGREED` status only after full Reservation coverage is confirmed. PR #29 will implement the allowed commercial transitions into scheduling, dispute and cancellation states. Execution, completion and verification remain later phases and cannot be asserted by this phase.

## Acceptance gates

- Ruff lint and formatting.
- Mypy.
- Full pytest regression suite.
- Alembic upgrade, downgrade and rebuild.
- Alembic model alignment.
- PostgreSQL migration and conformance checks.
- Transaction domain, persistence, tenant-boundary, allocation coverage, idempotency, lifecycle and API integration tests.


## PR #29 implementation notes

- Adds the `AGREED → SCHEDULED / DISPUTED / CANCELLED` and `SCHEDULED → DISPUTED / CANCELLED` transitions; disputes can be resolved back to `SCHEDULED` with a future schedule and an explicit resolution note.
- Enforces participant attribution, non-empty reasons, timezone-aware transition times, future scheduling, version increments and transition provenance.
- Validates that the active Reservations exactly cover the accepted Agreement quantity and all reference the same tenant, Agreement, Resource, ResourceState and version.
- Prevents Agreement cancellation/expiry/termination while a non-cancelled Transaction exists.
- Prevents independent Reservation release/expiry while a non-cancelled Transaction holds it.
- Transaction cancellation releases its active Reservation set atomically; the Transaction API is wired in PR #30.


## PR #30 implementation notes

- Adds tenant-scoped Transaction create, list and detail endpoints.
- Transaction creation locks the Agreement and source Resource, rechecks idempotency after serialization, and requires the request to include the complete active Reservation set.
- Creation revalidates accepted Offer/Opportunity freshness, current ResourceState version, Agreement validity and exact Reservation quantity coverage.
- Transaction creation snapshots accepted terms, stores all Reservation links and emits an outbox event atomically.
- Lifecycle API requires ETags and idempotency keys. Scheduling, dispute, dispute resolution and cancellation are explicitly validated.
- Cancellation atomically marks all remaining active linked Reservations RELEASED (or EXPIRED when their expiry instant has passed), records Reservation outbox events, and records the Transaction transition in the same database transaction.
- Once an Agreement has a Transaction, additional Reservations are blocked even if that Transaction is later cancelled; a cancelled Agreement cannot be reused to create a second Transaction.


PR #30 also enforces database-level checks for positive quantities/prices/versions, distinct commercial parties, valid lifecycle status and scheduled-state consistency. Reservation links are unique across Transactions. Offer and Opportunity versions are persisted and included in Transaction outbox provenance.
