# CRR Conformance and Cross-Document Matrix

**Protocol:** Computational Resource Routing (CRR)  
**Specification target:** 0.1.1 with normative clarification 0.1.2
**Purpose:** Provide a reviewer-facing matrix showing where each major CRR concern is defined and what a conforming implementation must preserve.

> This is a navigation and audit artifact. Normative semantics remain in the authoritative documents identified below.

---

# 1. Canonical object coverage

| Object | Domain | Protocol | Validation | Routing | API | Data Flow | System |
|---|---:|---:|---:|---:|---:|---:|---:|
| Organization | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Actor | ✓ | ✓ | ✓ | — | ✓ | ✓ | ✓ |
| Location | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Resource | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ResourceState | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Demand | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Capability | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Transformation | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Route | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Decision | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Opportunity | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Offer | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Agreement | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Transaction | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Execution | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Evidence | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| EconomicModel | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Event | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

`—` means the concern is not a primary focus of that document, not that the object is unsupported.

---

# 2. Semantic invariants

| Requirement | Required behavior |
|---|---|
| Physical primitive | `ResourceState` is the authoritative physical-state primitive. |
| Resource identity | `Resource` provides stable identity and lineage context. |
| Historical truth | Material physical history is never silently destroyed. |
| Quantity | Exact semantics; no authoritative binary floating point; zero may represent valid historical state. |
| Units | Ambiguous/invalid conversions are rejected. |
| Conservation | Applicable transformations reconcile inputs, outputs, and declared loss/residual within explicit tolerance. |
| Lineage | Split/merge/transform operations preserve traceable ancestry. |
| Quality | Incompatible quality blocks routing unless a declared transformation can alter it. |
| Capacity | Routing cannot consume unavailable capacity. |
| Demand | Expired/cancelled/fully satisfied demand cannot be active. |
| Capability | Revoked/expired/suspended capability cannot be selected for execution. |
| Hard constraints | Blocking constraints are deterministic and cannot be overridden by AI. |
| Route | A route is a plan, not proof of execution. |
| Staleness | Material commitments revalidate stale routes. |
| Economics | Results are reproducible from recorded inputs and calculation version. |
| Commercial state | Opportunity/offer/agreement/transaction are distinct. |
| Execution | Actual operations are distinct from plans and commercial commitments. |
| Evidence | Evidence supports claims; it is not itself physical truth. |
| Verification | Verification is authorized, evidence-backed, and auditable. |
| AI/Jev | Advisory only; no direct canonical mutation or hard-constraint override. |
| Derived data | Graphs/indexes/embeddings/rankings/caches are rebuildable and non-authoritative. |
| Tenant isolation | Cross-organization access is explicitly authorized. |
| Concurrency | Stale writes cannot silently overwrite newer state. |
| Idempotency | Retries cannot duplicate externally observable effects. |
| Events | Events are immutable and replay-safe. |
| Attribution | Material transitions identify actor, organization, and time. |

---

# 3. Lifecycle coverage

## Opportunity

```text
DISCOVERED
→ VALIDATING
→ PROPOSED
→ APPROVED
```

Terminal alternatives include `REJECTED` and `EXPIRED`.

## Transaction

```text
DISCOVERED
→ PROPOSED
→ ACCEPTED
→ AGREED
→ SCHEDULED
→ EXECUTING
→ COMPLETED
→ VERIFIED
```

Illegal transitions MUST be rejected.

## Evidence

```text
CLAIMED
→ SUBMITTED
→ VERIFIED
```

Terminal alternatives include `REJECTED` and `DISPUTED`.

## Decision

```text
REQUESTED
→ EVALUATING
→ GENERATED
→ VALIDATED
→ ACCEPTED
```

Terminal alternatives include `REJECTED` and `ESCALATED`.

These are lifecycle semantics, not permission for clients to set arbitrary status values.

---

# 4. Epistemic model

CRR MUST NOT collapse the following concepts into one state machine:

```text
RAW
VALIDATED
NORMALIZED
CANONICAL
DERIVED
PLANNED
ACTUAL
CLAIMED
VERIFIED
```

They represent different dimensions of authority, processing history, intention, observation, assertion, and verification.

Examples:

```text
canonical + planned
canonical + actual
canonical + claimed
canonical + verified
derived + planned
derived + claimed
```

The implementation may choose a different storage model, but the semantics must remain distinguishable.

---

# 5. Decision authority boundary

```text
                AUTHORITATIVE SYSTEM
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
 HARD CONSTRAINTS    FACTS / STATE     ECONOMIC MODEL
        │                │                │
        └────────────────┼────────────────┘
                         ↓
                  DECISION ENGINE
                         ↓
                  DecisionProvider
                         ↓
                    JevProvider
```

The provider can improve interpretation and prioritization but cannot become the authority for physical truth.

If the provider fails, the implementation should continue deterministically where possible and escalate where ambiguity prevents safe continuation.

