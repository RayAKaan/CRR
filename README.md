# CRR — Computational Resource Routing

> **A proposed computational infrastructure layer for the physical economy.**
>
> CRR is designed to allow physical resources to be represented, discovered, routed, transformed, traded, executed and verified across organizational and industrial boundaries.

**Status:** Architecture / protocol design and reference implementation foundation  
**Version:** 0.1  
**Repository:** `RayAKaan/CRR`

---

## What CRR is

Most digital systems are built around information. The physical economy is different: it is constrained by quantities, locations, material properties, processing capabilities, capacity, timing, regulation, logistics and economics.

CRR proposes an infrastructure layer that makes those constraints computable.

The fundamental object is not “waste.” It is **Resource State**.

```text
RESOURCE
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

CRR asks:

> **What is the highest-value physically, operationally, economically and legally/safely feasible next state this resource can reach?**

rather than simply:

> “Who wants this waste?”

---

## The CRR operating loop

```text
PHYSICAL REALITY
       ↓
RESOURCE REPRESENTATION
       ↓
DEMAND + CAPABILITY REALITY
       ↓
RESOURCE / TRANSFORMATION GRAPH
       ↓
ROUTE COMPUTATION
       ↓
DETERMINISTIC VALIDATION
       ↓
DECISION SUPPORT
       ↓
OPPORTUNITY
       ↓
TRANSACTION
       ↓
EXECUTION
       ↓
EVIDENCE
       ↓
VERIFIED OUTCOME
       ↓
NETWORK LEARNING
       ↺
```

The key principle is that CRR does not stop at a match or recommendation. The intended system closes the loop from physical reality to verified physical outcome.

---

# Why this repository exists

CRR is being developed as a protocol and infrastructure concept rather than as a conventional marketplace application.

The repository separates:

- **Protocol semantics** — what CRR means.
- **Domain model** — what objects exist and how they relate.
- **System architecture** — how a reference implementation can operate.
- **Data flow** — how physical and digital information moves through the system.
- **Routing and decision logic** — how feasible resource routes are computed and selected.
- **Validation and invariants** — what must never be violated.
- **API contract** — how independent implementations and applications can interact with CRR.

The goal is to make the protocol implementation-independent so that PostgreSQL, FastAPI, a graph database, a UI, an AI provider, or a cloud platform can eventually be replaced without changing the meaning of the underlying physical network.

---

# Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                       PHYSICAL ECONOMY                       │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│ RESOURCE REALITY                                             │
│ Resource · ResourceState · Location · Provenance             │
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
│ Hard constraints → feasibility → economics → optimization    │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
                 ┌─────────────┴─────────────┐
                 ↓                           ↓
          DETERMINISTIC ENGINE             JEV
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
                         NETWORK UPDATE
```

---

# Core domain objects

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
Transformation consumes ResourceState / produces ResourceState
Route starts from ResourceState and terminates at Demand or target state
Opportunity proposes Route
Transaction executes Opportunity
Execution produces Evidence
Evidence verifies claims
Event records protocol changes
Decision records decision provenance
```

---

# The most important architectural rules

### 1. Physical reality is authoritative

The system cannot allow a recommendation, embedding, cached projection or model response to become more authoritative than the physical facts it represents.

### 2. ResourceState is the physical primitive

A Resource is a stable identity/lineage container. ResourceState represents the actual physical condition, quantity, location, quality, ownership/custody and availability.

### 3. History is not destructively rewritten

Material physical changes create new states/events. Corrections remain auditable.

### 4. Hard constraints are deterministic

Quantity, units, capacity, physical compatibility, timing, authorization and other hard constraints cannot be overridden by an AI model.

### 5. Jev is advisory

Jev may assist with classification, semantic compatibility, prioritization, ambiguity and contextual decisions. It cannot create facts, override constraints, fabricate evidence or execute physical/commercial actions.

### 6. A route is not an execution

A route is a plan. An execution records what actually happened. Evidence establishes what can be verified.

### 7. Claimed is not verified

CRR explicitly distinguishes planned, actual, claimed and verified information.

### 8. Derived data is disposable

Graphs, embeddings, rankings, caches and projections must be rebuildable from canonical state.

---

# Repository documentation

The canonical architecture documentation is under [`docs/`](./docs/).

| Document | Purpose |
|---|---|
| [`CRR_DATA_FLOW_ARCHITECTURE.md`](./docs/CRR_DATA_FLOW_ARCHITECTURE.md) | End-to-end data flow from physical reality through verified outcomes. |
| [`SYSTEM_DESIGN.md`](./docs/SYSTEM_DESIGN.md) | Full reference system architecture and implementation boundaries. |
| [`CRR_PROTOCOL_SPEC.md`](./docs/CRR_PROTOCOL_SPEC.md) | Implementation-independent CRR protocol semantics and conformance model. |
| [`CRR_DOMAIN_MODEL.md`](./docs/CRR_DOMAIN_MODEL.md) | Canonical domain objects, relationships and lifecycle states. |
| [`CRR_API_CONTRACT.md`](./docs/CRR_API_CONTRACT.md) | External API behavior, resources, errors, authorization, idempotency and versioning. |
| [`CRR_DECISION_AND_ROUTING_SPEC.md`](./docs/CRR_DECISION_AND_ROUTING_SPEC.md) | Routing pipeline, hard constraints, economics, ranking and Jev decision boundaries. |
| [`CRR_VALIDATION_AND_INVARIANTS.md`](./docs/CRR_VALIDATION_AND_INVARIANTS.md) | Normative validation system, invariant registry, failure semantics and conformance tests. |

These documents are intended to be read together. No single implementation file should silently redefine protocol semantics established here.

---

# Reference system behavior

A complete CRR transaction should be representable as:

```text
Factory A
  ↓
