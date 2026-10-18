# CRR Specification Index

**Project:** Computational Resource Routing (CRR)  
**Specification version:** 0.1.1, with normative clarification 0.1.2
**Status:** Proposed protocol/category specification  
**Repository:** `RayAKaan/CRR`

> CRR is a proposed technical/category specification created by this project. It is not being presented as an existing global industry standard.

---

## 1. Purpose of this document

This file is the orientation layer for the CRR specification set.

A new engineer, researcher, architect, operator, reviewer, or independent implementation team should be able to start here and understand:

- what CRR is;
- what problem it solves;
- what the canonical concepts are;
- which document is authoritative for each question;
- what is normative versus explanatory;
- how the physical, computational, commercial, execution, and verification layers fit together;
- where AI/Jev is allowed and where it is prohibited;
- what an implementation must preserve to claim conformance.

This document does not replace the normative specifications. It tells the reader how to interpret them together.

---

# 2. CRR in one paragraph

**Computational Resource Routing (CRR)** is a proposed implementation-independent infrastructure protocol for representing, discovering, routing, transforming, trading, executing, and verifying physical-resource flows across organizational and industrial boundaries. CRR treats **ResourceState** as the fundamental physical primitive and separates authoritative physical reality from derived computation, plans, commercial commitments, actual execution, claims, and verification. Its routing process combines deterministic physical, capacity, logistics, authorization, regulatory/safety, and economic constraints with optional decision support such as Jev, then closes the loop through execution and evidence-backed verification.

---

# 3. The central model

```text
RESOURCE IDENTITY
       ↓
RESOURCE STATE
       ↓
TRANSFORMATION
       ↓
NEW RESOURCE STATE
```

The physical economy is modeled as a changing network of resource states, demands, capabilities, transformations, locations, organizations, and transactions.

The complete CRR operating loop is:

```text
PHYSICAL REALITY
↓
RESOURCE OBSERVATION
↓
VALIDATION
↓
CANONICAL RESOURCE STATE
↓
DEMAND + CAPABILITY REALITY
↓
RESOURCE / TRANSFORMATION GRAPH
↓
ROUTE DISCOVERY
↓
HARD-CONSTRAINT VALIDATION
↓
PHYSICAL FEASIBILITY
↓
CAPACITY + LOGISTICS + TIME
↓
REGULATORY / SAFETY VALIDATION
↓
ECONOMICS
↓
OPTIMIZATION
↓
DECISION SUPPORT
↓
OPPORTUNITY
↓
OFFER
↓
AGREEMENT
↓
TRANSACTION
↓
EXECUTION
↓
EVIDENCE
↓
VERIFICATION
↓
VERIFIED OUTCOME
↓
NETWORK KNOWLEDGE
↺
```

The loop is intentionally closed only after physical execution and appropriate verification.

---

# 4. What CRR is not

CRR is not inherently:

- a waste marketplace;
- a recycling directory;
- an ESG dashboard;
- a logistics marketplace;
- an ERP replacement;
- a consumer recycling application;
- a generic AI chatbot;
- a generic LLM wrapper;
- a blockchain/token system;
- a principal trading company;
- a robotics control system;
- a giant ontology that must be completed before deployment.

Those can exist as applications, integrations, services, or ecosystem participants around CRR.

---

# 5. Canonical objects

The minimum canonical vocabulary is:

```text
Organization
Actor
Location
Resource
ResourceState
Demand
Capability
Transformation
Route
Decision
Opportunity
Offer
Agreement
Transaction
Execution
Evidence
EconomicModel
Event
```

Supporting implementation concepts such as users, API keys, jobs, projections, indexes, caches, embeddings, webhook subscriptions, and UI models are not canonical physical objects and MUST NOT redefine the semantics above.

---

# 6. The most important distinctions

## 6.1 Resource vs ResourceState

`Resource` is the stable identity and lineage container.

`ResourceState` is the physical state of that resource at a point or interval in time.

Material changes MUST preserve historical lineage. A current-state pointer is a convenience; it is not permission to erase prior states.

## 6.2 Transformation vs Execution

A `Transformation` is a versioned definition of a permitted/known process and its input/output semantics.

An `Execution` records what actually happened.

A transformation definition is not proof that the process occurred.

## 6.3 Route vs Transaction

A `Route` is a computed plan describing a feasible path through physical and commercial constraints.

A `Transaction` records a commercial commitment/execution relationship.

A route is not a transaction, and a transaction is not proof of physical completion.

## 6.4 Planned vs Actual vs Claimed vs Verified

These are distinct epistemic dimensions, not one universal state machine:

```text
PLANNED   = intended future value
ACTUAL    = observed execution value
CLAIMED   = submitted assertion
VERIFIED  = accepted fact after required verification
```

A value may be planned without being actual, actual without being verified, or claimed without being verified.

## 6.5 Canonical vs Derived

Canonical state is authoritative protocol state accepted under protocol rules.

