# CRR Domain Model

**Status:** Canonical domain model specification  
**Version:** 0.1  
**Protocol:** Computational Resource Routing (CRR)  
**Role:** Defines the canonical objects, relationships, semantics, lifecycle states, identity rules, and epistemic distinctions used throughout CRR.

> CRR is a proposed protocol/category specification. This document defines the project's canonical domain model; it does not claim that CRR is an existing external standard.

---

# 1. Domain model purpose

The CRR domain model exists to represent the physical economy as a set of authoritative entities and relationships that can be validated, routed, transacted, executed, and verified.

The central design decision is:

> **ResourceState is the fundamental physical primitive. Resource is the stable identity and lineage container.**

The domain must therefore distinguish:

```text
IDENTITY
   ↓
PHYSICAL STATE
   ↓
CAPABILITY / TRANSFORMATION
   ↓
ROUTE
   ↓
COMMERCIAL COMMITMENT
   ↓
EXECUTION
   ↓
EVIDENCE
   ↓
VERIFIED OUTCOME
```

---

# 2. Canonical object inventory

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

These objects form the minimum canonical vocabulary.

Additional implementation objects such as jobs, API keys, webhook subscriptions, projections, caches, embeddings, or UI models may exist, but they are not allowed to redefine canonical physical semantics.

---

# 3. Domain graph

```text
Organization
 ├─ owns → Resource
 ├─ creates → Demand
 ├─ provides → Capability
 ├─ performs → Transformation
 └─ participates in → Transaction

Resource
 └─ has → ResourceState

ResourceState
 ├─ has → Location
 ├─ has → Quantity
 ├─ has → Quality
 └─ has → Provenance

Capability
 └─ enables → Transformation

Transformation
 ├─ consumes → ResourceState specification
 └─ produces → ResourceState specification

Route
 ├─ starts from → ResourceState
 ├─ contains → RouteLeg
 └─ terminates at → Demand / target state

Decision
 └─ evaluates → Candidate routes/options

Opportunity
 └─ proposes → Route

Offer
 └─ proposes → Opportunity terms

Agreement
 └─ records → Accepted terms

Transaction
 ├─ executes → Opportunity / Agreement
 └─ references → Resource + Route

Execution
 └─ records → Actual operations

Evidence
 └─ supports/verifies → Claims about states/events/execution

EconomicModel
 └─ calculates → Value/cost outcome

Event
 └─ records → Protocol state change or material observation
```

---

# 4. Common object metadata

Every canonical object SHOULD contain the following conceptual metadata where applicable:

- stable ID;
- object type;
- schema version;
- object/revision version;
- lifecycle status;
- owning organization or authority;
- created timestamp;
- updated timestamp;
- creator/actor;
- provenance;
- metadata/extensions.

Not every field is semantically applicable to every object. The protocol must not add meaningless fields merely for uniformity.

---

# 5. Organization

An Organization represents a participating legal, commercial, operational, governmental, or other authorized entity.

## 5.1 Responsibilities

An organization may:

- own resources;
- create demands;
- register capabilities;
- define transformations;
- participate in transactions;
- provide evidence;
- verify evidence if authorized;
- integrate external systems.

## 5.2 Core concepts

An organization has:

- stable identity;
- legal/display identity;
- operating status;
- jurisdiction metadata;
- authorized actors;
- access policies;
- provenance.

## 5.3 Ownership rule

Ownership and operational custody are distinct concepts. An organization may control a resource without being the ultimate legal owner, subject to the relevant implementation/policy model.

---

# 6. Actor

An Actor represents a human or service identity acting within an organization or authorized system context.

Actors are used for:

- authentication;
- authorization;
- attribution;
- approvals;
- verification;
- audit history;
- machine-to-machine operations.

An Actor cannot grant itself permissions merely by supplying an organization identifier.

---

# 7. Location

Location represents a physical place relevant to the resource network.

It can describe:

- resource origin;
- storage location;
- facility;
- processing site;
- pickup location;
- delivery location;
- inspection site;
- capability location.

A location may contain:

- coordinates;
- address information;
- jurisdiction;
- location type;
- provenance;
- uncertainty/precision information.

Coordinates must be valid when supplied. Location uncertainty must be explicit where it materially affects routing.

---

# 8. Resource

A Resource is a stable identity and lineage container.

It is intentionally **not** the complete representation of physical reality.

A Resource can represent the continuing identity of a material or physical lineage while multiple ResourceStates represent its changing physical condition.

Conceptual fields include:

- resource ID;
- resource type/classification;
- description;
- origin;
- owner;
- current state reference;
- lineage metadata;
- provenance;
- status.

A Resource with historical states must not be deleted in a way that destroys physical history.

---

# 9. ResourceState

`ResourceState` is the most important object in CRR.

It represents a particular physical state at a point or interval in time.

Conceptual fields include:

- `resource_id`;
- state/material classification;
- quantity;
- unit;
- physical properties;
- quality;
- location;
- ownership/custody;
- availability window;
- condition;
- effective time;
- provenance;
- evidence references;
- predecessor state references;
- balance/lineage information;
- lifecycle status.

## 9.1 State semantics

A state is not simply a row that can be overwritten whenever the resource changes.

Material physical changes create new states or equivalent versioned history.

For example:

```text
100 t MIXED_ALUMINUM_SCRAP
       ↓ sorting
92 t CLEAN_ALUMINUM_SCRAP
       ↓ melting
88 t MOLTEN_ALUMINUM
       ↓ casting
86 t ALUMINUM_BILLET
```

The protocol must retain the relationships between these states and the declared losses/residuals.

---

# 10. ResourceState lineage

Lineage supports:

- split;
- merge;
- transformation;
- external origin;
- correction;
- consumption;
- partial fulfillment.

A child state must reference its predecessor lineage unless it is explicitly introduced from an external origin.

### Split

```text
PARENT
 ├── CHILD A
 ├── CHILD B
 └── CHILD C
```

### Merge

```text
A ─┐
B ─┼→ CHILD
C ─┘
```

The applicable quantity balance must reconcile.

---

# 11. Demand

Demand describes what a participant needs and the conditions under which it will accept a resource state.

Core concepts:

- organization;
- required state specification;
- quantity minimum/target/maximum;
- quality requirements;
- location constraints;
- timing window;
- pricing constraints;
- certifications;
- regulatory constraints;
- substitutions;
- recurrence;
- remaining quantity;
- lifecycle state.

## 11.1 Demand status

```text
DRAFT
  ↓
ACTIVE
  ↓
PAUSED
  ↓
ACTIVE

ACTIVE → FULFILLED
ACTIVE → EXPIRED
ACTIVE → CANCELLED
ACTIVE → DISPUTED
```

Only active demand is eligible for ordinary routing.

---

# 12. Capability

Capability describes what an organization can physically do.

It can represent:

- material acceptance;
- processing;
- transformation;
- storage;
- inspection;
- logistics;
- handling;
- specialized services.

Core concepts:

- organization;
- accepted inputs;
- output specifications;
- transformation references;
- capacity;
- operating windows;
- minimum batch;
- location;
- processing cost;
- certifications;
- regulatory eligibility;
- status;
- provenance.

## 12.1 Capability status

```text
DRAFT
 ↓
ACTIVE
 ↓
SUSPENDED / EXPIRED / REVOKED
```

A revoked or expired capability cannot be selected for execution.

---

# 13. Transformation

A Transformation defines a permitted relationship between input and output states.

It is a reusable process definition rather than an execution record.

It should specify:

1. accepted inputs;
2. output specifications;
3. process;
4. yield bounds;
5. loss/residual semantics;
6. capacity;
7. duration;
8. cost;
9. energy or auxiliary requirements where relevant;
10. quality effects;
11. regulatory requirements;
12. eligible capabilities/locations.

