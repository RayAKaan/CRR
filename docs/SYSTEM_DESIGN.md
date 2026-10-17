# CRR System Design

**Status:** Normative reference system design  
**Version:** 0.1  
**Protocol:** Computational Resource Routing (CRR)  
**Scope:** End-to-end reference architecture from physical resource observation through verified outcome and network feedback.

> CRR is a proposed computational infrastructure/category specification. This document defines the recommended reference system; it does not make the implementation stack part of the protocol itself.

---

# 1. System thesis

CRR is a proposed computational infrastructure layer that allows the physical economy to discover, route, transform, trade, execute, and verify resource flows across organizational and industrial boundaries.

The fundamental primitive is **ResourceState**, not waste.

```text
RESOURCE IDENTITY
      ↓
RESOURCE STATE
      ↓
TRANSFORMATION
      ↓
NEW RESOURCE STATE
```

The system therefore moves from representation to routing and then all the way to verified physical execution.

---

# 2. System objectives

CRR must be designed to:

1. represent physical reality as computable protocol objects;
2. preserve physical lineage and historical truth;
3. connect supply, demand, capabilities, and transformations;
4. compute executable routes rather than simple matches;
5. enforce hard constraints deterministically;
6. separate deterministic truth from probabilistic/advisory reasoning;
7. coordinate commercial transactions;
8. coordinate physical execution without prematurely automating unsafe actions;
9. capture evidence and verified outcomes;
10. expose stable APIs for independent applications and participants;
11. allow derived knowledge to improve future routing;
12. remain operational if an AI provider disappears;
13. remain semantically valid if infrastructure components are replaced.

---

# 3. Non-goals

CRR is not initially:

- a generic waste marketplace;
- a recycling directory;
- a logistics company;
- a recycling company;
- an ERP replacement;
- a consumer recycling application;
- a generic chatbot;
- an ESG dashboard;
- a blockchain/token system;
- an autonomous physical-robotics system;
- a principal trading company;
- a global ontology project built before network density exists.

Those can become applications or ecosystem participants around CRR, but they are not the protocol core.

---

# 4. Architecture principles

1. **Physical reality is authoritative.**
2. **ResourceState is the physical primitive.**
3. **Resource is identity/lineage, not a substitute for state.**
4. **Historical physical facts are not destructively rewritten.**
5. **Hard constraints are deterministic.**
6. **AI is bounded and advisory.**
7. **Every material decision is explainable and auditable.**
8. **Evidence distinguishes claims from verified outcomes.**
9. **APIs are first-class interfaces.**
10. **Human approval is the initial physical/commercial execution boundary.**
11. **Derived data is regenerable.**
12. **Protocol semantics are independent of infrastructure technology.**
13. **The system must fail safely rather than silently weaken constraints.**
14. **Verified outcomes improve future computation without rewriting history.**

---

# 5. Complete architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                       PHYSICAL ECONOMY                       │
│ factories · warehouses · processors · buyers · logistics     │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│ RESOURCE REALITY                                             │
│ Organization · Actor · Location · Resource · ResourceState   │
│ provenance · ownership · quality · quantity                   │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│ MARKET + CAPABILITY REALITY                                  │
│ Demand · Capability · Transformation                         │
└──────────────────────────────┬───────────────────────────────┘
                               ↓
┌──────────────────────────────────────────────────────────────┐
│ RESOURCE / TRANSFORMATION GRAPH                              │
│ canonical reality → derived relationships                    │
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
                               ↺
```

---

# 6. Logical layers

## Layer 1 — Physical reality

The physical economy is the ultimate source of what the system is trying to represent.

## Layer 2 — Reality registry

Canonical objects represent accepted observations: Organization, Actor, Location, Resource, ResourceState, Demand, Capability, and Transformation.

## Layer 3 — Resource graph

The graph connects canonical objects into a computational network. It is a projection, not the ultimate source of truth.

## Layer 4 — Routing

Routing constructs and validates possible physical paths.

## Layer 5 — Decision

Decision support ranks or selects among already-valid candidates.

## Layer 6 — Commercial execution

Opportunity, Offer, Agreement, Transaction.

## Layer 7 — Physical execution

Pickup, shipment, receipt, processing, delivery, acceptance.

## Layer 8 — Evidence/trust

Evidence establishes what can be verified.

## Layer 9 — Network learning

Verified outcomes become inputs to future derived computation.

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

These objects and their relationships are defined in `CRR_DOMAIN_MODEL.md`.

---

# 8. Resource architecture

A Resource is the stable identity/lineage container. A ResourceState represents a physical state.

```text
Resource R1
   │
   ├── State S1: mixed scrap
   ├── State S2: sorted scrap
   ├── State S3: clean scrap
   └── State S4: processed output
