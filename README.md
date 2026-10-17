# CRR — Computational Resource Routing

> **A proposed computational infrastructure layer for the physical economy.**
>
> CRR is designed to allow physical resources to be represented, discovered, routed, transformed, traded, executed, and verified across organizational and industrial boundaries.

**Status:** Protocol / architecture foundation  
**Version:** 0.1  
**Repository:** `RayAKaan/CRR`

> **Terminology note:** CRR / Computational Resource Routing is a proposed technical/category name used by this project. It is not being presented as an already-established global industry standard.

---

# 1. What CRR is

Most digital systems are designed around information. The physical economy is constrained by a different class of realities:

- quantities;
- units;
- material state;
- quality;
- contamination;
- location;
- ownership/custody;
- processing capability;
- transformation rules;
- capacity;
- timing;
- logistics;
- regulation;
- safety;
- economics;
- evidence.

CRR proposes a computational infrastructure layer that makes these constraints representable, discoverable, routable, executable, and verifiable.

The fundamental object is not **waste**.

It is **ResourceState**.

```text
RESOURCE IDENTITY
       ↓
RESOURCE STATE
       ↓
TRANSFORMATION
       ↓
NEW RESOURCE STATE
```

A resource can therefore move through a chain such as:

```text
Aluminum
  ↓
Mixed scrap
  ↓
Sorted scrap
  ↓
Clean scrap
  ↓
Molten aluminum
  ↓
Billet
  ↓
Component
```

The system does not merely ask:

> “Who wants this waste?”

It asks:

> **What is the highest-value physically, operationally, economically, and legally/safely feasible route by which this resource can reach another useful state?**

---

# 2. The CRR thesis

The proposed category can be described as **Resource Routing Infrastructure**.

A technical description is:

> **A computational infrastructure layer for industrial resource circulation, extending industrial symbiosis from manually discovered relationships into continuously computed, executable resource flows.**

The long-term system is intended to become infrastructure on top of which participants and third-party applications can discover, route, transform, trade, execute, and verify physical resource flows.

---

# 3. The complete CRR operating loop

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

The central design decision is that CRR does **not** stop at a match, listing, recommendation, or route.

The intended loop closes only when the physical outcome is executed and sufficiently verified.

---

# 4. Why ResourceState is the primitive

A `Resource` is a stable identity and lineage container.

A `ResourceState` represents the physical condition of that resource at a particular point or interval in time.

```text
Resource R1
   │
   ├── State S1: mixed scrap
   ├── State S2: sorted scrap
   ├── State S3: clean scrap
   ├── State S4: molten material
   └── State S5: billet
```

Each state can contain:

- quantity;
- unit;
- material classification;
- physical properties;
- quality;
- location;
- ownership/custody;
- availability;
- effective time;
- provenance;
- evidence;
- predecessor lineage.

Material physical changes must not silently overwrite history.

---

# 5. What CRR is not

CRR should not initially be reduced to:

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
- an autonomous physical-robotics system;
- a giant global ontology built before network density exists.

Those can become applications, services, or ecosystem participants around the protocol. They are not the protocol itself.

---

# 6. Core architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                       PHYSICAL ECONOMY                       │
│ factories · warehouses · processors · buyers · logistics     │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│ RESOURCE REALITY                                             │
│ Organization · Actor · Location · Resource · ResourceState   │
│ quantity · quality · ownership · provenance                   │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│ MARKET + CAPABILITY REALITY                                  │
│ Demand · Capability · Transformation                         │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│ RESOURCE / TRANSFORMATION GRAPH                              │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│ ROUTING ENGINE                                               │
│ hard constraints → feasibility → economics → optimization   │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
                 ┌─────────────┴─────────────┐
                 ↓                           ↓
          DETERMINISTIC ENGINE              JEV
                 └─────────────┬─────────────┘
                               ↓
                       DECISION ENGINE
                               ↓
                         OPPORTUNITY
                               ↓
                     OFFER / AGREEMENT
                               ↓
                         TRANSACTION
                               ↓
                          EXECUTION
                               ↓
                       EVIDENCE / TRUST
                               ↓
                       VERIFIED OUTCOME
                               ↓
                       NETWORK KNOWLEDGE
```

---

# 7. Canonical domain objects

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

Core relationships:

```text
Organization owns Resource
Organization creates Demand
Organization provides Capability
Organization performs Transformation
Organization participates in Transaction

