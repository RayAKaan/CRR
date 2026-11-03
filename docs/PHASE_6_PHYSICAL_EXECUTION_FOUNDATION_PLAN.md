# Phase 6 — Physical Execution Foundation

**Status:** COMPLETE — PRs #31–#35 merged; post-merge CI green  
**Scope:** PRs #32–#35 (following planning PR #31)  
**Predecessor:** Phase 5 Transaction Foundation (PR #30 must pass all required CI and merge before Phase 6 implementation is merged)  
**Implementation base:** merged Phase 5 Transaction Foundation.

## Objective

Introduce the canonical Execution aggregate that records the operational work performed under a scheduled commercial Transaction. Execution must distinguish planned operations from actual observations, preserve an append-only operational history, and require attributable human authorization for material actions.

Execution is not evidence verification. A recorded event means an actor or integrated system reported an operational fact; it does not prove that fact is independently verified. Evidence submission, evidence review, verification decisions, verified ResourceState changes, and network learning are later phases.

## Normative boundaries

1. An Execution belongs to exactly one tenant and one Transaction. Its commercial parties, Agreement, Resource, ResourceState snapshot, quantity, unit, route and accepted terms are derived from and traceable to the Transaction; clients cannot substitute them.
2. Only an eligible, non-cancelled Transaction in an allowed scheduled state can create an Execution. Creation is idempotent and one-to-one for the initial reference implementation.
3. Creating an Execution does not mutate ResourceState, Reservation, ownership, custody, availability, or verified quantity.
4. Planned milestones, reported actual events, submitted evidence and verified outcomes are distinct concepts and must never be collapsed into one status or timestamp.
5. Operational history is append-only. Corrections are compensating/superseding records with actor, reason, time and references; prior events are not overwritten or deleted.
6. Every material operation is attributable to an authorized actor and tenant, uses timezone-aware timestamps, and records relevant location, quantity/unit and provenance when applicable.
7. Quantities use exact decimal arithmetic and canonical units. Actual quantities must be positive, unit-compatible and bounded by domain rules; partial, split and excess quantities must be represented explicitly rather than silently coerced.
8. The execution workflow supports pickup, shipment, receipt, processing, output, delivery and acceptance as distinct operation types. The implementation must not assume every Transaction uses every operation type.
9. Out-of-order, duplicate, stale, unauthorized, impossible and conflicting operations are rejected deterministically or represented as explicit exceptions; they must not silently advance the workflow.
10. Execution lifecycle changes use optimistic concurrency, idempotency and transactional outbox publication.
11. Material physical/commercial actions require explicit human authorization in this phase. No autonomous dispatch, custody transfer, payment, regulatory attestation or external side effect is permitted.
12. Execution records actual operations only. It does not establish independent verification, legal title transfer, payment settlement, completion of a transformation, or verified outcomes.

## Domain model

The phase introduces:

- **Execution** — tenant-scoped operational aggregate linked to one Transaction.
- **ExecutionOperation** — immutable, typed planned or actual operational milestone, with explicit distinction between plan and reported fact.
- **ExecutionException** — attributable record of a blocked, disputed, failed or materially deviating operation and its resolution history.
- **ExecutionEvent / outbox event** — durable domain event emitted atomically with canonical writes.

The exact schema and state transitions must be validated against the existing Transaction, Reservation, ResourceState, authorization and outbox models before implementation. Avoid duplicating commercial snapshots that are already authoritative on Transaction; reference immutable transaction provenance and snapshot only execution-specific operational commitments.

## Lifecycle and operation semantics

Execution creation is allowed only from a scheduled Transaction and begins in a non-executed planned state. The aggregate lifecycle must represent at least:

- PLANNED
- IN_PROGRESS
- EXCEPTION
- CLOSED (operational record closed; not equivalent to verified or accepted outcome)
- CANCELLED (only under explicitly defined pre-execution conditions)

Operations are typed independently of aggregate status:

- PICKUP
- SHIPMENT
- RECEIPT
- PROCESSING
- OUTPUT
- DELIVERY
- ACCEPTANCE

A valid operation sequence is transaction-specific and may omit irrelevant operation types. The domain must enforce declared dependencies and permitted transitions without imposing a universal linear chain. A reported ACCEPTANCE event is still an unverified claim until the later evidence and verification phases authorize and record a verification decision.

## PR plan

| PR | Scope | Acceptance |
|---|---|---|
| #32 | Execution domain contract, SQLAlchemy persistence, tenant-safe Transaction linkage and migration | Domain invariants, exact decimals, immutable operation history, migration upgrade/downgrade/rebuild |
| #33 | Execution operation state machine, scheduling/actual separation, exceptions and human authorization boundary | Deterministic transition matrix, duplicate/out-of-order/stale/unauthorized rejection, correction provenance |
| #34 | Tenant-isolated Execution API, idempotency, ETags, pagination/detail, transactional outbox | API contract, scope enforcement, retry/concurrency behavior, event atomicity |
| #35 | End-to-end integration, conformance and documentation closure | Transaction-to-Execution integration, PostgreSQL conformance, regression suite, all CI gates green |

## API contract targets

- `POST /v1/executions` — create an Execution from an eligible scheduled Transaction.
- `GET /v1/executions` — tenant-scoped list with bounded pagination and filters.
- `GET /v1/executions/{id}` — tenant-scoped aggregate and operation history.
- `POST /v1/executions/{id}/operations/planned` and `/reported` — append a planned milestone or a linked actual report using distinct schemas and permissions.
- `POST /v1/executions/{id}/exceptions` — record an operational exception.
- `POST /v1/executions/{id}/corrections` — append a correction/superseding record; never mutate the original event.
- `POST /v1/executions/{id}/lifecycle` — close an operational record or cancel it before any actual operation is reported.

Final route shapes, request schemas and scopes must be reconciled with the existing API conventions before code is written. Mutations require idempotency keys and version preconditions. Reads and writes must enforce tenant boundaries.

## Required acceptance gates

- Ruff lint and formatting.
- Mypy.
- Full pytest regression suite.
- Alembic upgrade, downgrade and rebuild.
- Alembic model alignment.
- PostgreSQL migration and conformance checks.
- Domain transition matrix and property/invariant tests.
- Tenant isolation and authorization tests.
- Idempotency, optimistic concurrency and outbox atomicity tests.
- Transaction-to-Execution integration tests.
- Tests proving execution creation and operational reporting do not mutate canonical ResourceState or claim verification.
- Documentation/API contract consistency.

## Explicitly deferred

- Evidence file/object storage, evidence submission and review.
- Independent verification, verifier roles, verification decisions and dispute adjudication over evidence.
- Verified ResourceState transitions and custody/title transfer.
- Payment settlement, invoicing and financial rails.
- Autonomous dispatch, carrier integrations or external physical side effects.
- Network learning based on verified outcomes.

These require later, separately scoped phases. Phase 6 must leave explicit extension points but must not implement them prematurely.

## Completion definition

Phase 6 completion verified on 2026-11-03:

- Planning PR #31 and implementation PRs #32–#35 are merged to `main`.
- PR #35 merge commit: `e936e0802fb0bc4b01733349265627a39062995b`.
- Post-merge main CI run `41611210190` passed both `test` and `postgres` jobs.
- PR #35 branch CI passed both jobs; pytest reported 224 passed and 1 PostgreSQL-only test skipped in the SQLite test job. PostgreSQL conformance ran in the separate PostgreSQL job and passed.
- Migration upgrade/downgrade/rebuild and model-alignment checks are included in the passing PostgreSQL job.
- Execution lifecycle closure/cancellation, append-only corrections, exceptions, idempotency, tenant isolation, stale-version checks and unchanged ResourceState behavior are covered by domain/API tests.

Phase 6 is complete within the explicitly stated scope. Reported operations remain actor-attributed operational claims, not independently verified evidence. Evidence review, verification decisions, verified ResourceState transitions, custody/title transfer, payment settlement, carrier integrations and autonomous dispatch remain deferred to later phases.
