# CRR Protocol Specification

**Status:** Proposed normative protocol specification  
**Version:** 0.1  
**Protocol name:** Computational Resource Routing (CRR)  
**Authority:** Protocol semantics for conforming CRR implementations

> **Important:** CRR is a proposed technical/category specification created by this project. It is not an existing external global standard. This document defines the semantics of the proposed protocol.

---

## 1. Purpose and scope

CRR defines an implementation-independent protocol for representing, discovering, routing, transforming, trading, executing, and verifying physical-resource flows across organizational and industrial boundaries.

The protocol exists because physical-resource routing cannot be reduced to text search or simple marketplace matching. A valid route depends on:

- what physically exists;
- quantity and unit;
- physical state;
- quality;
- location;
- ownership/custody;
- demand;
- processing capability;
- transformation rules;
- capacity;
- timing;
- logistics;
- regulation and safety;
- economics;
- evidence;
- commercial agreement;
- actual execution.

CRR defines the semantics that allow those facts to be represented and reasoned over without allowing derived computation or AI output to become authoritative physical truth.

---

# 2. Normative language

The following terms are normative:

- **MUST** — mandatory for conformance.
- **MUST NOT** — prohibited.
- **SHOULD** — strongly recommended unless a documented reason exists.
- **SHOULD NOT** — normally avoided unless documented.
- **MAY** — optional.

An implementation is conforming only if its observable behavior preserves the mandatory semantics, regardless of technology choice.

---

# 3. Core protocol thesis

The fundamental physical primitive is **ResourceState**, not waste.

```text
RESOURCE IDENTITY
       ↓
RESOURCE STATE
       ↓
TRANSFORMATION
       ↓
NEW RESOURCE STATE
```

A Resource represents stable identity and lineage. A ResourceState represents a particular physical condition.

The protocol therefore asks:

> What is the highest-value physically, operationally, economically, and legally/safely feasible route by which a resource can reach another useful state?

It does not merely ask who wants a material.

---

# 4. Protocol architecture

```text
PHYSICAL ECONOMY
       ↓
RESOURCE / DEMAND / CAPABILITY REALITY
       ↓
RESOURCE GRAPH
       ↓
TRANSFORMATION GRAPH
       ↓
ROUTING ENGINE
       ↓
DETERMINISTIC VALIDATION
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
EVIDENCE
       ↓
VERIFIED OUTCOME
       ↓
NETWORK LEARNING
```

The protocol separates canonical reality from derived computation at every layer.

---

# 5. Canonical objects

The canonical domain vocabulary is:

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

An implementation may introduce additional objects, but extensions must not silently redefine these canonical semantics.

---

# 6. Object relationships

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

Opportunity proposes Route
Transaction executes Opportunity
Execution produces Evidence
Evidence verifies claims about state/events/execution/transactions
Decision records selection reasoning
Event records protocol changes
```

These relationships are semantic. A particular database schema is not mandated.

---

# 7. Resource semantics

A `Resource` is a stable identity and lineage container.

A `ResourceState` is the authoritative representation of a particular physical state and includes, where applicable:

- material/state classification;
- quantity;
- unit;
- physical properties;
- quality;
- location;
- ownership/custody;
- availability;
- effective time;
- provenance;
- evidence references;
- predecessor lineage.

Historical physical facts MUST NOT be destructively overwritten.

If a resource changes materially, the implementation MUST represent that change through a new state, version, event, or equivalent auditable mechanism.

---

# 8. Quantity semantics

Authoritative physical quantities MUST use exact decimal semantics.

Binary floating-point representations MUST NOT be the authoritative representation of physical quantities.

A quantity consists conceptually of:

```text
VALUE + UNIT + CONTEXT
```

Context may be required for conversions involving:

- density;
- temperature;
- pressure;
- moisture;
- concentration;
- purity;
- other resource-specific conditions.

Ambiguous units MUST be rejected.

Unit conversions MUST be explicit, versioned, and reproducible.

---

# 9. Money semantics

Authoritative monetary values MUST use exact decimal semantics or integer minor units.

A money value must identify:

- amount;
- currency;
- calculation context where applicable.

Economic calculations must preserve whether a value represents:

- revenue;
- purchase/payment;
- transport cost;
- processing cost;
- handling cost;
- certification cost;
- taxes/fees;
- other value/cost components.

Rounding MUST NOT convert an economically negative result into a positive result.

---

# 10. Provenance

Every canonical externally sourced physical fact MUST have provenance sufficient to answer:

1. where did the fact originate?
2. who supplied or captured it?
3. when was it captured?
4. by what method?
5. what source record supports it?
6. what transformations occurred before canonicalization?

Provenance is not equivalent to verification. A claim can have excellent provenance and still remain unverified.

---

# 11. Lineage

CRR MUST preserve physical lineage.

For a split:

```text
PARENT
 ├── CHILD A
 ├── CHILD B
 └── CHILD C