Resource has ResourceState

Transformation consumes ResourceState specifications
Transformation produces ResourceState specifications

Route starts from ResourceState
Route terminates at Demand / target ResourceState

Decision evaluates candidate routes/options
Opportunity proposes Route
Offer proposes commercial terms
Agreement records accepted terms
Transaction executes commercial commitment
Execution records actual operations
Evidence supports/verifies claims
Event records protocol changes
```

---

# 8. Non-negotiable architectural rules

## 8.1 Physical reality is authoritative

A recommendation, embedding, graph projection, cache, score, or AI response cannot become more authoritative than the physical facts it represents.

## 8.2 ResourceState is the physical primitive

The system routes states, not vague resource labels.

## 8.3 Historical physical truth is preserved

Material changes create new states, events, or equivalent auditable history.

## 8.4 Hard constraints are deterministic

Quantity, units, capacity, physical compatibility, timing, authorization, safety, and applicable regulatory blockers cannot be overridden by AI.

## 8.5 Jev is advisory

Jev can reason over a bounded candidate set. It cannot create facts, authorize itself, fabricate evidence, or execute transactions.

## 8.6 Route ≠ execution

A route is a plan. Execution records what actually happened. Evidence establishes what can be verified.

## 8.7 Claimed ≠ verified

CRR explicitly separates planned, actual, claimed, and verified information.

## 8.8 Derived data is disposable

Graphs, embeddings, indexes, rankings, and caches are rebuildable projections.

---

# 9. Validation philosophy

CRR validation is not merely JSON/schema validation.

The conceptual validation pipeline is:

```text
SYNTAX
 ↓
SCHEMA
 ↓
AUTHENTICATION
 ↓
AUTHORIZATION / TENANT
 ↓
REFERENCE INTEGRITY
 ↓
STATE / TIME
 ↓
QUANTITY / UNIT
 ↓
QUALITY
 ↓
LINEAGE / CONSERVATION
 ↓
CAPACITY / LOGISTICS
 ↓
REGULATORY / SAFETY
 ↓
ECONOMICS
 ↓
ROUTING
 ↓
DECISION
 ↓
TRANSACTION
 ↓
EXECUTION
 ↓
EVIDENCE / VERIFICATION
```

The complete validation and invariant registry is maintained in:

[`docs/CRR_VALIDATION_AND_INVARIANTS.md`](./docs/CRR_VALIDATION_AND_INVARIANTS.md)

---

# 10. Routing model

Routing is layered deliberately.

1. **Candidate discovery** — find potentially compatible demand, capabilities, and transformations.
2. **Hard constraints** — reject impossible or unauthorized routes.
3. **Physical feasibility** — validate state transitions, quantity, quality, and transformation compatibility.
4. **Capacity and timing** — validate operating windows, reservations, and delivery constraints.
5. **Logistics** — compute movement requirements and costs.
6. **Regulatory/safety** — enforce applicable hard requirements.
7. **Economics** — compute reproducible value/cost outcomes.
8. **Optimization** — rank feasible routes according to explicit objectives.
9. **Decision support** — optionally use Jev for contextual reasoning.
10. **Human approval** — initially required for material physical/commercial execution.

An infeasible route cannot become feasible because it receives a higher score or favorable AI recommendation.

---

# 11. Decision and Jev model

```text
Decision Engine
   ├── deterministic rules
   ├── hard constraints
   ├── optimization
   ├── evidence checks
   └── DecisionProvider
          └── JevProvider
```

Jev can assist with:

- semantic compatibility;
- ambiguous classification;
- candidate prioritization;
- qualitative tradeoffs;
- contextual interpretation;
- explanations;
- escalation.

Jev cannot:

- override hard constraints;
- invent physical facts;
- create capacity;
- invent regulations;
- fabricate evidence;
- mutate canonical state directly;
- execute commercial/physical actions.

If Jev is unavailable, deterministic routing continues where possible and ambiguous cases can escalate to human review.

---

# 12. Commercial model inside the protocol

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

The distinctions are deliberate:

- **Opportunity:** commercially actionable possibility.
- **Offer:** proposed terms.
- **Agreement:** accepted obligations/terms.
- **Transaction:** protocol-level commercial execution record.

Commercial state does not prove physical completion.

---

# 13. Physical execution and evidence

```text
TRANSACTION
 ↓
EXECUTION
 ↓