```

Material changes create new states or equivalent auditable history. The system must preserve quantity, units, quality, location, ownership/custody, availability, provenance, and lineage.

---

# 9. Demand architecture

Demand is a structured acceptance requirement.

```text
Demand
 ├── required state
 ├── quantity
 ├── quality
 ├── location
 ├── timing
 ├── price constraints
 ├── certifications
 ├── regulatory constraints
 └── substitutions
```

Demand lifecycle must be explicit so expired or fulfilled demand cannot continue receiving allocations.

---

# 10. Capability architecture

Capability describes what an organization can physically perform.

```text
Capability
 ├── accepted inputs
 ├── transformations
 ├── outputs
 ├── capacity
 ├── operating windows
 ├── locations
 ├── minimum batches
 ├── costs
 ├── certifications
 └── regulatory eligibility
```

The system calculates available capacity from declared capacity and current commitments/reservations.

---

# 11. Transformation architecture

A transformation is a versioned state-transition definition.

```text
INPUT STATE
    ↓
PROCESS REQUIREMENTS
    ↓
PROCESS
    ↓
YIELD / LOSS / RESIDUAL MODEL
    ↓
OUTPUT STATE
```

A transformation must define inputs, outputs, yield bounds, losses/residuals, duration, capacity, cost, quality effects, and safety/regulatory requirements. The definition does not prove execution.

---

# 12. Graph architecture

The Resource Graph is a derived projection of canonical state. It connects organizations, resources, states, locations, demands, capabilities, transformations, routes, opportunities, transactions, and evidence relationships.

The graph should support queries such as:

- what can this resource become?
- who can perform the transformation?
- who needs the resulting state?
- which paths are geographically feasible?
- which capabilities have capacity?
- which previous routes succeeded?

A dedicated graph database is not required for the MVP. A relational graph projection is sufficient if it remains auditable and rebuildable.

---

# 13. Routing architecture

Routing has distinct stages:

1. candidate discovery;
2. hard constraints;
3. physical feasibility;
4. capacity and timing;
5. logistics;
6. transformation feasibility;
7. regulatory/safety eligibility;
8. economics;
9. optimization;
10. contextual decision support.

The output is a set of feasible route candidates with traceable calculations and invalidation reasons.

A route score cannot make an infeasible route feasible.

---

# 14. Geographic architecture

Location data should be canonical and provenance-aware.

Geospatial calculations may include distance, travel-time assumptions, route feasibility, facility proximity, and geographic eligibility.

A reference implementation may use PostGIS.

A model, user, or derived projection must not manipulate authoritative coordinates or distances merely to make an economics calculation pass.

---

# 15. Economic architecture

The EconomicModel is deterministic and reproducible.

```text
GROSS VALUE
+ BUYER PAYMENT
+ OTHER VALUE
- TRANSPORT
- PROCESSING
- HANDLING
- CERTIFICATION
- TAXES / FEES
= NET OUTCOME
```

Every model stores currency, component inputs, assumptions, calculation version, source references, timestamp, and resulting value.

Economic calculations are not delegated to an LLM as authoritative arithmetic.

---

# 16. Decision architecture

```text
Decision Engine
   ├── deterministic rules
   ├── hard-constraint validation
   ├── optimization
   ├── evidence checks
   └── DecisionProvider
          └── JevProvider
```

The provider interface isolates the protocol from any particular AI provider.

The system should continue operating if the provider is unavailable.

---

# 17. Jev boundary

Jev may assist with semantic compatibility, classification ambiguity, contextual prioritization, qualitative tradeoffs, explanations, and escalation recommendations.

Jev cannot override hard constraints, invent quantities/capacity/demand/organizations/regulations, fabricate evidence, write canonical physical state directly, or execute transactions.

The input to Jev should be a structured decision context, not an uncontrolled database dump.

The decision record retains provider, model/version, context hash, candidate set, result, rationale, uncertainty, evidence references, and escalation status.

---

# 18. Opportunity architecture

```text
FEASIBLE ROUTE
      ↓