```

The applicable balance equation must reconcile the parent quantity with child quantities plus explicitly declared losses/residuals within an explicit tolerance.

For a merge:

```text
A ─┐
B ─┼→ CHILD
C ─┘
```

The parent states must be compatible according to the merge policy.

The protocol MUST NOT silently create or destroy physical quantity.

---

# 12. Transformation semantics

A transformation is a versioned declaration of a permitted state change.

It defines, as applicable:

- accepted input state specifications;
- output state specifications;
- process definition;
- yield bounds;
- loss/residual model;
- capacity;
- duration;
- cost;
- energy/resource requirements;
- quality effects;
- regulatory requirements;
- eligible locations/capabilities.

A transformation definition is not proof that the transformation occurred.

Actual transformation requires an execution record and appropriate evidence.

---

# 13. Demand semantics

Demand describes what an organization or participant needs and the conditions under which it will accept a resource state.

A demand may specify:

- required state;
- quantity range;
- quality requirements;
- location constraints;
- availability/delivery window;
- price constraints;
- certification requirements;
- regulatory requirements;
- substitution rules;
- recurrence;
- remaining quantity.

Only active demand can normally participate in routing.

---

# 14. Capability semantics

Capability represents what an organization can physically do.

It may specify:

- accepted inputs;
- transformations;
- outputs;
- capacity;
- minimum batch;
- operating windows;
- location;
- processing costs;
- certifications;
- regulatory eligibility.

The routing system MUST distinguish theoretical capability from currently available capacity.

---

# 15. Route semantics

A Route is a proposed executable sequence of transport and transformation legs.

Supported conceptual leg types include:

- `TRANSPORT`;
- `TRANSFORMATION`;
- `STORAGE`;
- `INSPECTION`;
- `TRANSFER`;
- explicitly defined extensions.

A route MUST:

1. start from a valid source ResourceState;
2. terminate at a valid Demand or target state;
3. contain ordered legs;
4. maintain state compatibility between legs;
5. satisfy hard constraints;
6. respect capacity;
7. respect time windows;
8. expose relevant logistics assumptions;
9. expose economic assumptions/results;
10. expose regulatory/safety results where applicable;
11. have a validity/expiry boundary;
12. remain distinguishable from actual execution.

A route is never proof that the physical operation occurred.

---

# 16. Hard constraints

Hard constraints are deterministic blockers.

Examples include:

- insufficient quantity;
- invalid unit conversion;
- incompatible state;
- incompatible quality;
- unavailable capability;
- insufficient capacity;
- impossible timing;
- impossible logistics;
- expired demand;
- revoked certification;
- missing required authorization;
- prohibited material/process combination;
- ownership/custody conflict;
- impossible transformation yield;
- required evidence missing before an execution step.

A route that violates a hard constraint MUST be infeasible regardless of score, model confidence, or AI recommendation.

---

# 17. Routing semantics

Routing is a layered process:

```text
CANDIDATE DISCOVERY
       ↓
HARD CONSTRAINTS
       ↓
PHYSICAL FEASIBILITY
       ↓
CAPACITY / TIME
       ↓
LOGISTICS
       ↓
TRANSFORMATION FEASIBILITY
       ↓
REGULATORY / SAFETY
       ↓
ECONOMICS
       ↓
OPTIMIZATION
       ↓
