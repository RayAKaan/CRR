# CRR Phase 4A — Opportunity Foundation Plan

**Status:** In Progress  
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2  
**Base:** Phase 3G bounded decision-support foundation merged to `main`

## Objective

Establish the first explicit commercial-conversion boundary: a tenant-isolated, auditable Opportunity that can be created only from a feasible, non-stale, deterministically evaluated route result.

Opportunity is commercial intent, not an Offer, Agreement, Transaction, Reservation, execution record, or evidence of physical completion.

## Scope

- Immutable-at-creation route provenance, source/demand versions, candidate-set fingerprint, advisory/economic provenance, exact quantity/unit, validity window, lifecycle, attribution, and version.
- Explicit lifecycle: `DRAFT → OPEN → EXPIRED/CANCELLED/CLOSED`; invalid transitions fail deterministically.
- Eligibility gate: same tenant, feasible route, no hard rejections, candidate fingerprint match, current source/demand versions, active Demand, bounded validity window, canonical unit validation, and no inline authoritative physical/economic facts.
- `POST /v1/opportunities`, `GET /v1/opportunities`, `GET /v1/opportunities/{id}`, and ETag/idempotency-protected lifecycle mutation.
- Canonical persistence, reversible migration, transactional outbox, idempotency, optimistic concurrency, and PostgreSQL/SQLite alignment.

## Explicit non-goals

Offers, agreements, transactions, reservations, execution, evidence verification, autonomous acceptance, Jev/LLM decisions, external pricing/geographic providers, candidate rediscovery, canonical physical-state mutation, or new infrastructure.

## Invariants and tests

Tenant isolation, exact decimals, timezone-aware windows, route freshness, fingerprint integrity, Demand eligibility, economic-model consistency, idempotent replay/conflict, ETag concurrency, illegal transitions, rollback/outbox coupling, least privilege, malformed authority rejection, canonical source immutability, migration lifecycle, SQLAlchemy alignment, and PostgreSQL conformance are mandatory.

## Execution order

1. Plan first — complete.
2. Audit Phase 3D–3G and normative commercial-conversion semantics — complete.
3. Implement domain/persistence/migration/API/outbox/concurrency — in progress.
4. Add comprehensive domain/API/security/failure/conformance tests — in progress.
5. Run Ruff, format, mypy, pytest, migration lifecycle, SQLAlchemy alignment, PostgreSQL conformance, and all GitHub checks.
6. Diagnose and fix every failure without weakening requirements.
7. Synchronize normative documentation after behavior is proven.
8. Add closure evidence and open PR; do not merge automatically.
