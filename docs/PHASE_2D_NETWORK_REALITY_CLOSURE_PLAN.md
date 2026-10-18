# Phase 2D Network-Reality Conformance Closure Plan

**Status:** Planned
**Base:** Phase 2C Transformation foundation merged to `main`
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2
**Branch:** `phase2d/network-reality-closure-v2`

## 1. Objective

Close Phase 2 conformance across Demand, Capability, and Transformation. This is an audit-and-hardening boundary, not a routing implementation.

The objective is to prove that the three canonical network-reality objects coexist without collapsing physical state, requirements, operational ability, or reusable process definitions into one another.

## 2. Scope

### Included

- Re-audit the actual Phase 1, Phase 2A, Phase 2B, and Phase 2C implementations against the canonical protocol documents.
- Verify cross-object reference integrity and same-tenant ownership for references that are authoritative at the current boundary.
- Verify lifecycle eligibility semantics for Demand, Capability, and Transformation.
- Verify exact-decimal and unit-registry behavior across all three boundaries, including zero, negative, malformed, float, scientific notation, and excessive-precision inputs where the canonical quantity contract applies.
- Verify temporal invariants and timezone-aware API/persistence behavior.
- Verify idempotency, optimistic concurrency, tenant isolation, authorization, attribution, provenance, and transactional outbox behavior across all three APIs.
- Verify migration-chain reversibility, rebuildability, PostgreSQL model/migration alignment, and PostgreSQL-specific behavior after the complete Phase 2 schema is present.
- Verify that Demand, Capability, and Transformation mutations cannot mutate Resource or ResourceState physical truth.
- Add regression/conformance evidence for Phase 1 and Phase 2A/2B/2C behavior.
- Synchronize the conformance matrix and Phase 2 status only after executable evidence is green.

### Explicitly excluded

- Route computation or graph search.
- Optimization or allocation.
- Jev/LLM decision authority.
- Commercial offers, agreements, transactions, settlement, or execution.
- Evidence verification.
- Autonomous actions.
- Graph database infrastructure.
- New physical execution semantics.

## 3. Canonical semantic boundary

```text
ResourceState = authoritative physical state
Demand        = requirement / acceptance condition
Capability    = declared operational ability
Transformation= reusable input/output process definition
```

None of Demand, Capability, or Transformation is physical execution proof. None may directly mutate Resource or ResourceState merely by being created, updated, or transitioned.

## 4. Audit matrix

| Area | Demand | Capability | Transformation |
|---|---|---|---|
| Stable identity | ✓ | ✓ | ✓ |
| Organization ownership | ✓ | ✓ | ✓ |
| Exact decimal quantities | ✓ | ✓ | ✓ |
| Unit registry | ✓ | ✓ | ✓ |
| Zero/negative semantics | ✓ | ✓ | ✓ |
| Temporal validity | ✓ | ✓ | ✓ |
| Lifecycle transitions | ✓ | ✓ | ✓ |
| Tenant isolation | ✓ | ✓ | ✓ |
| Least-privilege scopes | ✓ | ✓ | ✓ |
| Provenance | ✓ | ✓ | ✓ |
| Attribution | ✓ | ✓ | ✓ |
| Idempotency | ✓ | ✓ | ✓ |
| Optimistic concurrency | ✓ | ✓ | ✓ |
| Transactional outbox | ✓ | ✓ | ✓ |
| Failure/rollback | ✓ | ✓ | ✓ |
| PostgreSQL behavior | ✓ | ✓ | ✓ |
| Migration reversibility | ✓ | ✓ | ✓ |
| Cross-object reference ownership | ✓ | ✓ | ✓ |
| No physical-state mutation | ✓ | ✓ | ✓ |

## 5. Reference rules

- Every authoritative object must be owned by the authenticated organization.
- Transformation references to Capability and Location must not cross the organization boundary.
- Missing or unauthorized references must not disclose another tenant's existence.
- Reference lists must reject duplicates where uniqueness is semantically required.
- Capability transformation identifiers remain declarative references; they are not execution proof.
- Demand remains a requirement and cannot be treated as inventory.
- Capability remains a declaration of ability and cannot create available physical capacity by itself.
- Transformation remains a reusable definition and cannot create ResourceState or execution records.