PICKUP
 ↓
SHIPMENT
 ↓
RECEIPT
 ↓
PROCESSING
 ↓
OUTPUT
 ↓
DELIVERY / ACCEPTANCE
 ↓
EVIDENCE
 ↓
VERIFICATION
```

Evidence can include:

- weighbridge records;
- laboratory reports;
- inspection records;
- pickup records;
- shipment records;
- delivery receipts;
- processing records;
- buyer acceptance;
- output measurements.

A verified outcome requires the required evidence and an authorized verification process.

---

# 14. Event architecture

Material protocol changes produce immutable events.

Recommended examples:

```text
resource.created
resource.state.created
resource.state.transitioned
demand.created
capability.registered
transformation.registered
route.generated
route.validated
decision.created
opportunity.created
opportunity.proposed
opportunity.approved
offer.created
offer.accepted
agreement.accepted
transaction.created
transaction.scheduled
execution.started
shipment.dispatched
resource.received
transformation.completed
evidence.submitted
evidence.verified
transaction.completed
outcome.verified
```

Event delivery may be at least once, so consumers must be idempotent.

---

# 15. Data authority model

CRR distinguishes:

| Class | Meaning |
|---|---|
| Raw | Original source input |
| Validated | Passed applicable checks |
| Normalized | Converted into canonical form |
| Canonical | Accepted domain truth |
| Derived | Regenerable computation |
| Planned | Intended future action |
| Actual | Observed execution value |
| Claimed | Submitted assertion |
| Verified | Evidence-backed accepted fact |

A raw record is not automatically canonical.

A derived record is never authoritative merely because it was produced by a trusted service.

A planned value is not an actual value.

An actual observation is not automatically verified.

A claim is not a verified fact.

---

# 16. API surface

Reference API prefix:

`/v1`

Canonical resources:

```text
/v1/organizations
/v1/actors
/v1/locations
/v1/resources
/v1/resource-states
/v1/demands
/v1/capabilities
/v1/transformations
/v1/routes
/v1/decisions
/v1/opportunities
/v1/offers
/v1/agreements
/v1/transactions
/v1/executions
/v1/evidence
/v1/economic-models
/v1/events
/v1/webhooks
```

The API enforces authorization, domain validation, idempotency where required, optimistic concurrency, explicit state transitions, and tenant isolation.

Full contract:

[`docs/CRR_API_CONTRACT.md`](./docs/CRR_API_CONTRACT.md)

---

# 17. Reference implementation

A practical reference implementation can use:

- **Backend:** Python + FastAPI + Pydantic
- **Database:** PostgreSQL
- **Geospatial:** PostGIS
- **Evidence:** S3-compatible object storage
- **Async processing:** Redis + Celery or equivalent
- **Frontend:** React + TypeScript
- **API contract:** OpenAPI
- **Decision provider:** `DecisionProvider → JevProvider`
- **Events:** transactional outbox + publisher
- **Graph:** relational projection initially
- **Testing:** unit, integration, contract, property-based, state-machine, failure, security, and end-to-end testing

This is a reference stack, not a protocol dependency.

---

# 18. Repository documentation

The `docs/` directory contains the canonical architecture and protocol specifications.

| Document | Role |
|---|---|
| [`CRR_PROTOCOL_SPEC.md`](./docs/CRR_PROTOCOL_SPEC.md) | Normative protocol meaning, object semantics, lifecycle rules, versioning, conformance, and protocol invariants. |
| [`CRR_DOMAIN_MODEL.md`](./docs/CRR_DOMAIN_MODEL.md) | Canonical domain objects, relationships, ownership, lineage, state machines, and epistemic distinctions. |
| [`SYSTEM_DESIGN.md`](./docs/SYSTEM_DESIGN.md) | Complete reference system architecture, layers, storage, deployment, security, testing, scaling, and MVP. |
| [`CRR_DATA_FLOW_ARCHITECTURE.md`](./docs/CRR_DATA_FLOW_ARCHITECTURE.md) | Complete data movement from physical reality through ingestion, routing, execution, evidence, and verified outcomes. |
| [`CRR_DECISION_AND_ROUTING_SPEC.md`](./docs/CRR_DECISION_AND_ROUTING_SPEC.md) | Candidate discovery, hard constraints, feasibility, capacity, logistics, economics, optimization, decision/Jev boundaries, and routing invariants. |
| [`CRR_API_CONTRACT.md`](./docs/CRR_API_CONTRACT.md) | External API resources, authentication, authorization, errors, precision, concurrency, idempotency, webhooks, ingestion, and versioning. |
| [`CRR_VALIDATION_AND_INVARIANTS.md`](./docs/CRR_VALIDATION_AND_INVARIANTS.md) | Full validation model, invariant registry, failure semantics, security rules, AI adversarial validation, conformance, and testing requirements. |

These documents are designed as one coherent specification set.

---

# 19. Documentation authority

When two documents overlap, use this authority order:

1. **Protocol semantics:** `CRR_PROTOCOL_SPEC.md`
2. **Canonical objects:** `CRR_DOMAIN_MODEL.md`
3. **Validation/invariants:** `CRR_VALIDATION_AND_INVARIANTS.md`
4. **Routing/decision behavior:** `CRR_DECISION_AND_ROUTING_SPEC.md`
5. **Observable API behavior:** `CRR_API_CONTRACT.md`
6. **Reference system architecture:** `SYSTEM_DESIGN.md`
7. **Data movement:** `CRR_DATA_FLOW_ARCHITECTURE.md`

An implementation must not silently redefine a higher-authority rule.

---

# 20. Complete reference scenario

```text
Factory A
  ↓
