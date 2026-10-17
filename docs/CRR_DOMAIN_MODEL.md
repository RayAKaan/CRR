# CRR Domain Model

**Status:** Canonical domain model specification
**Version:** 0.1

## 1. Domain graph

```text
Organization
 ├─ owns → Resource
 ├─ creates → Demand
 ├─ provides → Capability
 ├─ performs → Transformation
 └─ participates in → Transaction

Resource
 └─ has → ResourceState

Transformation
 ├─ consumes → ResourceState specification
 └─ produces → ResourceState specification

Route
 ├─ starts from → ResourceState
 └─ terminates at → Demand / target state

Opportunity
 └─ proposes → Route

Transaction
 └─ executes → Opportunity

Execution
 └─ produces → Evidence

Evidence
 └─ verifies → state/event/transaction claims

Event
 └─ records → protocol change

Decision
 └─ records → selection reasoning
```

## 2. Organization

Represents a participating legal or operational entity. It is the principal boundary for ownership, authorization and commercial participation.

Required concepts:

- stable identity
- legal/display identity
- operating status
- jurisdiction metadata
- authorized actors
- provenance

## 3. Actor

Represents a human or service identity acting for an organization. Authorization is evaluated against organization, actor and scope.

## 4. Location

Represents a physical location used for resources, capabilities, processing, storage or delivery. Coordinates and address data must be valid and provenance-aware.

## 5. Resource

Resource is the stable identity and lineage container. It should not be used as a substitute for physical state.

A resource can have multiple states over its lifecycle.

## 6. ResourceState

ResourceState is the fundamental physical primitive.

It includes:

- resource reference
- state/material classification
- quantity and unit
- physical properties
- quality
- location
- ownership/custody
- availability
- effective time
- provenance
- evidence references
- predecessor lineage

Historical physical states MUST NOT be destructively rewritten.

## 7. Demand

Demand describes a required state and the conditions under which a participant will accept it.

Core fields:

- organization
- required state
- quantity
- quality
- location
- time window
- pricing
- certifications
- regulatory constraints
- substitutions
- lifecycle status

## 8. Capability

Capability describes what an organization can do.

It references accepted inputs, transformations, outputs, capacity, operating windows, location, costs, certifications and regulatory eligibility.

## 9. Transformation

Transformation defines a valid state transition. It is versioned and testable.

A transformation must declare its input specification, output specification, yield bounds, loss/residual semantics, duration, capacity, cost and applicable requirements.

## 10. Route

Route is an ordered plan consisting of transport and transformation legs.

Supported leg types include:

- `TRANSPORT`
- `TRANSFORMATION`
- `STORAGE`
- `INSPECTION`
- `TRANSFER`
- `OTHER` as an extension where explicitly defined

A route is not evidence of execution.

## 11. Decision

Decision records how candidate routes or options were selected.

It includes decision type, context hash, candidates, constraints, selected option, rationale, confidence, uncertainty, evidence references, provider/model information and escalation status.

## 12. Opportunity

Opportunity represents a commercially actionable possibility derived from a route.

It is not yet a binding transaction.

## 13. Offer

Offer expresses proposed commercial terms such as quantity, price, timing, route and conditions.

## 14. Agreement

Agreement records accepted commercial terms and obligations. External legal enforceability may depend on jurisdiction and external documents; CRR records the protocol-level state.

## 15. Transaction

Transaction connects an accepted commercial arrangement to the resource and execution plan.

It maintains planned, actual and verified values separately.

## 16. Execution

Execution is the operational record of carrying out a transaction.

It contains ordered steps, responsible parties, planned/actual timestamps, quantities, exceptions and evidence references.

## 17. Evidence

Evidence is an attributable artifact or observation supporting a claim.

Evidence requires issuer/submitter, capture time, subject reference, content reference/hash and verification status.

## 18. EconomicModel

Represents reproducible value and cost calculations, including currency, assumptions, components, calculation version and computed outcome.

## 19. Event

Event is an immutable record of a protocol state change or material observation.

## 20. Lifecycle states

### ResourceState

`DRAFT → ACTIVE → RESERVED → IN_TRANSIT → RECEIVED → PROCESSING → TRANSFORMED → CONSUMED → COMPLETED`

Terminal/exception states include `CANCELLED` and `DISPUTED` where applicable.

### Demand

`DRAFT → ACTIVE → PAUSED → FULFILLED | EXPIRED | CANCELLED | DISPUTED`

### Capability

`DRAFT → ACTIVE → SUSPENDED | EXPIRED | REVOKED`

### Opportunity

`DISCOVERED → VALIDATING → PROPOSED → APPROVED | REJECTED | EXPIRED`

### Evidence

`CLAIMED → SUBMITTED → VERIFIED | REJECTED | DISPUTED`

### Decision

`REQUESTED → EVALUATING → GENERATED → VALIDATED → ACCEPTED | REJECTED | ESCALATED`

## 21. Identity and metadata

Every canonical object MUST have a stable identifier, schema version, object version, provenance and timestamps appropriate to the object.

## 22. Precision

Quantities and economic values use exact decimal semantics. Binary floating-point values are not authoritative.

## 23. Planned versus actual versus verified

The domain model deliberately separates:

- planned values;
- actual observations;
- submitted claims;
- verified facts.

A planned quantity MUST NOT be presented as actual. An actual observation MUST NOT automatically become verified.
