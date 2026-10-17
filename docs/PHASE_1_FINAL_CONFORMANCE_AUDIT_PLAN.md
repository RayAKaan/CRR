# CRR Phase 1 — Final Conformance Audit Plan

**Status:** Planned before implementation
**Base:** `main` after Phase 1 conformance-hardening merge
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2

## Objective

Close the remaining verification gap identified by the Phase 1 plan without beginning Phase 2. The purpose of this increment is to prove, rather than assume, that the implemented foundation preserves the Phase 1 invariants across validation, authorization, tenancy, concurrency, idempotency, failure handling, append-only history, persistence, and the documented API boundary.

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

## Non-goals

- Demand, Capability, Transformation, Route, Decision, Opportunity, Offer, Agreement, Transaction, Execution, Evidence, or EconomicModel implementation.
- Routing, optimization, economics, Jev integration, graph infrastructure, marketplace behavior, or autonomous execution.
- Replacing the current persistence architecture.
- Broad refactoring unrelated to a demonstrated conformance defect.

## Acceptance criteria

The increment is complete only when:

- every selected Phase 1 invariant has an explicit executable test or a documented reason it cannot yet be exercised;
- any discovered implementation/specification mismatch is corrected at the correct layer;
- SQLite tests pass;
- PostgreSQL migration and persistence verification passes;
- Ruff check passes;
- Ruff format check passes;
- mypy passes on the configured Phase 1 typed surface;
- the complete pytest suite passes;
- GitHub Actions is green on the final commit;
- documentation accurately distinguishes proven Phase 1 behavior from future protocol scope;
- no Phase 2 functionality is introduced accidentally.

## Completion rule

Do not declare this increment complete from local reasoning alone. The final state must be represented by a pushed commit and a green GitHub Actions run for that exact commit. If CI fails, diagnose and correct the failure, rerun CI, and repeat until all required jobs pass.