DECISION SUPPORT
```

Optimization operates only over feasible candidates.

A route score is comparative, not authoritative.

---

# 18. Economic semantics

Economic calculations are deterministic and auditable.

A reference model may calculate:

```text
VALUE / PAYMENT
- TRANSPORT
- PROCESSING
- HANDLING
- CERTIFICATION
- TAXES / FEES
- OTHER COSTS
= NET ECONOMIC OUTCOME
```

The exact model may vary by transaction, but every result must retain its inputs, assumptions, currency, calculation version, and timestamp.

A negative result remains negative. Economic feasibility is a policy/objective decision applied to a deterministic calculation.

---

# 19. Decision semantics

A `Decision` records bounded reasoning over a fixed candidate set and authoritative context.

A decision request contains, conceptually:

- decision type;
- candidate IDs;
- constraints;
- evidence references;
- economic context;
- uncertainties;
- allowed action space.

A decision result contains:

- selected candidate;
- rationale;
- confidence;
- uncertainty;
- evidence references;
- provider/model/version;
- validation result;
- escalation status.

The selected candidate MUST belong to the original candidate set and MUST pass deterministic validation.

Confidence is not proof.

Rationale is explanatory, not canonical physical truth.

---

# 20. Jev semantics

Jev is an optional decision provider behind a stable provider interface.

Recommended abstraction:

```text
DecisionProvider
      ↓
JevProvider
```

Jev may assist with:

- semantic compatibility;
- ambiguous classification;
- candidate prioritization;
- contextual tradeoffs;
- qualitative interpretation;
- escalation;
- explanations.

Jev MUST NOT:

- override hard constraints;
- invent quantities;
- invent capabilities;
- create capacity;
- invent regulatory permission;
- fabricate evidence;
- directly mutate canonical physical state;
- directly execute commercial transactions;
- establish verification merely through model output.

The system MUST remain operational when Jev is unavailable. Ambiguous decisions can fall back to deterministic rules or human escalation.

---

# 21. Opportunity semantics

An Opportunity represents a commercially actionable possibility derived from a route.

It may contain:

- route reference;
- source/target participants;
- resource information;
- economics;
- requirements;
- confidence;
- decision reference;
- expiry;
- evidence references.

An Opportunity is not a binding transaction.

---

# 22. Offer semantics

An Offer expresses proposed commercial terms.

At minimum, applicable offers identify:

- proposer;
- recipient;
- quantity;
- price/currency;
- timing;
- route/delivery assumptions;
- conditions;
- expiry.

An offer is not evidence of physical delivery.

---

# 23. Agreement semantics

An Agreement records accepted commercial terms and obligations.

It may reference external legal documents because legal enforceability depends on jurisdiction and external contract law.

CRR records the protocol-level state and relationships; it does not claim that a protocol record alone determines every legal question.

An agreement does not prove physical execution.

---

# 24. Transaction semantics

A Transaction connects an accepted commercial arrangement to physical resources and execution.

The reference lifecycle is:

```text
DISCOVERED
    ↓
PROPOSED
    ↓
ACCEPTED
    ↓
AGREED
    ↓
SCHEDULED
    ↓
EXECUTING
    ↓
COMPLETED
    ↓
VERIFIED
```

The semantic distinction between `COMPLETED` and `VERIFIED` MUST be preserved.

---

# 25. Execution semantics

Execution records what actually happens operationally.

It may contain:

- ordered steps;
- responsible parties;
- planned timestamps;
- actual timestamps;
- planned quantities;
- actual quantities;
- exceptions;
- partial completion;
- evidence references.

Execution MUST NOT silently rewrite the original plan.

---

# 26. Evidence semantics

Evidence is an attributable artifact or observation supporting a claim.

Evidence should identify:

- evidence ID;
- type;
- subject object/state/event;
- issuer;
- submitter;
- capture time;
- content reference;
- content hash where applicable;
- verification state;
- verifier;
- verification time;
- claims supported.

Evidence lifecycle:

```text
CLAIMED → SUBMITTED → VERIFIED
                   ↘ REJECTED
                   ↘ DISPUTED