100 t ResourceState S1
  ↓
Validate quantity / unit / quality / location / ownership
  ↓
Active Demand D1
  ↓
Capability C1
  ↓
Transformation S1 → S2
  ↓
Candidate routes
  ↓
Hard constraints
  ↓
Physical feasibility
  ↓
Capacity + timing
  ↓
Logistics
  ↓
Regulatory / safety
  ↓
Deterministic economics
  ↓
Feasible route ranking
  ↓
Optional Jev decision support
  ↓
Opportunity
  ↓
Offer
  ↓
Agreement
  ↓
Transaction
  ↓
Execution
  ↓
Pickup
  ↓
Shipment
  ↓
Receipt
  ↓
Processing
  ↓
Output S2
  ↓
Delivery / acceptance
  ↓
Evidence
  ↓
Verification
  ↓
Verified outcome
  ↓
Observed yield / cost / time / quality
  ↓
Network knowledge
```

This is the minimum complete proof that CRR is more than a matching engine.

---

# 21. MVP definition

The MVP is intentionally **narrow in scope but broad in architecture**.

Initial operating profile:

- one industrial cluster;
- one to three resource classes;
- several real organizations;
- processors/capabilities;
- relevant logistics;
- human approval;
- at least one complete verified transaction.

The MVP must demonstrate:

```text
RESOURCE EXISTS
→ REPRESENTED
→ DEMAND FOUND
→ CAPABILITY FOUND
→ TRANSFORMATION IDENTIFIED
→ ROUTE COMPUTED
→ ROUTE VALIDATED
→ DECISION MADE
→ OPPORTUNITY CREATED
→ TRANSACTION AGREED
→ EXECUTION COMPLETED
→ EVIDENCE VERIFIED
→ OUTCOME RECORDED
```

The MVP does not require:

- cross-border operations;
- autonomous physical execution;
- principal trading;
- financing;
- insurance;
- a dedicated graph database;
- a global marketplace;
- global ontology completeness;
- microservice decomposition.

---

# 22. Network architecture

Long term, CRR can support an ecosystem of independent participants:

```text
                         CRR NETWORK
                              │
       ┌──────────────────────┼──────────────────────┐
       │                      │                      │
   Logistics              Processing             Finance
       │                      │                      │
 Certification           Brokerage             Insurance
       │                      │                      │
   Analytics             Manufacturing          Markets
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              │
                       Third-party apps
                              │
                         APIs / SDKs
```

Potential ecosystem participants include logistics providers, processors, brokers, laboratories, certification providers, manufacturers, analytics companies, financing providers, insurers, and specialized applications.

The strategic goal is not to prevent other businesses from competing. It is to make participation in the network more valuable than operating without it.

---

# 23. Network flywheel

```text
MORE COMPANIES
       ↓
MORE RESOURCE DATA
       ↓
MORE DEMAND
       ↓
MORE CAPABILITIES
       ↓
MORE POSSIBLE ROUTES
       ↓
MORE TRANSACTIONS
       ↓
MORE VERIFIED OUTCOMES
       ↓
BETTER ROUTING
       ↓