OPPORTUNITY
      ↓
COMMERCIAL PARTICIPANTS
      ↓
ECONOMICS / REQUIREMENTS
      ↓
OFFER
```

An opportunity cannot be approved if its underlying route, demand, capability, authorization, or economic assumptions are invalid.

---

# 19. Transaction architecture

```text
Opportunity
   ↓
Offer
   ↓
Agreement
   ↓
Transaction
```

Transactions are state machines rather than arbitrary status records. The system records the exact terms that caused the transaction to become executable.

---

# 20. Execution architecture

Execution coordinates:

```text
TRANSACTION
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
DELIVERY
 ↓
ACCEPTANCE
```

Human approval is the initial boundary for material physical/commercial actions. Automation can be introduced later for constrained, low-risk operations without changing protocol semantics.

---

# 21. Evidence and trust architecture

Evidence is the bridge between digital claims and verified physical outcomes.

Potential evidence includes weighbridge records, laboratory reports, inspection records, shipment records, delivery records, processing records, and buyer acceptance.

Verification is an authorized act.

```text
CLAIMED ≠ SUBMITTED ≠ VERIFIED
```

---

# 22. Event architecture

```text
CANONICAL WRITE
     ↓
EVENT
     ↓
OUTBOX
     ↓
PUBLISHER
     ↓
WEBHOOKS / PROJECTIONS / ANALYTICS / INTEGRATIONS
```

Events are immutable. At-least-once delivery is acceptable if consumers are idempotent.

A transactional outbox is recommended for the reference implementation so that a committed state change cannot permanently lack its required event record.

---

# 23. API architecture

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

The API supports authentication, authorization, tenant isolation, idempotency, optimistic concurrency, explicit state transitions, pagination, filtering, structured errors, request/correlation IDs, and asynchronous status where required.

---

# 24. Security architecture

Security is part of domain integrity.

Required boundaries include authentication, authorization, organization isolation, least privilege, scoped evidence access, sensitive commercial data controls, audit logs, secrets management, and protected decision-provider credentials.

Verification permissions should be separated from ordinary evidence submission where practical.

---

# 25. Data lifecycle architecture

```text
RAW
 ↓
VALIDATED
 ↓
NORMALIZED
 ↓
CANONICAL
 ↓
DERIVED
 ↓
PLANNED
 ↓
ACTUAL
 ↓
CLAIMED
 ↓
VERIFIED
```

The lifecycle is conceptual rather than a single database status column. Different objects occupy different parts of the lifecycle.

---

# 26. Reference storage architecture

A practical implementation may use PostgreSQL for canonical objects and event/outbox records, PostGIS for geospatial calculations, object storage for evidence, Redis for cache, workers for asynchronous processing, and a relational graph projection for derived relationships.

An analytics warehouse and specialized search infrastructure may be introduced later. They remain derived.

---

# 27. Reference repository architecture

```text
crr/
  apps/
    api/
    worker/
    web/
  packages/
    protocol/
    domain/
    routing/
    decision/
    economics/
    graph/
    events/
    integrations/
    sdk/
  migrations/
  tests/
    unit/
    integration/
    contract/
    e2e/
    property/
    state-machine/
    failure/
    security/
  docs/
    protocol/
    architecture/
    data-flow/
    system-design/
    adr/
  infra/
  scripts/
```

This is a reference organization, not a protocol requirement.

---

# 28. MVP architecture

The MVP is narrow in operational scope but broad in architectural coverage.

Initial profile:

- one industrial cluster;
- one to three resource classes;
- several real organizations;
- at least one processor/capability;
- relevant logistics participation;
- one complete verified transaction.

The MVP must prove:

```text
REAL RESOURCE
→ RESOURCE STATE
→ DEMAND
→ CAPABILITY
→ TRANSFORMATION
→ ROUTE
→ VALIDATION
→ DECISION
→ OPPORTUNITY
→ OFFER
→ AGREEMENT
→ TRANSACTION
→ EXECUTION
→ EVIDENCE
→ VERIFICATION
→ NETWORK UPDATE
```

The MVP is the first vertical slice of the protocol, not a reduced marketplace.

---

# 29. MVP human boundary

```text
SYSTEM RECOMMENDS
       ↓
