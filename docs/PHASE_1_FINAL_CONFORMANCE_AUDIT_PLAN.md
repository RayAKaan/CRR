# CRR Phase 1 — Final Conformance Audit Plan

**Status:** Implemented; audit increment verified
**Base:** `main` after Phase 1 conformance-hardening merge
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2

## Objective

Close the remaining verification gap identified by the Phase 1 plan without beginning Phase 2. The purpose of this increment is to prove, rather than assume, that the implemented foundation preserves the Phase 1 invariants across validation, authorization, idempotency, failure handling, persistence, and the documented API boundary.

Phase 1 already contains the foundation implementation and migration lifecycle hardening. This increment is therefore an evidence-and-correction pass: audit the current implementation against the authoritative specifications, add only missing tests or narrowly scoped fixes, and update the conformance record to reflect externally verified behavior.

## Authoritative reading order

1. `docs/CRR_SPECIFICATION_INDEX.md`
2. `docs/CRR_PROTOCOL_SPEC.md`
3. `docs/CRR_DOMAIN_MODEL.md`
4. `docs/CRR_VALIDATION_AND_INVARIANTS.md`
5. `docs/CRR_API_CONTRACT.md`
6. `docs/CRR_DATA_FLOW_ARCHITECTURE.md`
7. `docs/SYSTEM_DESIGN.md`
8. `docs/CRR_NORMATIVE_AMENDMENT_0.1.1.md`
9. `docs/CRR_NORMATIVE_AMENDMENT_0.1.2.md`
10. `docs/CRR_CONFORMANCE_MATRIX.md`
11. `docs/PHASE_1_PLAN.md`

The repository implementation and tests are then treated as the executable source of truth for what is actually proven.

## Audit plan

### 1. Validation boundary

Verify canonical quantity and unit handling for negative, zero, malformed, excessive-precision, float, scientific-notation, unknown-unit, and incompatible-unit inputs where those cases are applicable to the current implementation. Confirm canonical persistence never depends on authoritative binary floating point.

### 2. Tenant and authorization boundary

Verify authenticated and unauthenticated access, least-privilege scope enforcement, cross-tenant detail/list/history reads, cross-tenant references on writes, inactive/revoked credentials where implemented, and actor attribution. Confirm protected mutation order matches the API contract.

### 3. Concurrency and idempotency

Verify stale `If-Match` writes, concurrent successor creation, duplicate idempotency replay, reuse of an idempotency key with a different payload, and transition-target binding. Confirm no retry can create a second externally observable transition.

### 4. Append-only physical history

Verify generic mutation cannot rewrite or delete authoritative `ResourceState`, transition records, or outbox events through the ORM/API/database boundary. Confirm predecessor links and version sequencing remain intact.

### 5. Transactional failure behavior

Inspect and test the boundary between canonical mutation and outbox/audit persistence. Where the current implementation has explicit rollback handling, prove rollback preserves the previous canonical state. Do not introduce artificial infrastructure solely to create a test seam; test the real transaction boundary.

### 6. API contract and error semantics

Cross-check implemented endpoints, authentication requirements, status codes, response envelopes, pagination behavior, ETags/versions, and idempotency behavior against `CRR_API_CONTRACT.md`. Correct implementation/spec drift instead of weakening tests.

### 7. Specification/conformance record

After implementation, update `PHASE_1_PLAN.md` and the conformance matrix only where the audit provides evidence. Explicitly distinguish implemented-but-unproven behavior from tested behavior. Do not mark Phase 2 objects or routing capabilities as implemented.

## Implemented evidence in this increment

- Least-privilege scope denial is exercised for a protected mutation.
- Revoked API keys and inactive actors are rejected.
- Reuse of an idempotency key with a different payload is rejected.
- Missing mutation idempotency keys are rejected.
- Scientific-notation decimal input is exercised and preserved as an exact `Decimal` representation; this is not treated as a binary float.
- A conflicting outbox insert is exercised to prove the canonical Resource mutation and idempotency record roll back together.
- Migration-level append-only history protection remains covered by `tests/test_migrations.py`, including rebuild/recreation of the database triggers.

## Explicit remaining evidence gaps

This increment does not claim to have closed every Phase 1 invariant. In particular, the repository still needs dedicated evidence for exhaustive cross-tenant history/list/write-reference cases, concurrent successor creation under real parallel transactions, every quantity/unit negative or incompatible-input permutation, and the complete final API/specification matrix. Those remain Phase 1 work rather than being silently marked complete.

## Non-goals

- Demand, Capability, Transformation, Route, Decision, Opportunity, Offer, Agreement, Transaction, Execution, Evidence, or EconomicModel implementation.
- Routing, optimization, economics, Jev integration, graph infrastructure, marketplace behavior, or autonomous execution.
- Replacing the current persistence architecture.
- Broad refactoring unrelated to a demonstrated conformance defect.

## Verification result

The final pushed audit commit is `49eb239cc5347fedd2ce2703b0efd21a636643ae`. GitHub Actions run `39066689971` is green: the `test` job passed Ruff, Ruff format, mypy, and the complete pytest suite; the `postgres` job passed PostgreSQL `upgrade → downgrade → upgrade → alembic check`.

The audit increment is therefore verified on the final commit. Phase 1 itself remains open until the explicitly listed evidence gaps and final specification audit are completed.