100 t ResourceState S1
  ↓
Validation
  ↓
Demand D1
  ↓
Capability C1
  ↓
Transformation S1 → S2
  ↓
Route candidates
  ↓
Hard-constraint validation
  ↓
Economic calculation
  ↓
Decision support
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
Transport
  ↓
Processing
  ↓
Delivery
  ↓
Evidence
  ↓
Verification
  ↓
Verified Outcome
  ↓
Network update
```

This complete loop is the central proof that CRR is more than a marketplace or matching engine.

---

# Routing model

Routing is deliberately layered:

1. **Candidate discovery** — find potentially compatible demand, capabilities and transformations.
2. **Hard constraints** — reject impossible or unauthorized routes.
3. **Physical feasibility** — validate state transitions, quantity, quality and transformation compatibility.
4. **Capacity and timing** — validate operating windows, reservations and delivery constraints.
5. **Logistics** — compute movement requirements and costs.
6. **Regulatory/safety** — enforce applicable hard requirements.
7. **Economics** — compute reproducible value/cost outcomes.
8. **Optimization** — rank feasible routes according to explicit objectives.
9. **Decision support** — optionally use Jev for contextual reasoning.
10. **Human approval** — initially required for material commercial/physical execution.

An infeasible route cannot become feasible because it receives a higher score or a favorable AI recommendation.

---

# Validation model

CRR validation covers more than schemas:

```text
Syntax
 ↓
Schema
 ↓
Authorization
 ↓
References
 ↓
State / Time
 ↓
Quantity / Units
 ↓
Quality
 ↓
Lineage / Conservation
 ↓
Capacity / Logistics
 ↓
Regulation / Safety
 ↓
Economics
 ↓
Routing
 ↓
Decision
 ↓
Transaction
 ↓
Execution
 ↓
Evidence / Verification
```

The full invariant registry is maintained in `CRR_VALIDATION_AND_INVARIANTS.md`.

---

# Event model

Material state changes produce immutable events.

Recommended event types include:

```text
resource.created
resource.state.created
resource.state.transitioned
demand.created
capability.registered
transformation.registered
route.generated
decision.created
opportunity.created
opportunity.proposed
opportunity.approved
offer.created
agreement.accepted
transaction.created
execution.started
shipment.dispatched
resource.received
transformation.completed
evidence.submitted
evidence.verified
transaction.completed
outcome.verified
```

Event delivery can be at least once. Consumers therefore need idempotent processing.

---

# API surface

The reference API is versioned under `/v1` and is organized around the canonical domain model:

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

Mutation operations are designed around authorization, idempotency, optimistic concurrency and explicit state transitions.

---

# Reference implementation stack

The protocol is technology-neutral. A practical reference implementation can use:

- **Backend:** Python + FastAPI + Pydantic
- **Database:** PostgreSQL
- **Geospatial:** PostGIS
- **Evidence:** S3-compatible object storage
- **Async work:** Redis + Celery or equivalent
- **Frontend:** React + TypeScript
- **API specification:** OpenAPI
- **Decision provider:** `DecisionProvider → JevProvider` adapter
- **Events:** transactional outbox + publisher
- **Graph:** relational projection initially; dedicated graph database only when justified

The architecture does not require this stack.

---

# MVP definition

The MVP is intentionally narrow in commercial scope but broad in architectural coverage.

Initial target:

- one industrial cluster;
- one to three resource categories;
- a small set of real organizations;
- processors/capabilities;
- real or tightly controlled logistics;
- at least one complete verified transaction.

The MVP must prove:

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

The MVP does **not** require cross-border operations, autonomous execution, principal trading, financing, insurance, a dedicated graph database, or a global marketplace.

---

# Network architecture

The long-term network can support independent participants and applications:

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
                       Developer APIs
```

