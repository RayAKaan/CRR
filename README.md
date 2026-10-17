# CRR — Computational Resource Routing

> **A proposed computational infrastructure layer for the physical economy.**

CRR is a proposed implementation-independent protocol/category for representing, discovering, routing, transforming, trading, executing, and verifying physical-resource flows across organizational and industrial boundaries.

**Status:** Proposed protocol / architecture foundation  
**Specification:** 0.1.1 with normative clarification 0.1.2
**Repository:** `RayAKaan/CRR`

> **Important:** CRR is a project-defined technical/category specification. It is **not** being presented as an existing global industry standard.

---

## 1. Start here

If you are new to CRR, read the repository in this order:

1. [`docs/CRR_SPECIFICATION_INDEX.md`](./docs/CRR_SPECIFICATION_INDEX.md) — complete orientation and terminology map.
2. [`docs/CRR_PROTOCOL_SPEC.md`](./docs/CRR_PROTOCOL_SPEC.md) — normative protocol semantics.
3. [`docs/CRR_DOMAIN_MODEL.md`](./docs/CRR_DOMAIN_MODEL.md) — canonical objects and relationships.
4. [`docs/CRR_VALIDATION_AND_INVARIANTS.md`](./docs/CRR_VALIDATION_AND_INVARIANTS.md) — validation and blocking rules.
5. [`docs/CRR_DECISION_AND_ROUTING_SPEC.md`](./docs/CRR_DECISION_AND_ROUTING_SPEC.md) — routing and decision engine.
6. [`docs/CRR_API_CONTRACT.md`](./docs/CRR_API_CONTRACT.md) — external API semantics.
7. [`docs/CRR_DATA_FLOW_ARCHITECTURE.md`](./docs/CRR_DATA_FLOW_ARCHITECTURE.md) — end-to-end data movement.
8. [`docs/SYSTEM_DESIGN.md`](./docs/SYSTEM_DESIGN.md) — reference implementation architecture.
9. [`docs/CRR_NORMATIVE_AMENDMENT_0.1.1.md`](./docs/CRR_NORMATIVE_AMENDMENT_0.1.1.md) — cross-document consistency clarifications.
10. [`docs/CRR_NORMATIVE_AMENDMENT_0.1.2.md`](./docs/CRR_NORMATIVE_AMENDMENT_0.1.2.md) — zero-quantity history and ResourceState lifecycle clarification.

The index is the best entry point for an engineer, researcher, reviewer, or independent implementation team.

---

# 2. What CRR is

Most digital systems are designed around information. The physical economy is constrained by a different class of realities:

- quantities;
- units;
- physical state;
- quality and contamination;
- location;
- ownership and custody;
- processing capability;
- transformation rules;
- capacity;
- timing;
- logistics;
- regulation;
- safety;
- economics;
- evidence;
- actual execution.

CRR proposes an infrastructure layer that makes these constraints representable, discoverable, routable, executable, and verifiable.

The fundamental physical primitive is **ResourceState**.

```text
RESOURCE IDENTITY
       ↓
RESOURCE STATE
       ↓
TRANSFORMATION
       ↓
NEW RESOURCE STATE
```

A resource can move through a chain such as:

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

CRR therefore does not merely ask:

> Who wants this material?

It asks:

> **What is the highest-value physically, operationally, economically, and legally/safely feasible route by which this resource can reach another useful state?**

---

# 3. The CRR thesis

A useful category description is **Resource Routing Infrastructure**.

A more technical description is:

> **A computational infrastructure layer for industrial resource circulation, extending industrial symbiosis from manually discovered relationships into continuously computed, executable resource flows.**

The long-term goal is infrastructure on top of which participants and third-party applications can discover, route, transform, trade, execute, and verify physical resource flows.

CRR is not required to own the physical resources. Its initial role is to provide the computational protocol and coordination infrastructure around them.

---

# 4. The complete operating loop

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

The loop deliberately does **not** end at discovery, matching, recommendation, or route generation. The intended loop closes when the physical outcome has been executed and sufficiently verified.

---

# 5. What CRR is not

CRR should not be reduced to:

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

