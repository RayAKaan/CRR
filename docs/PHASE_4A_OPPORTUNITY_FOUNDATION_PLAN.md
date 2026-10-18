# CRR Phase 4A — Opportunity Foundation Plan

**Status:** Complete  
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2  
**Base:** Phase 3G bounded decision-support foundation merged to `main`

## Objective

Establish the first explicit commercial-conversion boundary: a tenant-isolated, auditable Opportunity that can be created only from a feasible, non-stale, deterministically evaluated route result.

Opportunity is commercial intent, not an Offer, Agreement, Transaction, Reservation, execution record, or evidence of physical completion.

## Scope delivered

- Immutable-at-creation route provenance, source/demand versions, candidate-set fingerprint, advisory/economic provenance, exact quantity/unit, validity window, lifecycle, attribution, and version.
- Explicit lifecycle: `DRAFT → OPEN → EXPIRED/CANCELLED/CLOSED`; invalid transitions fail deterministically.
- Eligibility gate: same tenant, feasible route, no hard rejections, candidate fingerprint match, current source/demand versions, active Demand, bounded validity window, canonical unit validation, and no inline authoritative physical/economic facts.
- `POST /v1/opportunities`, `GET /v1/opportunities`, `GET /v1/opportunities/{id}`, and ETag/idempotency-protected lifecycle mutation.
- Canonical persistence, reversible migration, transactional outbox, idempotency, optimistic concurrency, and PostgreSQL/SQLite alignment.
- Tenant isolation and least-privilege scopes `opportunities:read` and `opportunities:write`.
- EconomicModel identity/version/currency consistency when an economic model is attached.

## Explicit non-goals

Offers, agreements, transactions, reservations, execution, evidence verification, autonomous acceptance, Jev/LLM decisions, external pricing/geographic providers, candidate rediscovery, canonical physical-state mutation, or new infrastructure.

## Domain invariants

1. Every Opportunity belongs to exactly one organization.
2. Cross-tenant reads and writes are isolated.
3. Only a feasible source route can be converted.
4. The route candidate fingerprint must match the supplied candidate provenance.
5. Source ResourceState and Demand versions must still match the route result.
6. Demand must remain active and the Opportunity validity window must remain within Demand timing.
7. Quantity/unit snapshots use exact decimal semantics and the canonical unit registry.
8. Monetary context is explicit and versioned when present.
9. Lifecycle transitions are explicit and optimistic-concurrency protected.
10. Create and lifecycle mutation are idempotent; key reuse with another payload is a conflict.
11. Creation emits a transactional outbox event with attribution and provenance.
12. Opportunity creation never mutates ResourceState, Demand, Capability, Transformation, Location, or EconomicModel canonical truth.
13. Opportunity is never evidence of physical execution or settlement.

## Testing and evidence

Implemented coverage includes:

- Opportunity domain lifecycle/version invariants;
- valid create/get/idempotent replay;
- least-privilege scope rejection;
- candidate fingerprint tampering rejection;
- stale source-version rejection;
- ETag lifecycle transition and illegal-transition rejection;
- cross-tenant retrieval isolation;
- transactional outbox creation event;
- exact-decimal and canonical unit validation through the API schema/domain boundary;
- full existing routing, economics, optimization, decision-support, and migration regression suite.

The final green GitHub Actions run is `39147684686` on branch head `5dabf9f19d7d6a0fd56f0e157cccd63f033d74b5`.

Test job:

- Ruff check: PASS
- Ruff format: PASS
- mypy: PASS
- pytest: PASS — 153 passed, 1 skipped (PostgreSQL-only test in the standard job)

PostgreSQL job:

- migration upgrade: PASS
- migration downgrade: PASS
- database rebuild: PASS
- SQLAlchemy/model alignment: PASS
- PostgreSQL conformance: PASS

An earlier green-gate failure was not ignored: the migration alignment check exposed missing SQLAlchemy indexes, and the model was corrected to declare the same indexes as the migration. The subsequent full run passed without weakening tests or CI requirements.

## Documentation audit

The following normative documents were audited against the delivered implementation:

- `docs/CRR_API_CONTRACT.md`
- `docs/CRR_DECISION_AND_ROUTING_SPEC.md`
- `docs/CRR_DOMAIN_MODEL.md`
- `docs/CRR_VALIDATION_AND_INVARIANTS.md`
- `docs/CRR_CONFORMANCE_MATRIX.md`
- `docs/CRR_DATA_FLOW_ARCHITECTURE.md`
- `docs/CRR_SPECIFICATION_INDEX.md`
- `docs/CRR_NORMATIVE_AMENDMENT_0.1.1.md`
- `docs/CRR_NORMATIVE_AMENDMENT_0.1.2.md`

The existing normative model already defines the commercial chain `Opportunity → Offer → Agreement → Transaction` and separates commercial intent from execution and verification. Phase 4A adds the first executable Opportunity boundary without redefining those downstream objects or violating the existing physical/canonical/derived separation. No conflicting normative rule was introduced.

## Database boundary

Opportunity is durable commercial-intent state and therefore has canonical persistence and migration `f7a8b9c0d1e2`. The migration is reversible and is verified against SQLite and PostgreSQL. SQLAlchemy metadata now declares the same status and demand indexes as the migration.

No Offer, Agreement, Transaction, Reservation, or Execution tables were introduced.

## Definition of done

- Plan committed before implementation — **complete**.
- Domain contract and lifecycle — **complete**.
- Source route feasibility/freshness gate — **complete**.
- Tenant isolation and least privilege — **complete**.
- Exact quantity/unit and explicit monetary semantics — **complete**.
- Idempotency, optimistic concurrency, attribution, provenance, transactional outbox — **complete**.
- Reversible SQLite/PostgreSQL migration and SQLAlchemy alignment — **complete**.
- Canonical-reference-based API and inline-authority rejection — **complete**.
- Domain/API/security/failure/regression tests — **complete**.
- Ruff, format, mypy, pytest, migration lifecycle, SQLAlchemy alignment, PostgreSQL conformance, and GitHub CI — **complete and green**.
- Normative documentation audit — **complete**.
- PR opened for review; merge remains with repository owner.

## Closure evidence

- Branch: `phase4a/opportunity-foundation`
- PR: #19
- Final implementation head: `5dabf9f19d7d6a0fd56f0e157cccd63f033d74b5`
- Final fully green CI run: `39147684686`
- PR remains open and is not auto-merged.