The strategic objective is not to prevent other businesses from existing. It is to make participation in the network more valuable than operating without it.

---

# Scaling thesis

```text
ONE INDUSTRIAL CLUSTER
        ↓
MORE COMPANIES
        ↓
MORE RESOURCES
        ↓
MORE DEMAND
        ↓
MORE CAPABILITIES
        ↓
MORE ROUTES
        ↓
MORE VERIFIED TRANSACTIONS
        ↓
BETTER ROUTING
        ↓
MORE ECONOMIC VALUE
        ↓
MORE PARTICIPANTS
        ↓
MORE CLUSTERS
        ↓
SAUDI
        ↓
GCC
        ↓
MENA
        ↓
GLOBAL
```

---

# What CRR is not

CRR should not initially be reduced to:

- a waste marketplace;
- a recycling directory;
- an ESG dashboard;
- a logistics marketplace;
- an ERP replacement;
- a generic AI wrapper;
- a chatbot;
- a token/blockchain system;
- a consumer recycling application.

Those can become applications around a deeper protocol if they create value, but they are not the protocol itself.

---

# Design status and terminology

**CRR / Computational Resource Routing** is a proposed technical/category name used by this project. It should not be presented as an already-established global industry standard.

The broader company/category thesis can be described as:

> **Resource Routing Infrastructure — infrastructure that allows the physical economy to discover, route, transform, trade, execute and verify resources across organizational and industrial boundaries.**

A more technical description is:

> **A computational infrastructure layer for industrial resource circulation, extending industrial symbiosis from manually discovered relationships into continuously computed, executable resource flows.**

---

# Engineering principles

1. **Reality first.**
2. **Protocol before application complexity.**
3. **Resource State before marketplace concepts.**
4. **Deterministic constraints before AI recommendations.**
5. **Evidence before trust.**
6. **Execution before claims of impact.**
7. **API-first and implementation-independent.**
8. **Human approval before autonomous physical action.**
9. **Append history rather than rewriting it.**
10. **Build network density before geographic breadth.**

---

# Development roadmap

### Phase 0 — CRR Constitution
Freeze terminology, protocol principles, object semantics, invariants and governance.

### Phase 1 — Resource Reality
Canonical ingestion and ResourceState representation.

### Phase 2 — Market Reality
Demand and capability registries.

### Phase 3 — Route Intelligence
Transformations, graph, routing, economics and decision support.

### Phase 4 — Physical Execution
Human-controlled transaction and execution workflows.

### Phase 5 — Verified Network
Evidence, trust and repeat transactions.

### Phase 6 — Saudi Network
Build density in selected industrial clusters.

### Phase 7 — Open Infrastructure
APIs, SDKs, webhooks and developer tooling.

### Phase 8 — Ecosystem
Enable logistics, processing, certification, finance, insurance, analytics and applications.

### Phase 9 — Regional
GCC → MENA.

### Phase 10 — Global
Interoperable cross-border resource routing.

---

# Documentation authority

When documents appear to overlap:

1. `CRR_PROTOCOL_SPEC.md` defines protocol meaning.
2. `CRR_DOMAIN_MODEL.md` defines canonical domain objects and relationships.
3. `CRR_VALIDATION_AND_INVARIANTS.md` defines what must not be violated.
4. `CRR_DECISION_AND_ROUTING_SPEC.md` defines route and decision semantics.
5. `CRR_API_CONTRACT.md` defines observable API behavior.
6. `SYSTEM_DESIGN.md` defines the reference system architecture.
7. `CRR_DATA_FLOW_ARCHITECTURE.md` describes information movement through that architecture.

An implementation must not silently contradict a higher-level normative rule.

---

# Current status

This repository currently serves as the **CRR protocol and architecture foundation**. The documentation establishes the target semantics and reference architecture before implementation complexity is introduced.

The next implementation priority is not to build every possible feature. It is to implement the protocol core and prove a complete, evidence-backed physical resource loop.

---

# License

License terms are to be defined by the repository owner.