Those can become applications, integrations, services, or ecosystem participants around CRR. They are not the protocol itself.

---

# 6. Core architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                      PHYSICAL ECONOMY                       │
│ factories · warehouses · processors · buyers · logistics    │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ RESOURCE REALITY                                            │
│ Organization · Actor · Location · Resource · ResourceState  │
│ quantity · quality · ownership/custody · provenance         │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ MARKET + CAPABILITY REALITY                                 │
│ Demand · Capability · Transformation                        │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ RESOURCE / TRANSFORMATION GRAPH                             │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ ROUTING ENGINE                                              │
│ hard constraints → feasibility → economics → optimization  │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
                 ┌────────────┴────────────┐
                 ↓                         ↓
          DETERMINISTIC ENGINE            JEV
                 └────────────┬────────────┘
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
Route terminates at Demand or target ResourceState

Decision evaluates candidate routes/options
Opportunity proposes Route
Offer proposes commercial terms
Agreement records accepted terms
Transaction executes commercial commitment
Execution records actual operations
Evidence supports/verifies claims
Event records protocol changes
```

The complete semantics are defined in [`CRR_DOMAIN_MODEL.md`](./docs/CRR_DOMAIN_MODEL.md).

---

# 8. The distinctions that make CRR work

## Resource vs ResourceState

`Resource` is a stable identity and lineage container.

`ResourceState` is the physical condition of that resource at a point or interval in time.

Material physical changes preserve history rather than silently overwriting it.

## Transformation vs Execution

`Transformation` is a versioned process definition.

`Execution` records what actually happened.

A transformation definition is not proof that the process occurred.

## Route vs Execution

A `Route` is a computed plan.

`Execution` records actual operations.

A feasible route does not prove that the route was executed.

## Commercial commitment vs physical outcome

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
 ↓
EXECUTION
```

A completed commercial transaction is not automatically a completed physical transformation.

## Planned vs Actual vs Claimed vs Verified

These are **separate epistemic dimensions**, not one universal linear lifecycle.

- `PLANNED` — intended future value/action.
- `ACTUAL` — observed execution value.
- `CLAIMED` — submitted assertion.
- `VERIFIED` — accepted fact after the required verification process.

## Canonical vs Derived

Canonical data is accepted protocol-domain truth.

Derived data includes graphs, embeddings, indexes, rankings, recommendations, projections, and caches. These are rebuildable and MUST NOT silently become physical truth.

## Evidence vs physical truth

Evidence supports a claim about physical reality. Evidence does not become the physical resource state itself.

---

# 9. Non-negotiable architectural rules

1. **Physical reality is authoritative.** Derived computation cannot outrank authoritative facts.
2. **ResourceState is the physical primitive.** Routing operates on specific states rather than vague labels.
3. **Physical history is preserved.** Material changes are represented through new state/version/transition history.
4. **Hard constraints are deterministic and blocking.** AI cannot override them.
5. **Jev is advisory.** It reasons inside a bounded decision interface.
6. **Route is not execution.** Plans and actual operations are distinct.
7. **Claim is not verification.** Evidence-backed verification is explicit.
8. **Derived data is disposable.** Graphs, embeddings, indexes, rankings, and caches can be rebuilt.
9. **Important transitions are attributable.** Actor, organization, time, and provenance matter.
10. **Important state is versioned.** Stale writes cannot silently overwrite newer state.
11. **External mutations are retry-safe.** Idempotency is required where duplicate effects are possible.
12. **The protocol is implementation-independent.** A reference stack is not a protocol dependency.
13. **Human approval is initially required for material physical/commercial actions.**
14. **Third parties can implement the protocol independently.**

The cross-document consistency rules are in [`CRR_NORMATIVE_AMENDMENT_0.1.1.md`](./docs/CRR_NORMATIVE_AMENDMENT_0.1.1.md), with zero-quantity and lifecycle clarifications in [`CRR_NORMATIVE_AMENDMENT_0.1.2.md`](./docs/CRR_NORMATIVE_AMENDMENT_0.1.2.md).

---

# 10. Routing model

Routing is intentionally layered:

