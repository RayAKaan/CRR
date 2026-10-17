# CRR Phase 1 Plan — Executable Foundation

**Status:** Implemented; conformance hardening in progress
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2

## Objective

Create the smallest executable reference foundation that safely represents tenant-scoped organizations and actors, locations, resources, and versioned ResourceStates with exact quantities, provenance, and append-preserving, attributable physical transitions.

This phase establishes project tooling and the canonical state foundation. It does not implement route computation or all 18 canonical objects.

## Normative prerequisites resolved

`CRR_NORMATIVE_AMENDMENT_0.1.2.md` permits zero-quantity historical/reconciled states while excluding them from supply routing, and separates ResourceState physical history from lifecycle, availability, execution, and epistemic dimensions. This amendment is authoritative for those ambiguities.

## Planned scope

- Python reference project structure, dependency declaration, local developer commands, and CI.
- Tenant-scoped Organization, Actor, Location, Resource, and ResourceState foundations.
- Exact decimal quantity representation and validated unit representation; no authoritative float path.
- Stable identity, schema/object version, provenance, and attributable state-transition records.
- Persistence and explicit transition operations that preserve prior physical history.
- Optimistic concurrency and idempotent externally triggered transitions.
- API boundaries for foundation objects and ResourceState transitions, consistent with the v1 API contract.
- Behavior tests for quantity/unit validity, history preservation, attribution, tenancy, duplicate requests, and stale versions.

## Out of scope

- Routing, optimization, Jev integration, and economics calculations.
- Commercial lifecycle, execution, evidence verification, and end-to-end transaction proof.
- Graph database, microservices, or marketplace functionality.

## Affected domain objects

Organization, Actor, Location, Resource, ResourceState, and the auditable ResourceState transition/event representation.

## API and persistence impact

Introduce the first versioned API and persistence schema/migration for the in-scope objects. ResourceState material changes must use an explicit transition/correction operation, validate the expected predecessor version, preserve the prior state, and emit an auditable record. A generic patch must not rewrite authoritative physical semantics.

The initial schema preserves append-only ResourceState snapshots and transition records. Phase 1 does not implement generic status or availability state machines.

## Validation and security

- Validate exact non-negative quantities; permit zero for valid historical states; reject negative values, invalid units, and float inputs at canonical boundaries.
- Enforce authentication/authorization and tenant ownership before protected reads or writes.
- Enforce actor attribution, provenance, expected object version, idempotency, and append-only history for transitions.
- Return explicit validation, authorization, conflict, and precondition failures using the documented API envelope.

## Failure modes to cover

- Negative, zero (per resolved rule), malformed, or excessive-precision quantity.
- Unknown or incompatible unit.
- Unauthorized or cross-tenant object access.
- Stale transition against a prior ResourceState version.
- Replayed idempotency key and same key with a different request.
- Failure between canonical mutation and audit/event persistence.
- Attempted generic mutation of material physical fields.

## Migration and compatibility

There is no existing application schema to migrate. Add an initial versioned migration. Keep protocol semantics independent of PostgreSQL; choose the reference database only after confirming the local development/test setup. Any change to the transition representation must preserve existing state and audit history.

The reference implementation exercises both SQLite and PostgreSQL migration paths. PostgreSQL CI now verifies a complete `upgrade → downgrade → upgrade → alembic check` lifecycle. The SQLite migration test verifies the same round trip and confirms that database-level append-only history protections are recreated after the rebuild. CI also runs Ruff, formatting verification, mypy, and pytest.

## Documentation changes

Resolve and amend the normative domain/validation/API documents before implementing the affected quantity and lifecycle rules. Update the conformance matrix if the resolved semantics change its requirements. Re-read affected documents after implementation and remove any discrepancy between plan, API, schema, and behavior.

## Definition of done

- The project and CI checks run locally and in CI.
- In-scope canonical objects have stable IDs, tenant association, versions, and provenance as applicable.
- Quantities are exact decimals; canonical paths reject float representations.
- ResourceState transitions are explicit, attributable, concurrency-checked, idempotent, and history-preserving.
- Cross-tenant access is denied and tested at service/API boundaries.
- Tests cover valid transitions and the failure modes listed above.
- SQLite and PostgreSQL migration lifecycles are reversible and rebuildable.
- Database-level append-only history protections survive migration rebuilds.
- Relevant documentation agrees with externally observable behavior.
- Test/lint/type-check results and the resulting Git commit are identifiable.

## Current implementation status

The Phase 1 implementation is present on `main`. It includes the Python/FastAPI/SQLAlchemy API, exact decimal/versioned unit validation, tenant-scoped creation, detail, collection and history reads, cursor pagination, append-only state transitions, API-key scopes with least-privilege enforcement, idempotency, optimistic concurrency, a transactional outbox, Alembic schema migration, and CI configuration.

The first verification-hardening increment has already established green GitHub Actions for Ruff, formatting, mypy, pytest, PostgreSQL migration upgrade, and Alembic model alignment. The current conformance-hardening increment adds migration round-trip verification in both SQLite tests and PostgreSQL CI. Phase 1 is not declared fully complete until the remaining invariant/concurrency/failure-mode evidence and final specification audit are completed.
