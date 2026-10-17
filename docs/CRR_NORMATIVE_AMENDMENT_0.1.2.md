# CRR Normative Amendment 0.1.2

**Status:** Normative clarification for CRR 0.1.1
**Applies to:** All CRR 0.1 documentation and conforming implementations

## 1. Zero-quantity ResourceState

This section supersedes any earlier rule requiring `quantity > 0` for every ResourceState, including the validation example in `CRR_VALIDATION_AND_INVARIANTS.md`. The invariant remains exact and non-negative quantity; positivity applies to available supply and routing allocation.

Canonical quantities MUST be exact decimals and MUST NOT be negative. A ResourceState MAY record zero quantity when it represents a valid measured, completed, or reconciled physical history. A zero-quantity state MUST NOT represent available supply and MUST NOT be selected as a route source. Any route allocation MUST have a strictly positive quantity no greater than the source quantity available under the applicable allocation model.

## 2. ResourceState history and lifecycle dimensions

A ResourceState is an immutable, attributable representation of physical condition over its effective time semantics. A material physical change creates a successor state through an explicit transition/correction operation; it does not mutate the predecessor. The transition records the predecessor, resulting state, actor, organization, occurrence time, provenance, and applicable validation result.

ResourceState lifecycle, commercial lifecycle, availability/reservation, execution progress, and epistemic classifications are separate dimensions. The generic ResourceState status sequence in the 0.1 Domain Model and the `status` property in the ResourceState example in `CRR_API_CONTRACT.md` are illustrative only; it MUST NOT be implemented as a universal linear state machine. Availability and execution status MUST be represented by their own governed records when those capabilities are implemented. A client MUST NOT set any such lifecycle or availability value through an unrestricted status patch.

## 3. Routing consequence

Routing MUST use a positive, currently available quantity under the applicable source-state, ownership/custody, and allocation rules. A zero-quantity ResourceState remains part of auditable history but is ineligible as available supply.

## 4. Precedence

This amendment resolves only the zero-quantity and ResourceState lifecycle ambiguities described above. It otherwise leaves the CRR 0.1.1 document authority order and all other protocol semantics unchanged.