Derived state includes graphs, rankings, embeddings, search indexes, caches, recommendations, projections, and other rebuildable computations.

Derived data MUST never silently become the source of truth.

## 6.6 Evidence vs Physical truth

Evidence supports a claim about physical reality. Evidence does not become the owner of the physical resource merely because it proves a fact.

The controlling organization/source and protocol-accepted `ResourceState` remain the canonical physical representation; evidence provides provenance and verification support.

---

# 7. Routing in one view

A CRR route is valid only if all applicable blocking constraints pass.

```text
CANDIDATE DISCOVERY
        ↓
HARD CONSTRAINTS
        ↓
PHYSICAL FEASIBILITY
        ↓
QUALITY / LINEAGE
        ↓
CAPACITY / TIME
        ↓
LOGISTICS
        ↓
REGULATORY / SAFETY / AUTHORIZATION
        ↓
ECONOMICS
        ↓
OPTIMIZATION
        ↓
DECISION
```

A score ranks feasible routes. It never converts an infeasible route into a feasible route.

---

# 8. Jev in one view

Jev is an optional decision provider behind a controlled interface.

```text
Decision Engine
├── deterministic rules
├── hard constraints
├── optimization
├── evidence checks
└── DecisionProvider
      └── JevProvider
```

Jev MAY assist with:

- semantic compatibility;
- ambiguity resolution;
- contextual prioritization;
- qualitative tradeoffs;
- explanations;
- escalation.

Jev MUST NOT:

- override hard constraints;
- invent quantities, capacity, cost, regulations, or physical facts;
- fabricate evidence;
- directly mutate canonical state;
- authorize itself;
- execute physical or commercial actions.

CRR must remain useful when Jev is unavailable. Ambiguous cases can escalate to human review.

---

# 9. Commercial chain

```text
ROUTE
↓
OPPORTUNITY
↓
OFFER
↓
AGREEMENT
↓
TRANSACTION
```

An opportunity identifies an actionable possibility. An offer proposes terms. An agreement records accepted terms. A transaction records the resulting commercial commitment and its connection to execution.

Commercial state does not prove physical outcome.

---

# 10. Execution and verification chain

```text
TRANSACTION
↓
EXECUTION
↓
SHIPMENT / TRANSFER / PROCESSING
↓
ACTUAL OBSERVATIONS
↓
EVIDENCE
↓
VERIFICATION
↓
VERIFIED OUTCOME
```

Examples of evidence include weighbridge records, laboratory reports, inspection records, shipment records, delivery receipts, processing records, and buyer acceptance.

The required evidence depends on the claim being verified.

---

# 11. Data authority model

CRR uses the following conceptual classifications:

| Classification | Meaning |
|---|---|
| RAW | Original source input |
| VALIDATED | Passed applicable validation |
| NORMALIZED | Converted into canonical representation |
| CANONICAL | Accepted protocol-domain truth |
| DERIVED | Rebuildable computation |
| PLANNED | Intended future action/value |
| ACTUAL | Observed execution value |
| CLAIMED | Submitted assertion |
| VERIFIED | Evidence-backed accepted fact |

These classifications are not a universal linear lifecycle. They describe different dimensions of information authority and epistemic status.

---

# 12. Non-negotiable invariants

A conforming implementation MUST preserve, at minimum:

1. no negative authoritative quantity;
2. no ambiguous or invalid unit conversion;
3. no impossible transformation;
4. no route that violates a blocking hard constraint;
5. no stale/expired demand used as active demand;
6. no revoked/expired capability used for execution;
7. no allocation above remaining demand or capacity;
8. no destructive physical history mutation;
9. no broken lineage across split/merge/transform operations;
10. no unverified claim treated as verified fact;
11. no unauthorized cross-tenant disclosure;
12. no duplicate externally observable effect from retried mutations;
13. no stale write silently overwriting newer canonical state;
14. no decision provider overriding authoritative constraints;
15. no Jev direct mutation of canonical state;
16. no verification without an authorized verifier and required evidence;
17. no event replay causing duplicate domain effects;
18. no canonical economic result that cannot be deterministically reproduced from its recorded inputs and calculation version;
19. no state transition without attribution and auditability;
20. no derived projection promoted to canonical truth merely because it is convenient.

The complete registry is in `CRR_VALIDATION_AND_INVARIANTS.md`.

---

# 13. Document authority map

Use the following order when resolving overlap:

| Question | Authoritative document |
|---|---|
| What does CRR mean? | `CRR_PROTOCOL_SPEC.md` |
| What are the canonical objects? | `CRR_DOMAIN_MODEL.md` |
| What must be rejected or blocked? | `CRR_VALIDATION_AND_INVARIANTS.md` |
| How is a route computed? | `CRR_DECISION_AND_ROUTING_SPEC.md` |
| How do external systems interact? | `CRR_API_CONTRACT.md` |
| How is the reference system assembled? | `SYSTEM_DESIGN.md` |
| How does data move through the system? | `CRR_DATA_FLOW_ARCHITECTURE.md` |
| How are cross-document ambiguities resolved? | `CRR_NORMATIVE_AMENDMENT_0.1.1.md` and `CRR_NORMATIVE_AMENDMENT_0.1.2.md` |
| How should a new reader navigate the specification? | `CRR_SPECIFICATION_INDEX.md` |

