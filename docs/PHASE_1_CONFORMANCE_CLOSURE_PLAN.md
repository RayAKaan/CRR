# CRR Phase 1 — Conformance Closure Plan

**Status:** Planned before implementation
**Base:** `main` after the final conformance audit increment
**Specification target:** CRR 0.1.1 with normative clarification 0.1.2

## Objective

Close the explicitly recorded Phase 1 evidence gaps without introducing Phase 2 capabilities. This increment is a verification-and-correction pass: audit the current implementation against the authoritative Phase 1/API semantics, add executable evidence for remaining foundation invariants, correct only demonstrated implementation/specification drift, and update the conformance record only from verified behavior.

## Remaining gaps carried forward

1. Exhaustive cross-tenant history/list/write-reference cases.
2. Real parallel concurrency evidence for successor creation.
3. Full quantity/unit negative, malformed, excessive-precision, float, unknown-unit, and incompatible-input matrix applicable to ResourceState.
4. Final API/specification conformance audit for the implemented Phase 1 endpoints, envelopes, status codes, pagination, ETag/version behavior, and idempotency semantics.

## Implementation plan

### 1. Cross-tenant isolation matrix

Exercise organization A and organization B against the same foundation objects. Verify detail, collection, ResourceState history, and mutation/reference paths cannot disclose or mutate another tenant's canonical state. Verify errors remain consistent with the documented tenant-isolation boundary.

### 2. Parallel optimistic-concurrency proof

Use the real persistence boundary and concurrent transactions against PostgreSQL. Create one predecessor ResourceState, race two successor transitions with the same expected predecessor version, and prove exactly one successor commits while the other receives an explicit concurrency conflict. No mocked transaction behavior is permitted.

### 3. Quantity/unit conformance matrix

Add parameterized tests for negative, zero, malformed, excessive-precision, float-shaped, scientific notation, unknown unit, and incompatible unit inputs. Preserve the normative distinction that zero is valid for historical/reconciled state. Verify accepted canonical values remain exact decimals and rejected inputs never mutate canonical state.

### 4. API conformance audit

Cross-check implemented Phase 1 endpoints against `CRR_API_CONTRACT.md`: authentication, authorization ordering, response envelopes, collection pagination, status codes, ETags/versions, idempotency requirements, and ResourceState transition semantics. Correct implementation drift at the API/domain layer rather than weakening tests.

### 5. Documentation/conformance closure

Update `PHASE_1_PLAN.md`, `PHASE_1_FINAL_CONFORMANCE_AUDIT_PLAN.md`, and the conformance matrix only after executable evidence is green. Explicitly record what Phase 1 proves and keep all Phase 2 objects/routing/optimization/Jev/economics functionality out of scope.

## Non-goals

- Demand, Capability, Transformation, Route, Decision, Opportunity, Offer, Agreement, Transaction, Execution, Evidence, or EconomicModel implementation.
- Routing, optimization, Jev integration, economics, graph infrastructure, marketplace behavior, or autonomous execution.
- Broad refactoring without a demonstrated conformance defect.

## Acceptance criteria

The increment is complete only when:

- every four carried-forward evidence gaps has executable evidence or a documented implementation-specific limitation;
- cross-tenant reads and writes are tested across detail, collection, history, and references;
- a real PostgreSQL concurrent transition test proves stale successor rejection;
- the quantity/unit matrix is explicit and passing;
- the implemented Phase 1 API surface is reconciled against the normative contract;
- SQLite tests pass;
- PostgreSQL migration and persistence verification pass;
- Ruff check and format checks pass;
- mypy passes on the configured Phase 1 typed surface;
- the complete pytest suite passes;
- GitHub Actions is green on the final commit;
- documentation accurately reflects verified behavior;
- no Phase 2 functionality is introduced.

## Completion rule

Do not declare Phase 1 complete from local reasoning alone. The final state must be represented by a pushed commit and a green GitHub Actions run for that exact commit. If CI fails, diagnose the exact failure, correct it at the appropriate layer, push a new commit, and repeat until every required job passes.