## 6. Validation hardening

The closure test matrix must explicitly exercise:

- missing required values;
- invalid status values and illegal transitions;
- negative quantities/capacity/yield;
- zero semantics according to Amendment 0.1.2;
- non-string authoritative decimal input;
- binary float input;
- scientific notation where prohibited by the exact-decimal contract;
- malformed and excessive-precision values;
- unknown and incompatible units;
- invalid quantity relationships;
- invalid timezones and inverted windows;
- invalid duration and yield bounds;
- invalid remaining-demand quantity;
- missing provenance;
- unauthorized and revoked credentials;
- cross-tenant reads, writes, and reference injection;
- stale writes;
- duplicate idempotency replay;
- idempotency-key reuse with a materially different request;
- persistence/outbox failure rollback;
- database integrity failures.

## 7. Database and migration closure

Verify the complete Alembic chain in PostgreSQL:

```text
upgrade head
→ downgrade to Phase 1 foundation
→ upgrade head
→ alembic check / model alignment
```

SQLite remains useful for broad behavioral tests, but PostgreSQL is authoritative for dialect-specific migration, transaction, constraint, and concurrency evidence.

## 8. API closure

Verify all Phase 2 canonical endpoints:

- `GET/POST/PATCH /v1/demands`
- `GET/POST/PATCH /v1/capabilities`
- `GET/POST/PATCH /v1/transformations`

Verify common guarantees:

- authentication before protected disclosure;
- least-privilege read/write scopes;
- tenant-filtered collections and detail reads;
- machine-readable validation/conflict errors;
- required `Idempotency-Key` on mutations;
- required `If-Match` on mutable updates;
- ETags derived from object versions;
- deterministic idempotency replay;
- stale-write rejection;
- transactional event emission only on committed mutations.

## 9. Test strategy

Add or strengthen tests rather than weakening existing requirements. Use domain tests for semantic invariants, API tests for externally observable behavior, persistence tests for exact storage/reference behavior, security tests for authorization and tenant boundaries, failure-path tests for rollback, and PostgreSQL tests where SQLite cannot establish the required guarantee.

Run the full repository test suite plus formatting, Ruff, mypy, migration lifecycle, SQLAlchemy alignment, and PostgreSQL conformance.

## 10. Documentation synchronization

After behavior is proven, synchronize:

- `docs/PHASE_2_PLAN.md` status and subphase evidence;
- `docs/CRR_CONFORMANCE_MATRIX.md` executable evidence references;
- affected API/domain/validation/data-flow documentation where implementation behavior is clarified;
- this closure plan with final evidence and exact commit/CI identifiers.

Documentation must not substitute for executable proof.

## 11. Definition of done

Phase 2D is complete only when:

1. Demand, Capability, and Transformation conform to the audited canonical boundary.
2. Cross-object reference and tenant ownership rules are executable and tested.
3. Exact quantity/unit/time/lifecycle semantics are covered.
4. Authorization, idempotency, concurrency, provenance, attribution, and outbox guarantees hold across all three objects.
5. Full migration lifecycle and PostgreSQL conformance are green.
6. Regression tests for Phase 1 and Phase 2A/2B/2C remain green.
7. Documentation and conformance evidence match actual behavior.
8. Final GitHub CI is green on the final commit.
9. A PR records the exact implementation and CI evidence.

## 12. Execution order

1. Commit this plan before implementation.
2. Audit the actual current code, tests, migrations, and CI configuration.
3. Implement only gaps proven by that audit.
4. Add comprehensive conformance and regression tests.
5. Push and run the complete CI matrix.
6. Diagnose every CI failure from actual workflow logs and fix the implementation or tests without weakening requirements.
7. Repeat until both standard and PostgreSQL CI jobs are green.
8. Synchronize documentation after executable proof.
9. Open the PR only after the branch is internally consistent and CI is green.