1. **Candidate discovery** — find potentially compatible demand, capabilities, and transformations.
2. **Hard constraints** — reject impossible or unauthorized routes.
3. **Physical feasibility** — validate state transitions, quantity, quality, and transformation compatibility.
4. **Capacity and timing** — validate operating windows and finite capacity.
5. **Logistics** — validate movement requirements and costs.
6. **Regulatory/safety** — enforce applicable blockers.
7. **Economics** — calculate reproducible value/cost outcomes.
8. **Optimization** — rank feasible routes against explicit objectives.
9. **Decision support** — optionally use Jev for bounded contextual reasoning.
10. **Human approval** — initially required before material execution.

An infeasible route cannot become feasible because it receives a higher score or favorable AI recommendation.

See [`CRR_DECISION_AND_ROUTING_SPEC.md`](./docs/CRR_DECISION_AND_ROUTING_SPEC.md).

---

# 11. Jev / AI boundary

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
- ambiguous classification;
- candidate prioritization;
- qualitative tradeoffs;
- contextual interpretation;
- explanations;
- escalation.

Jev MUST NOT:

- override hard constraints;
- invent physical facts;
- create capacity;
- invent regulations;
- fabricate evidence;
- mutate canonical state directly;
- authorize itself;
- execute physical/commercial actions.

If Jev is unavailable, deterministic routing continues where possible and ambiguous cases can escalate to humans.

---

# 12. Physical execution and evidence

```text
TRANSACTION
 ↓
EXECUTION
 ↓
PICKUP / TRANSFER
 ↓
SHIPMENT
 ↓
RECEIPT
 ↓
PROCESSING
 ↓
OUTPUT
 ↓
ACCEPTANCE
 ↓
EVIDENCE
 ↓
VERIFICATION
 ↓
VERIFIED OUTCOME
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

# 13. Data authority model

| Classification | Meaning |
|---|---|
| `RAW` | Original source input |
| `VALIDATED` | Passed applicable checks |
| `NORMALIZED` | Converted into canonical representation |
| `CANONICAL` | Accepted domain truth |
| `DERIVED` | Rebuildable computation |
| `PLANNED` | Intended future action/value |
| `ACTUAL` | Observed execution value |
| `CLAIMED` | Submitted assertion |
| `VERIFIED` | Evidence-backed accepted fact |

These are not a universal state machine. They describe different authority/epistemic properties that may coexist.

---

# 14. Validation philosophy

CRR validation is substantially more than JSON schema validation.

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

The full validation registry and invariants are in [`CRR_VALIDATION_AND_INVARIANTS.md`](./docs/CRR_VALIDATION_AND_INVARIANTS.md).

---

# 15. Quantity and economics

Authoritative quantities and monetary values use exact decimal semantics or equivalent exact representations.

Example quantity:

```json
{
  "value": "100.000",
  "unit": "t"
}
```

Example money:

```json
{
  "amount": "125000.00",
  "currency": "SAR"
}
```

Binary floating point MUST NOT be the authoritative physical or monetary representation.

Where conservation applies:

```text
INPUTS = OUTPUTS + DECLARED LOSSES / RESIDUALS
```

within an explicit tolerance and declared transformation model.

Economic calculation conceptually follows:

```text
VALUE
− TRANSPORT
− PROCESSING
− HANDLING
− CERTIFICATION
− TAXES / FEES
− OTHER COSTS
=
NET ECONOMIC VALUE
```

Calculation assumptions, versions, sources, currencies, quantities, and rounding policy must be reproducible.

---

# 16. Event architecture

Material protocol changes are represented by immutable events.

Representative events include:

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

At-least-once delivery is acceptable, but consumers MUST be idempotent.

---

# 17. API surface

Reference API prefix:

```text
/v1
```

Core resources:

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

Important API principles:

- authorization before protected disclosure;
- domain validation before canonical mutation;
- explicit lifecycle transitions;
- idempotency for duplicate-effect mutations;
- optimistic concurrency for stale writes;
- tenant isolation;
- machine-readable errors;
- asynchronous status for long-running operations.

Material `ResourceState` changes should use explicit transition operations and MUST NOT be freely writable through a generic patch.

See [`CRR_API_CONTRACT.md`](./docs/CRR_API_CONTRACT.md).

---

# 18. Security model

CRR implementations should provide:

- OAuth2/OIDC users or equivalent identity;
- API keys/service accounts for machine access;
- least-privilege RBAC/scopes;
- strict tenant isolation;
- protected evidence access;
- protected economics and proprietary capability data;
- encryption in transit and at rest as appropriate;
- secure secret handling;
- signed webhooks where appropriate;
- immutable/auditable event history;
- controlled decision-provider context.

Representative roles:

```text
ORG_ADMIN
RESOURCE_MANAGER
OPERATOR
TRANSACTION_MANAGER
VERIFIER
AUDITOR
DEVELOPER
READ_ONLY
```

A client cannot make an object verified simply by submitting `status = VERIFIED`.

---

# 19. Reference implementation architecture

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

# 20. Conformance

CRR defines a progressive conformance ladder:

```text
LEVEL 0 — SCHEMA
Canonical object representation.