---

# 6. API safety boundary

The API MUST enforce the following sequence for protected mutations:

```text
REQUEST
↓
AUTHENTICATION
↓
AUTHORIZATION / TENANT CHECK
↓
SCHEMA VALIDATION
↓
REFERENCE VALIDATION
↓
DOMAIN / INVARIANT VALIDATION
↓
CONCURRENCY CHECK
↓
CANONICAL MUTATION
↓
AUDIT / EVENT
↓
RESPONSE
```

For material `ResourceState` changes, the generic patch surface MUST NOT provide unrestricted authority over physical semantics. Explicit transition/correction semantics are required.

---

# 7. Data flow audit

A complete implementation should be traceable through:

```text
PHYSICAL REALITY
↓
INGESTION
↓
RAW INPUT
↓
VALIDATION
↓
NORMALIZATION
↓
CANONICAL STATE
↓
DERIVED GRAPH / INDEX
↓
ROUTE DISCOVERY
↓
FEASIBILITY
↓
ECONOMICS
↓
DECISION
↓
COMMERCIAL COMMITMENT
↓
EXECUTION
↓
ACTUAL OBSERVATIONS
↓
EVIDENCE
↓
VERIFICATION
↓
VERIFIED OUTCOME
↓
NETWORK UPDATE
```

The derived graph may be rebuilt from canonical data. It is never the only copy of physical truth.

---

# 8. Minimum conformance evidence

A system claiming a CRR conformance level should be able to demonstrate:

### Level 0 — Schema

- canonical object representations;
- required IDs and versions;
- valid API envelopes.

### Level 1 — Reality

- ResourceState semantics;
- provenance;
- exact quantities/units;
- lineage preservation;
- authority separation;
- historical state preservation.

### Level 2 — Routing

- candidate discovery;
- hard constraints;
- physical feasibility;
- capacity/time;
- logistics;
- regulatory/safety;
- reproducible economics;
- optimization over feasible routes.

### Level 3 — Transaction

- opportunity;
- offer;
- agreement;
- transaction;
- execution;
- explicit lifecycle transitions;
- idempotent mutation behavior.

### Level 4 — Verification

- evidence submission;
- authorized verification;
- verification history;
- disputes/corrections;
- verified outcomes.

### Level 5 — Network

- independent implementation interoperability;
- third-party participants;
- stable protocol/version semantics;
- externally verifiable conformance claims.

---

# 9. Adversarial acceptance tests

A conforming implementation should fail safely under at least these tests:

1. attempt negative quantity;
2. attempt invalid unit conversion;
3. attempt impossible transformation;
4. route with insufficient capacity;
5. route with expired demand;
6. route with revoked capability;
7. route with incompatible quality;
8. route blocked by safety/regulation;
9. AI recommends a prohibited route;
10. AI recommends a route with fabricated capacity;
11. client submits `VERIFIED` without verifier authority;
12. stale client overwrites newer ResourceState;
13. duplicate transaction request with same idempotency key;
14. duplicate event delivery;
15. cross-tenant object access;
16. altered evidence after verification;
17. economic replay with changed calculation inputs;
18. route execution after route expiry;
19. split/merge that loses lineage;
20. transformation whose outputs violate declared yield bounds.

Each case should produce an explicit, auditable outcome rather than silent corruption.

---

# 10. Reviewer conclusion standard

A reviewer should not conclude that CRR is conforming merely because:

- the API responds successfully;
- JSON schemas validate;
- a graph exists;
- an LLM produces plausible recommendations;
- a transaction record exists;
- a dashboard shows a green status.

The decisive question is:

> **Can an independent reviewer trace a physical resource from authoritative state through routing, constraints, economics, commercial commitment, actual execution, evidence, and verification without any derived layer, AI output, stale write, or unverified claim silently becoming physical truth?**

If not, the implementation is not semantically conforming.

---

# 11. Phase 3C executable conformance

Phase 3C adds deterministic logistics feasibility to the routing implementation boundary without creating execution or reservation semantics.

The executable evidence is:

- explicit immutable transport-mode and logistics evaluation contracts;
- authoritative source/destination endpoint checks;
- cross-tenant rejection at the logistics boundary;
- exact-decimal distance validation;
- versioned unit-registry capacity conversion;
- transport payload capacity rejection;
- maximum-distance rejection;
- deterministic travel arrival calculation;
- destination timing-window rejection;
- zero-quantity supply rejection;
- machine-readable `LOCATION_INFEASIBLE`, `CAPACITY_INSUFFICIENT`, `TIME_WINDOW_CONFLICT`, `UNIT_INCOMPATIBLE`, and `INSUFFICIENT_QUANTITY` outcomes;
- deterministic repeated evaluation tests;
- full repository CI including PostgreSQL migration/model/conformance checks.

Phase 3C does **not** claim economics, optimization, reservations, commercial conversion, physical shipment execution, evidence verification, or autonomous action.