MORE ECONOMIC VALUE
       ↓
MORE COMPANIES
```

Network density is more important than premature geographic breadth.

---

# 24. Scaling roadmap

```text
ONE INDUSTRIAL CLUSTER
        ↓
MULTIPLE COMPANIES
        ↓
MULTIPLE RESOURCE CLASSES
        ↓
PROCESSORS + LOGISTICS
        ↓
VERIFIED TRANSACTIONS
        ↓
MORE CLUSTERS
        ↓
SAUDI ARABIA
        ↓
GCC
        ↓
MENA
        ↓
GLOBAL
```

The system should prove repeatable economic value before expanding across every industry or geography.

---

# 25. Development roadmap

## Phase 0 — CRR Constitution

Freeze terminology, scope, protocol principles, governance, object semantics, invariants, extension rules, and conformance definitions.

## Phase 1 — Resource Reality

Canonical ingestion, normalization, provenance, Resource, and ResourceState.

## Phase 2 — Market Reality

Demand and Capability registries.

## Phase 3 — Route Intelligence

Transformations, graph, routing, economics, optimization, and decision support.

## Phase 4 — Physical Execution

Human-controlled opportunities, transactions, execution, and evidence.

## Phase 5 — Verified Network

Verification, trust, reliability history, and repeat transactions.

## Phase 6 — Saudi Network

Industrial-cluster density and real commercial deployment.

## Phase 7 — Open Infrastructure

APIs, SDKs, webhooks, integrations, and developer tooling.

## Phase 8 — Ecosystem

Logistics, processing, certification, finance, insurance, analytics, and applications.

## Phase 9 — Regional

GCC → MENA.

## Phase 10 — Global

Interoperable cross-border resource routing.

---

# 26. Engineering principles

1. **Reality first.**
2. **Protocol before application complexity.**
3. **ResourceState before marketplace concepts.**
4. **Deterministic constraints before AI recommendations.**
5. **Evidence before trust.**
6. **Execution before impact claims.**
7. **API-first.**
8. **Implementation-independent semantics.**
9. **Human approval before autonomous physical action.**
10. **Append history rather than silently rewrite it.**
11. **Derived data must be rebuildable.**
12. **Network density before geographic breadth.**
13. **Failures must be explicit.**
14. **Every important decision must be auditable.**

---

# 27. What a conforming implementation must preserve

A conforming implementation must preserve:

- stable identity;
- ResourceState semantics;
- quantity/unit precision;
- quality semantics;
- physical lineage;
- demand lifecycle;
- capability lifecycle;
- transformation/yield rules;
- deterministic hard constraints;
- route feasibility;
- economic reproducibility;
- bounded decision support;
- transaction state;
- execution history;
- evidence provenance;
- verification authority;
- event immutability;
- idempotency;
- tenant isolation;
- API version semantics;
- derived/canonical separation.

---

# 28. Implementation independence

CRR does not require:

- PostgreSQL;
- PostGIS;
- FastAPI;
- Python;
- React;
- Redis;
- Celery;
- a dedicated graph database;
- a particular cloud provider;
- Jev;
- a particular AI model.

These are reference implementation choices.

The protocol survives replacement of the database, graph engine, UI, AI provider, worker system, and cloud environment.

---

# 29. Current repository role

This repository is currently the **protocol and architecture foundation** for CRR.

The documentation intentionally establishes the target semantics before implementation complexity is allowed to determine the architecture.

The correct next engineering objective is not to build every feature simultaneously.

It is to implement the protocol core and prove one complete, evidence-backed, economically meaningful physical-resource loop.

---

# 30. Final CRR principle

> **CRR must never allow a computational representation, model output, recommendation, route score, commercial state, cached projection, or user assertion to become more authoritative than the physical, economic, authorization, and evidence-backed reality it represents.**

The complete loop is:

```text
REALITY
  ↓
REPRESENTATION
  ↓
VALIDATION
  ↓
ROUTING
  ↓
DECISION
  ↓
COMMERCIAL COMMITMENT
  ↓
EXECUTION
  ↓
EVIDENCE
  ↓
VERIFICATION
  ↓
TRUSTED OUTCOME
  ↓
BETTER FUTURE ROUTING
```

CRR is intended to make physical-resource circulation computable without losing the distinction between what is proposed, what is observed, what is claimed, and what is verified.

---

# License

License terms are to be defined by the repository owner.