LEVEL 1 — REALITY
Physical-state, provenance, quantity, lineage, and authority semantics.

LEVEL 2 — ROUTING
Feasibility, constraints, capacity, logistics, economics, and route semantics.

LEVEL 3 — TRANSACTION
Opportunity, offer, agreement, transaction, and execution semantics.

LEVEL 4 — VERIFICATION
Evidence, verification, attribution, disputes, and verified outcomes.

LEVEL 5 — NETWORK
Independent implementations and third-party ecosystem interoperability.
```

Using CRR object names or `/v1` endpoints alone does not constitute full conformance. Observable semantic behavior is what matters.

---

# 21. MVP boundary

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

The MVP does **not** require:

- cross-border routing;
- autonomous execution;
- principal trading;
- financing or insurance;
- a dedicated graph database;
- a third-party marketplace;
- a global ontology.

The MVP philosophy is **narrow operational scope with final architectural principles**.

---

# 22. Strategic rollout

The intended network strategy is density before breadth:

```text
ONE CLUSTER
↓
MULTIPLE COMPANIES
↓
MULTIPLE RESOURCE TYPES
↓
PROCESSORS
↓
LOGISTICS
↓
TRANSACTIONS
↓
VERIFIED OUTCOMES
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

Saudi Arabia is a plausible launch market, but CRR should not be described as having no competitors or as an already established standard. The differentiation is the proposed protocol/infrastructure model and its closed loop from physical reality to verified outcome.

---

# 23. Economic flywheel