```

Clients MUST NOT self-assign `VERIFIED` without the required authority and process.

---

# 27. Event semantics

Events are immutable protocol records.

Recommended event envelope:

```json
{
  "event_id": "evt_123",
  "event_type": "resource.state.created",
  "event_version": 1,
  "occurred_at": "2026-10-17T12:34:56Z",
  "aggregate_type": "resource_state",
  "aggregate_id": "rst_123",
  "aggregate_version": 3,
  "actor": "act_123",
  "organization_id": "org_123",
  "correlation_id": "corr_123",
  "causation_id": "evt_122",
  "idempotency_key": "idem_123",
  "payload": {},
  "schema_version": "0.1"
}
```

Event delivery MAY be at least once. Consumers MUST therefore be idempotent.

Aggregate versions MUST be monotonic where ordering is required.

---

# 28. Event vocabulary

Recommended event types include:

```text
resource.created
resource.updated
resource.state.created
resource.state.transitioned
demand.created
demand.updated
capability.registered
capability.updated
transformation.registered
transformation.updated
route.generated
route.validated
decision.created
decision.accepted
decision.rejected
decision.escalated
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
evidence.rejected
transaction.completed
outcome.verified
```

An implementation may add events through versioned extensions.

---

# 29. State transition rules

State transitions MUST be explicit and validated.

ResourceState reference states include:

```text
DRAFT → ACTIVE → RESERVED → IN_TRANSIT → RECEIVED → PROCESSING → TRANSFORMED → CONSUMED / COMPLETED
```

Exception states can include `CANCELLED` and `DISPUTED` where semantically applicable.

Demand:

```text
DRAFT → ACTIVE → PAUSED → ACTIVE
                    ↓
          FULFILLED / EXPIRED / CANCELLED / DISPUTED
```

Capability:

```text
DRAFT → ACTIVE → SUSPENDED / EXPIRED / REVOKED
```

Opportunity:

```text
DISCOVERED → VALIDATING → PROPOSED → APPROVED / REJECTED / EXPIRED
```

Evidence:

```text
CLAIMED → SUBMITTED → VERIFIED / REJECTED / DISPUTED
```

Decision:

```text
REQUESTED → EVALUATING → GENERATED → VALIDATED → ACCEPTED / REJECTED / ESCALATED
```

Exact object-specific transitions may differ, but invalid transitions MUST be rejected.

---

# 30. Planned, actual, claimed, verified

CRR explicitly distinguishes epistemic states:

| State | Meaning |
|---|---|
| Planned | Intended future action/value |
| Actual | Observed execution value |
| Claimed | Participant assertion |
| Verified | Accepted evidence-backed fact |

A planned quantity MUST NOT be represented as actual.

An actual quantity MUST NOT automatically become verified.

A claim MUST NOT be presented as verified merely because it came through an authenticated client.

---

# 31. API semantics

The protocol does not mandate REST, but the reference implementation exposes canonical resources under `/v1`.

Canonical reference resources include:

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

The API is defined in `CRR_API_CONTRACT.md`.

---

# 32. API mutation semantics

Mutations MUST:

- authenticate the caller;
- authorize the operation;
- enforce tenant scope;
- validate references;
- validate lifecycle transitions;
- enforce protocol invariants;
- support idempotency where retries can repeat effects;
- prevent stale writes through optimistic concurrency or equivalent controls.

Authoritative lifecycle changes SHOULD use explicit transition/action semantics rather than arbitrary status patching.

---

# 33. Data processing model

The conceptual processing lifecycle is:

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
TRANSACTIONAL
 ↓
VERIFIED
```

Raw records must remain traceable. Derived projections must remain regenerable. Evidence must remain attributable.

---

# 34. Security semantics

Conforming implementations MUST enforce:

- authentication for protected operations;
- authorization before disclosure;
- tenant isolation;
- least privilege;
- scoped evidence access;
- protected provider credentials;
- auditability;
- protection of sensitive commercial information.

Cross-organization relationships are explicit and authorized; membership in the CRR network does not imply access to every participant's data.

---

# 35. Extension model

Implementations MAY expose extensions using a namespace such as:

```json
{
  "extensions": {
    "com.example.extension": {}
  }
}
```

Extensions MUST NOT:

- redefine core fields;
- silently change lifecycle semantics;
- bypass validation;
- change the meaning of canonical objects;
- create an alternate incompatible definition of physical truth.

---

# 36. Protocol versioning

Breaking semantic changes require a new major protocol version.

Additive changes SHOULD remain backward compatible.

Schema versions MUST be explicit for canonical objects and events.

Implementations should provide deprecation periods for API versions and must not silently reinterpret existing data.

---

# 37. Conformance levels

### Level 0 — Schema conformance

The implementation supports canonical schemas, IDs, timestamps, precision, and structural validation.

### Level 1 — Reality conformance

Adds ResourceState, provenance, ownership/custody, units, quantity, quality, lineage, demand, and capability semantics.

### Level 2 — Routing conformance

Adds transformations, deterministic feasibility, capacity, logistics, regulatory checks, and reproducible economics.

### Level 3 — Transaction conformance