A transformation definition does not prove that a physical transformation happened.

---

# 14. Route

A Route is an ordered plan connecting a source ResourceState to a target Demand or state.

It contains route legs.

Supported conceptual legs:

- `TRANSPORT`;
- `TRANSFORMATION`;
- `STORAGE`;
- `INSPECTION`;
- `TRANSFER`;
- extension-defined types.

Every leg has expected input/output semantics.

Example:

```text
S1: Mixed Scrap
  ↓ TRANSPORT
Facility B
  ↓ TRANSFORMATION
S2: Sorted Scrap
  ↓ TRANSPORT
Buyer C
```

A route is not proof of execution.

---

# 15. Decision

A Decision records reasoning over a fixed candidate set.

Conceptual fields:

- decision ID;
- decision type;
- context hash;
- candidate IDs;
- authoritative constraints;
- selected option;
- rationale;
- confidence;
- uncertainty;
- evidence references;
- provider;
- model/version;
- deterministic validation result;
- escalation requirement;
- status.

A Decision cannot create canonical physical facts.

---

# 16. Opportunity

Opportunity represents a commercially actionable possibility derived from a feasible route.

It connects:

```text
RESOURCE
 +
ROUTE
 +
DEMAND
 +
CAPABILITY
 +
PARTICIPANTS
 +
ECONOMICS
 +
REQUIREMENTS
```

Lifecycle:

```text
DISCOVERED
   ↓
VALIDATING
   ↓
PROPOSED
   ↓
APPROVED / REJECTED / EXPIRED
```

An Opportunity is not a transaction.

---

# 17. Offer

An Offer contains proposed commercial terms.

Core concepts:

- opportunity;
- proposer;
- recipient;
- quantity;
- price;
- currency;
- delivery terms;
- timing;
- route assumptions;
- conditions;
- expiration;
- status.

An offer is a proposal, not proof of acceptance or execution.

---

# 18. Agreement

Agreement records accepted commercial terms and obligations.

It may reference:

- one or more offers;
- external contracts;
- transaction terms;
- evidence requirements;
- delivery conditions;
- payment terms;
- acceptance conditions.

External legal enforceability depends on applicable law and contractual context. CRR records protocol-level commercial state.

An Agreement is not execution evidence.

---

# 19. Transaction

Transaction connects the accepted commercial arrangement to physical resource movement and execution.

It may contain:

- agreement;
- opportunity;
- resource references;
- route;
- quantity;
- price;
- obligations;
- execution reference;
- evidence requirements;
- economic model;
- status.

Reference lifecycle:

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

`COMPLETED` means the protocol considers the transaction execution complete. `VERIFIED` means the required evidence has been accepted.

---

# 20. Execution

Execution records actual operations.

It contains:

- transaction reference;
- ordered steps;
- responsible parties;
- planned timestamps;
- actual timestamps;
- planned quantities;
- actual quantities;
- statuses;
- exceptions;
- evidence references.

Execution must distinguish planned from actual values.

Partial execution must remain explicitly partial.

---

# 21. Evidence

Evidence is an attributable artifact or observation supporting a claim.

Potential evidence types include:

- weighbridge record;
- laboratory report;
- inspection report;
- pickup record;
- shipment record;
- delivery receipt;
- processing record;
- buyer acceptance;
- output measurement.

Conceptual fields:

- evidence ID;
- type;
- subject reference;
- issuer;
- submitter;
- capture timestamp;
- content reference;
- content hash;
- verification status;
- verifier;
- verification timestamp;
- supported claims.

Lifecycle:

```text
CLAIMED
  ↓
SUBMITTED
  ↓
VERIFIED
```

Alternative terminal outcomes:

```text
SUBMITTED → REJECTED
SUBMITTED → DISPUTED
```

---

# 22. EconomicModel

EconomicModel represents reproducible calculations.

It may contain:

- currency;
- gross value;
- supplier value;
- buyer payment;
- processing cost;
- transport cost;
- handling cost;
- certification cost;
- taxes/fees;
- other components;
- assumptions;
- calculation version;
- source references;
- computed timestamp;
- net outcome.

The calculation must be reproducible from stored inputs and rules.

---

# 23. Event

An Event is an immutable record of a protocol state change or material observation.

Recommended fields:

- event ID;
- event type;
- event version;
- occurrence timestamp;
- aggregate type;
- aggregate ID;
- aggregate version;
- actor;
- organization;
- correlation ID;
- causation ID;
- idempotency key where applicable;
- payload;
- provenance;
- schema version.

Events must not be used as a mutable shadow database that contradicts canonical state.

---

# 24. Lifecycle state machines

## 24.1 ResourceState

```text
DRAFT
  ↓
ACTIVE
  ↓
RESERVED
  ↓
IN_TRANSIT
  ↓
RECEIVED
  ↓
PROCESSING
  ↓
TRANSFORMED
  ↓
CONSUMED / COMPLETED
```

Exceptions:

```text
CANCELLED
DISPUTED
```

Not every state transition applies to every resource type.

## 24.2 Demand

```text
DRAFT
  ↓
ACTIVE
  ↓
PAUSED ↔ ACTIVE
  ↓
FULFILLED / EXPIRED / CANCELLED / DISPUTED
```

## 24.3 Capability

```text
DRAFT → ACTIVE → SUSPENDED / EXPIRED / REVOKED
```

## 24.4 Opportunity

```text
DISCOVERED → VALIDATING → PROPOSED → APPROVED
                                      ↘ REJECTED
                                      ↘ EXPIRED
```

## 24.5 Evidence

```text
CLAIMED → SUBMITTED → VERIFIED
                   ↘ REJECTED
                   ↘ DISPUTED
```

## 24.6 Decision

```text
REQUESTED → EVALUATING → GENERATED → VALIDATED
                                      ↓
                           ACCEPTED / REJECTED / ESCALATED
```

---

# 25. Identity rules

Every canonical object must have:

- stable identity;
- explicit type;
- schema version;
- object version where mutable;
- provenance;
- timestamps appropriate to its semantics.

IDs should be opaque.

Reference prefixes such as `res_`, `rst_`, `dem_`, `cap_`, `trn_`, `rte_`, `txn_`, and `evd_` are implementation conventions, not required semantic meanings.

---

# 26. Ownership and custody

Ownership and custody must be distinguishable.

Examples:

```text
LEGAL OWNER
     ↓
OPERATIONAL CUSTODIAN
     ↓
PHYSICAL LOCATION
```

A route requiring authority over a resource cannot execute when the relevant ownership/custody permission is unresolved.

---

# 27. Quantity and precision

Quantities use exact decimal semantics.

Example conceptual representation:

```json
{
  "quantity": {
    "value": "100.000",
    "unit": "t"
  }
}
```

Binary floating-point must not be the authoritative representation.

---

# 28. Quality model

Quality is resource-specific and may include:

- composition;
- grade;
- purity;
- contamination;
- moisture;
- temperature;
- dimensions;
- calorific value;
- concentration;
- mechanical properties.

A quality value should retain its unit, measurement method/source, timestamp, and evidence where material.

Unknown quality is not verified quality.

---

# 29. Provenance model

Conceptual provenance:

```json
{
  "source_type": "MANUAL | FILE | API | SYSTEM | EXTERNAL",
  "source_id": "...",
  "source_record_id": "...",
  "captured_at": "...",
  "captured_by": "...",
  "method": "..."
}
```

Confidence may be recorded, but confidence does not replace verification.

---

# 30. Derived versus canonical domain data

Canonical:

- resource states;
- demands;
- capabilities;
- transformation definitions;
- transactions;
- verified evidence;
- protocol events.

Derived:

- graph projections;
- embeddings;
- search indexes;
- route scores;
- rankings;
- analytics aggregates;
- UI projections.

Derived objects are rebuildable and must not become the sole source of physical truth.

---

# 31. Planned, actual, claimed, verified

The domain explicitly separates:

| Category | Meaning |
|---|---|
| Planned | Intended future value |
| Actual | Observed value during execution |
| Claimed | Submitted assertion |
| Verified | Evidence-backed accepted fact |

This distinction is required because a planned route can fail, an actual observation can be wrong, a claim can be disputed, and evidence can be rejected.

---

# 32. Cross-object consistency rules

The domain model requires:

1. every ResourceState references a valid Resource;
2. every Demand references a valid organization;
3. every Capability references a valid organization;
4. every Transformation has valid input/output specifications;
5. every Route references a valid source and target;
6. every Decision references an auditable candidate set;
7. every Opportunity references a valid route;
8. every Offer references a valid opportunity;
9. every Agreement references accepted terms;
10. every Transaction references valid commercial state;
11. every Execution references a transaction;
12. every Evidence references an existing subject;
13. every Event references a valid aggregate where required;
14. every verified outcome has required evidence.

---

# 33. Domain invariants

The complete invariant registry is maintained in `CRR_VALIDATION_AND_INVARIANTS.md`. The core domain invariants are:

- no negative physical quantity;
- no ambiguous unit;
- no broken lineage;
- no silent physical history overwrite;
- no route from invalid source state;
- no route through inactive demand;
- no route through revoked capability;
- no transformation beyond declared yield bounds;
- no capacity overcommitment;
- no hard-constraint bypass;
- no AI-created physical fact;
- no transaction from invalid commercial state;
- no execution treated as verification;
- no unverified evidence treated as verified;
- no cross-tenant access;
- no duplicate event effect;
- no derived projection overriding canonical state.

---

# 34. Reference end-to-end object chain

```text
Organization A
    ↓ owns
Resource R1
    ↓ has
ResourceState S1
    ↓ evaluated against
Demand D1
    ↓ requires
Capability C1
    ↓ enables
Transformation T1
    ↓ produces
ResourceState S2
    ↓ participates in
Route RTE1
    ↓ evaluated by
Decision DEC1
    ↓ produces
Opportunity O1
    ↓ produces
Offer OFF1
    ↓ accepted into
Agreement AGR1
    ↓ creates
Transaction TXN1
    ↓ executed by
Execution EXE1
    ↓ produces
Evidence EVD1
    ↓ verified into
Verified Outcome
    ↓ emits
Event EVT1
```

This chain is the domain-level representation of the complete CRR loop.

---

# 35. Protocol/domain separation

The domain model defines semantics, not infrastructure.

It does not require:

- PostgreSQL;
- a graph database;
- FastAPI;
- React;
- Python;
- Redis;
- Celery;
- Jev;
- a specific cloud.

An implementation may use any technology that preserves these domain semantics.

---

# 36. Relationship to other documents

- `CRR_PROTOCOL_SPEC.md` defines protocol meaning.
- `CRR_DOMAIN_MODEL.md` defines canonical domain objects and relationships.
- `SYSTEM_DESIGN.md` maps these concepts into a reference system.
- `CRR_DATA_FLOW_ARCHITECTURE.md` defines how data moves between them.
- `CRR_DECISION_AND_ROUTING_SPEC.md` defines route and decision computation.
- `CRR_API_CONTRACT.md` defines externally observable API behavior.
- `CRR_VALIDATION_AND_INVARIANTS.md` defines enforcement rules.

The domain model is the bridge between protocol semantics and implementation.

---

# 37. Final domain principle

> **CRR models the physical economy as evolving resource states connected by capabilities, transformations, routes, commercial commitments, execution records, evidence, and verified outcomes.**

The domain model must preserve the difference between identity, physical state, possibility, plan, agreement, execution, claim, and verified reality.