HUMAN REVIEWS
       ↓
HUMAN APPROVES
       ↓
TRANSACTION EXECUTES
       ↓
EVIDENCE CAPTURED
```

Autonomous execution should only be introduced after sufficient evidence, governance, reliability, and constrained authorization exist.

---

# 30. Failure architecture

The system must explicitly handle invalid input, missing quality, insufficient quantity, expired demand, revoked capability, insufficient capacity, route failure, economic infeasibility, regulatory uncertainty, failed logistics, failed processing, yield variance, rejected delivery, bad evidence, disputed evidence, duplicate requests, event replay, worker crashes, database interruptions, Jev failures, webhook failures, and stale projections.

Hard constraints fail closed. AI/provider failures fail safely or escalate.

---

# 31. Observability

The system should be able to answer:

- What happened?
- Which object changed?
- Who changed it?
- Why did it change?
- Which event caused it?
- Which route candidates existed?
- Which constraints failed?
- Which decision provider was used?
- Which evidence supported the result?
- Which economic assumptions were used?

Correlation IDs should propagate across API, workers, events, routing, decisions, and execution.

---

# 32. Testing architecture

Testing must cover:

- unit validation;
- integration behavior;
- API contracts;
- complete end-to-end flows;
- property-based quantity/lineage/conservation tests;
- state-machine tests;
- route feasibility tests;
- evidence/verification tests;
- idempotency/replay tests;
- tenant isolation;
- failure injection;
- adversarial AI behavior.

The system should prove not only that valid flows work, but that invalid physical or commercial states cannot be accepted.

---

# 33. Performance and scaling architecture

Scale first through network density rather than premature infrastructure complexity.

```text
ONE CLUSTER
    ↓
MORE ORGANIZATIONS
    ↓
MORE RESOURCE TYPES
    ↓
MORE DEMAND
    ↓
MORE CAPABILITIES
    ↓
MORE ROUTES
    ↓
MORE VERIFIED TRANSACTIONS
    ↓
MORE CLUSTERS
```

Dedicated graph infrastructure, distributed routing, specialized search, warehouse infrastructure, or service decomposition should be introduced only when workload and product requirements justify them.

---

# 34. Network architecture

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

The objective is to make participation economically valuable, not to prevent competitors from building businesses.

---

# 35. Deployment architecture

The first reference deployment can be a modular monolith plus worker processes.

```text
             INTERNET
                ↓
        API / WEB APPLICATION
                ↓
       DOMAIN / ROUTING CORE
          ↙          ↘
 PostgreSQL/PostGIS   Redis
        ↓                ↓
 Evidence Storage    Worker Queue
        ↓                ↓
    Object Store    Async Processing
                ↓
        EVENT PUBLISHER
                ↓
       WEBHOOKS / APPS
```

The system can later decompose into services without changing protocol semantics.

---

# 36. Protocol versus reference system

The protocol defines object semantics, relationships, lifecycle rules, validation requirements, evidence semantics, routing semantics, decision boundaries, event semantics, and API-observable behavior.

The reference system defines framework, database, worker technology, deployment, UI, cloud, and provider integration.

The reference implementation is replaceable.

---

# 37. Definition of done

The architecture is implementation-ready when:

- canonical objects are defined;
- ResourceState is authoritative;
- lineage is preserved;
- exact quantities and economics are enforced;
- demand/capability lifecycle rules exist;
- transformations are explicit;
- route feasibility is deterministic;
- Jev is bounded behind a provider interface;
- commercial state machines are explicit;
- execution separates planned and actual values;
- evidence is attributable and verifiable;
- events are immutable and replay-safe;
- APIs enforce authorization and idempotency;
- derived projections are rebuildable;
- one complete verified transaction can be demonstrated.

---

# 38. Final architecture invariant

If PostgreSQL, PostGIS, Redis, Celery, the graph projection, the UI, the AI provider, the cloud provider, or the reference implementation itself is replaced, the following must remain unchanged in meaning:

```text
RESOURCE IDENTITY
RESOURCE STATE
LINEAGE
DEMAND
CAPABILITY
TRANSFORMATION
ROUTE
DECISION
TRANSACTION
EXECUTION
EVIDENCE
VERIFIED OUTCOME
```

The architecture is successful when infrastructure can evolve without changing the truth model of the physical network.