```text
MORE COMPANIES
↓
MORE RESOURCE DATA
↓
MORE DEMAND
↓
MORE CAPABILITIES
↓
MORE ROUTES
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

Potential commercial layers include:

1. enterprise resource intelligence;
2. success/transaction fees;
3. execution coordination;
4. verification;
5. API/infrastructure access;
6. later ecosystem, logistics, financing, or insurance services.

The initial model should favor facilitation and managed execution rather than principal ownership of resource risk.

---

# 24. Third-party ecosystem

CRR is designed to support independent participants such as:

- logistics providers;
- resource brokers;
- processors;
- laboratories;
- certification providers;
- financing providers;
- insurers;
- analytics applications;
- manufacturers;
- specialized marketplaces;
- developer applications.

The protocol should remain useful even when these participants are supplied by independent organizations.

---

# 25. Documentation map

| Document | Authority / purpose |
|---|---|
| [`CRR_SPECIFICATION_INDEX.md`](./docs/CRR_SPECIFICATION_INDEX.md) | Orientation, distinctions, reading order, reviewer checklist. |
| [`CRR_PROTOCOL_SPEC.md`](./docs/CRR_PROTOCOL_SPEC.md) | Normative protocol semantics, objects, lifecycle, versioning, conformance. |
| [`CRR_DOMAIN_MODEL.md`](./docs/CRR_DOMAIN_MODEL.md) | Canonical objects, relationships, identity, lineage, and state semantics. |
| [`CRR_VALIDATION_AND_INVARIANTS.md`](./docs/CRR_VALIDATION_AND_INVARIANTS.md) | Validation pipeline, invariant registry, failure semantics, security, testing, conformance. |
| [`CRR_DECISION_AND_ROUTING_SPEC.md`](./docs/CRR_DECISION_AND_ROUTING_SPEC.md) | Routing, hard constraints, feasibility, capacity, logistics, economics, optimization, Jev boundaries. |
| [`CRR_API_CONTRACT.md`](./docs/CRR_API_CONTRACT.md) | External API behavior, precision, auth, concurrency, idempotency, resources, webhooks. |
| [`CRR_DATA_FLOW_ARCHITECTURE.md`](./docs/CRR_DATA_FLOW_ARCHITECTURE.md) | End-to-end data movement from physical reality to verified outcome. |
| [`SYSTEM_DESIGN.md`](./docs/SYSTEM_DESIGN.md) | Reference architecture, storage, services, deployment, security, testing, scaling, MVP. |
| [`CRR_NORMATIVE_AMENDMENT_0.1.1.md`](./docs/CRR_NORMATIVE_AMENDMENT_0.1.1.md) | Cross-document normative clarifications and strict consistency rules. |
| [`CRR_NORMATIVE_AMENDMENT_0.1.2.md`](./docs/CRR_NORMATIVE_AMENDMENT_0.1.2.md) | Zero-quantity historical states and ResourceState lifecycle separation. |

### Authority order

1. Protocol semantics — `CRR_PROTOCOL_SPEC.md`
2. Canonical objects — `CRR_DOMAIN_MODEL.md`
3. Validation/invariants — `CRR_VALIDATION_AND_INVARIANTS.md`
4. Routing/decision — `CRR_DECISION_AND_ROUTING_SPEC.md`
5. API — `CRR_API_CONTRACT.md`
6. Reference architecture — `SYSTEM_DESIGN.md`
7. Data flow — `CRR_DATA_FLOW_ARCHITECTURE.md`
8. Cross-document clarifications — `CRR_NORMATIVE_AMENDMENT_0.1.1.md` and `CRR_NORMATIVE_AMENDMENT_0.1.2.md` where they explicitly apply

---

# 26. Repository status

This repository contains the **protocol and architecture specification foundation** plus an in-progress Phase 1 executable reference foundation. Phase 1 currently covers a narrow organization/actor/location/resource/ResourceState API. It does not yet implement routing, commercial execution, evidence verification, or a complete end-to-end transaction.

The specification remains authoritative for implementation semantics. The current code should be judged on:

- semantic completeness;
- internal consistency;
- precise domain boundaries;
- deterministic invariants;
- interoperability;
- implementation clarity;
- security and authorization boundaries;
- reproducibility;
- conformance definitions.

The presence of a complete specification does **not** imply that a production implementation already exists.

---

# 27. Definition of success

CRR is successful when an independent implementation team can read this repository and build a compatible system without needing undocumented assumptions about:

- what a resource is;
- what a resource state is;
- how physical changes are represented;
- how routes are generated and rejected;
- how hard constraints work;
- how capacity is reserved;
- how economics are computed;
- where AI/Jev is allowed;
- how commercial commitments differ from physical execution;
- how evidence becomes verification;
- how events remain auditable;
- how APIs preserve invariants;
- how tenants and permissions are isolated;
- what conformance means.

That is the standard this repository is intended to meet.

# Phase 1 Reference Foundation

The first executable increment covers tenant-scoped organizations and actors, locations, resources, immutable ResourceState history, authenticated REST access, optimistic concurrency, idempotency, and a transactional event outbox. It does not yet implement route discovery or commercial execution.

From the repository root, install the package and start the API:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
crr-bootstrap --organization-id org_factory_a --organization-name "Factory A" --actor-id act_admin --actor-name "Factory A Admin"
python -m uvicorn crr.api:app --reload
```

The bootstrap command applies Alembic migrations, creates the initial organization administrator, stores only a hash of the generated API key, and prints the secret once. Set `CRR_DATABASE_URL` before starting either command to select PostgreSQL or another configured SQLAlchemy database.