Adds opportunity, offer, agreement, transaction, execution, and lifecycle semantics.

### Level 4 — Evidence conformance

Adds evidence, verification, disputes, and verified outcomes.

### Level 5 — Network conformance

Adds events, webhooks, interoperability, developer interfaces, and ecosystem semantics.

---

# 38. CRR-MVP-0.1 profile

The first reference MVP should support:

- Organization;
- Actor;
- Location;
- Resource;
- ResourceState;
- Demand;
- Capability;
- Transformation;
- Route;
- Decision;
- Opportunity;
- Offer;
- Agreement;
- Transaction;
- Execution;
- Evidence;
- EconomicModel;
- Event;
- authenticated API;
- tenant isolation;
- human approval;
- one complete verified physical-resource transaction.

The MVP does not require:

- cross-border routing;
- autonomous physical execution;
- principal trading;
- financing;
- insurance;
- dedicated graph database;
- global ontology;
- third-party marketplace ecosystem;
- microservice decomposition.

---

# 39. Failure semantics

Protocol failures must be explicit and machine-readable.

Recommended categories include:

- validation failure;
- authorization failure;
- stale state;
- reference failure;
- insufficient capacity;
- no feasible route;
- economic infeasibility;
- regulatory failure;
- safety failure;
- quality mismatch;
- lineage failure;
- evidence failure;
- transaction conflict;
- partial execution;
- provider timeout;
- Jev unavailable;
- duplicate request;
- event publication failure;
- webhook failure;
- projection stale;
- logistics failure;
- processing yield variance;
- dispute.

Hard constraint failures MUST fail closed.

Jev failures MUST fail safely or escalate.

---

# 40. Protocol invariants

The full validation registry is maintained in `CRR_VALIDATION_AND_INVARIANTS.md`. The fundamental invariants are:

1. No negative physical quantity.
2. No ambiguous unit conversion.
3. No silent physical-history overwrite.
4. No broken lineage.
5. No silent physical quantity creation/destruction.
6. No use of expired demand as active demand.
7. No use of revoked capability.
8. No route violating a hard constraint.
9. No score overriding feasibility.
10. No AI-created physical facts.
11. No AI-created regulatory permission.
12. No direct Jev mutation of canonical truth.
13. No transaction from an invalid commercial state.
14. No execution represented as verification without evidence.
15. No evidence self-verification without authority.
16. No duplicate domain effect from event replay.
17. No cross-tenant disclosure.
18. No stale write silently overwriting current state.
19. No derived projection becoming canonical truth.
20. No irreproducible authoritative economic calculation.

---

# 41. Implementation independence

CRR does not require:

- PostgreSQL;
- PostGIS;
- FastAPI;
- Python;
- React;
- Redis;
- Celery;
- a particular graph database;
- a particular cloud;
- Jev;
- a particular AI model.

These are reference implementation choices.

An independent implementation is valid if it preserves protocol semantics.

---

# 42. Reference implementation mapping

| Protocol concern | Reference implementation |
|---|---|
| Domain model | Python/Pydantic/domain layer |
| Persistence | PostgreSQL |
| Geospatial | PostGIS |
| Evidence files | S3-compatible object storage |
| Async jobs | Redis + Celery or equivalent |
| Graph projection | Relational projection initially |
| API | FastAPI/OpenAPI |
| UI | React/TypeScript |
| Decisions | DecisionProvider/JevProvider |
| Events | Transactional outbox + publisher |
| Authentication | OAuth2/OIDC |

Replacing any row in this table must not change the protocol meaning.

---

# 43. Evolution model

Protocol evolution should proceed by:

1. preserving existing semantics;
2. adding explicit new capabilities;
3. versioning breaking schemas;
4. namespacing extensions;
5. maintaining migration paths;
6. retaining historical interpretation;
7. never silently rewriting physical truth.

The protocol should become more expressive without becoming ambiguous.

---

# 44. Final protocol loop

```text
RESOURCE REALITY
      ↓
MARKET REALITY
      ↓
CAPABILITY REALITY
      ↓
RESOURCE / TRANSFORMATION GRAPH
      ↓
ROUTES
      ↓
DETERMINISTIC VALIDATION
      ↓
DECISIONS
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
```

The central protocol invariant is:

> **No computational representation, model output, recommendation, route score, transaction state, cached projection, or user assertion may become more authoritative than the physical, economic, authorization, and evidence-backed reality it represents.**