If an explanatory document conflicts with a normative rule, the normative rule wins.

---

# 14. Protocol vs reference implementation

The protocol is implementation-independent.

A practical reference stack is:

```text
Python / FastAPI / Pydantic
PostgreSQL / PostGIS
S3-compatible evidence storage
Redis + Celery or equivalent
React + TypeScript
OpenAPI
Transactional outbox + publisher
Relational graph projection initially
DecisionProvider → JevProvider
```

Another implementation may use different languages, databases, queues, or deployment models and still conform if its externally observable semantics preserve CRR.

---

# 15. Conformance ladder

CRR conformance is progressive:

```text
LEVEL 0 — SCHEMA
Represent canonical objects correctly.

LEVEL 1 — REALITY
Preserve physical-state, provenance, lineage, quantity, and authority semantics.

LEVEL 2 — ROUTING
Implement feasibility, constraints, capacity, logistics, economics, and route semantics.

LEVEL 3 — TRANSACTION
Implement opportunity, offer, agreement, transaction, and execution semantics.

LEVEL 4 — VERIFICATION
Implement evidence, verification, attribution, and verified outcomes.

LEVEL 5 — NETWORK
Interoperate with independent CRR implementations and third-party ecosystem participants.
```

An implementation should state explicitly which level it claims.

---

# 16. MVP boundary

The first operational proof should be narrow but architecturally complete:

```text
Factory A
→ ResourceState
→ Demand
→ Capability
→ Transformation
→ Candidate Routes
→ Hard Constraint Validation
→ Feasible Route
→ Economics
→ Decision
→ Opportunity
→ Agreement
→ Transaction
→ Execution
→ Shipment
→ Receipt
→ Transformation
→ Evidence
→ Verification
→ Verified Outcome
→ Network Update
```

The MVP does not require cross-border routing, autonomous execution, principal trading, financing, insurance, a dedicated graph database, a third-party marketplace, or a global ontology.

---

# 17. Implementation reading order

For implementation work, read in this order:

1. this file;
2. `CRR_PROTOCOL_SPEC.md`;
3. `CRR_DOMAIN_MODEL.md`;
4. `CRR_VALIDATION_AND_INVARIANTS.md`;
5. `CRR_DECISION_AND_ROUTING_SPEC.md`;
6. `CRR_API_CONTRACT.md`;
7. `CRR_DATA_FLOW_ARCHITECTURE.md`;
8. `SYSTEM_DESIGN.md`;
9. `CRR_NORMATIVE_AMENDMENT_0.1.1.md`.
10. `CRR_NORMATIVE_AMENDMENT_0.1.2.md` for zero quantity and lifecycle separation.

Then use the repository README for project-level orientation.

---

# 18. Reviewer checklist

A reviewer should be able to answer “yes” to all of the following before calling the specification coherent:

- Is ResourceState the physical primitive?
- Is historical physical lineage preserved?
- Are canonical and derived data separated?
- Are planned, actual, claimed, and verified values separated?
- Are hard constraints deterministic and blocking?
- Can AI/Jev override a hard constraint? **It must be no.**
- Is a route distinct from execution?
- Is a transaction distinct from physical completion?
- Can stale writes overwrite canonical state? **They must not.**
- Can retries duplicate transactions or reservations? **They must not.**
- Can a client directly set a verification result? **It must not.**
- Can a revoked capability be selected? **It must not.**
- Can a derived graph become physical truth? **It must not.**
- Can economics be reproduced from recorded inputs and calculation version?
- Can independent implementations understand the same objects and transitions?
- Can a human trace a verified outcome back to the physical state, transaction, execution, and evidence that support it?

If any answer is no, the implementation is not semantically conforming even if its JSON schema is valid.

---

# 19. Current executable routing boundary

The currently implemented routing foundation progresses through deterministic candidate discovery, physical feasibility, and logistics feasibility before economics or optimization.

Phase 3C specifically establishes transport planning semantics for authoritative locations: explicit transport mode, distance, duration, payload capacity, endpoint validation, exact-decimal unit conversion, timing-window validation, and machine-readable hard-constraint rejection. Logistics remains a plan and does not imply reservation, shipment execution, commercial commitment, or verification.

The detailed implementation plans remain in the phase-specific documents, including `PHASE_3A_ROUTING_FOUNDATION_PLAN.md`, `PHASE_3B_PHYSICAL_FEASIBILITY_PLAN.md`, and `PHASE_3C_LOGISTICS_FEASIBILITY_PLAN.md`.
