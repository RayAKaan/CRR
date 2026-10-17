# CRR Data Flow Architecture

**Status:** Normative reference data-flow specification  
**Version:** 0.1  
**Protocol:** Computational Resource Routing (CRR)  
**Document role:** Defines how physical, commercial, computational, evidentiary, and derived information moves through a conforming CRR implementation.

> **Important terminology:** CRR / Computational Resource Routing is a proposed technical and category specification created by this project. It is not presented as an already-established global industry standard.

---

## 1. Purpose

CRR exists to make physical-resource circulation computationally representable and executable without confusing digital recommendations with physical truth.

The data-flow architecture covers the complete lifecycle:

```text
PHYSICAL REALITY
        ↓
OBSERVATION / INGESTION
        ↓
RAW RECORD
        ↓
VALIDATION
        ↓
NORMALIZATION
        ↓
CANONICAL RESOURCE REALITY
        ↓
RESOURCE STATE
        ↓
DEMAND + CAPABILITY REALITY
        ↓
TRANSFORMATION GRAPH
        ↓
ROUTE GENERATION
        ↓
HARD-CONSTRAINT VALIDATION
        ↓
FEASIBILITY
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
ACTUAL OBSERVATIONS
        ↓
EVIDENCE
        ↓
VERIFICATION
        ↓
VERIFIED OUTCOME
        ↓
NETWORK UPDATE
        ↓
BETTER FUTURE ROUTING
```

The architecture deliberately does **not** stop at matching. A match is only an intermediate computation. The intended system closes the loop from physical reality to a verified physical outcome.

---

## 2. Core data-flow principle

The system must always distinguish between:

1. what physically exists;
2. what a participant says exists;
3. what the protocol has normalized and accepted;
4. what the routing engine derives;
5. what the decision layer recommends;
6. what participants plan to do;
7. what actually happened;
8. what evidence was submitted;
9. what has been verified.

This produces the following epistemic hierarchy:

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

These are not interchangeable labels. The implementation must preserve their meaning.

---

## 3. Data authority model

| Data class | Meaning | Authority | Regenerable? |
|---|---|---|---|
| Raw | Original external submission | Source record | No |
| Validated | Passed applicable validation | Validation result | No, result should be auditable |
| Normalized | Converted into canonical representation | Domain normalization | Reproducible from raw + rules |
| Canonical | Accepted CRR domain truth | CRR domain state | No |
| Derived | Graph, index, embedding, score, cache | Computation | Yes |
| Planned | Intended future action | Plan/transaction | No |
| Actual | Observed execution fact | Execution/evidence | No |
| Claimed | Submitted assertion | Claimant | No |
| Verified | Evidence-backed accepted fact | Authorized verifier | No |

> **Non-negotiable:** Derived computation can explain, rank, search, or predict canonical reality, but it cannot replace canonical reality.

---

## 4. Complete system flow

### 4.1 Physical reality

A participant possesses, produces, stores, moves, transforms, consumes, sells, buys, or otherwise controls a physical resource.

CRR is intentionally not limited to waste. Relevant resource classes may include industrial byproducts, secondary raw materials, scrap, surplus inventory, recoverable process outputs, reusable components, or materials requiring transformation before reuse.

### 4.2 Observation and ingestion

Reality enters through manual entry, CSV, XLSX, JSON, REST APIs, ERP integrations, inventory systems, production systems, logistics systems, laboratory records, or other authorized feeds.

Every external observation receives provenance.

### 4.3 Validation and normalization

```text
RAW INPUT
   ↓
PARSING
   ↓
SCHEMA VALIDATION
   ↓
AUTHENTICATION / AUTHORIZATION
   ↓
REFERENCE RESOLUTION
   ↓
UNIT NORMALIZATION
   ↓
LOCATION NORMALIZATION
   ↓
CLASSIFICATION
   ↓
QUALITY VALIDATION
   ↓
DOMAIN VALIDATION
   ↓
PROVENANCE
```

Invalid information cannot silently become canonical truth.

### 4.4 Canonical reality

A successful ingestion creates or updates protocol objects such as `Organization`, `Actor`, `Location`, `Resource`, `ResourceState`, `Demand`, `Capability`, and `Transformation`.

`ResourceState` is the fundamental physical primitive.

### 4.5 Network computation

Canonical objects are projected into graph, search, embedding, ranking, and analytics structures. These structures are derived and regenerable.

### 4.6 Routing

```text
SOURCE STATE
    ↓
TARGET DEMAND / STATE
    ↓
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
```

Only feasible routes can enter ranking.

### 4.7 Decision support

Jev may assist with semantic compatibility, ambiguous classification, prioritization, qualitative tradeoffs, contextual interpretation, escalation, and explanation. It does not own hard facts.

### 4.8 Commercial conversion

```text
FEASIBLE ROUTE
     ↓
OPPORTUNITY
     ↓
OFFER
     ↓
AGREEMENT
     ↓
TRANSACTION
```

Opportunity, offer, agreement, and transaction have separate semantics and lifecycle rules.

### 4.9 Physical execution

```text
TRANSACTION
     ↓
EXECUTION PLAN
     ↓
PICKUP
     ↓
SHIPMENT
     ↓
RECEIPT
     ↓
PROCESSING / TRANSFORMATION
     ↓
DELIVERY / ACCEPTANCE
```

The route is a plan. Execution records actual operations.

### 4.10 Evidence and verification

Execution produces evidence such as weighbridge records, laboratory certificates, pickup records, transport records, delivery records, processing records, and buyer acceptance.

```text
CLAIMED
   ↓
SUBMITTED
   ↓
VALIDATED
   ↓
VERIFIED
```

Verification is an authorized operation, not a client-controlled field assignment.

### 4.11 Network feedback

Verified outcomes can improve future estimates of yield, cost, quality, distance, time, reliability, and failure probability. Historical facts remain unchanged.

---

## 5. Resource ingestion flow

```text
CSV / XLSX / JSON / API / MANUAL
              ↓
        RAW CAPTURE
              ↓
       PARSE / SCHEMA
              ↓
    AUTHENTICATION / AUTHORIZATION
              ↓
      REFERENCE RESOLUTION
              ↓
       NORMALIZATION
       ├── units
       ├── locations
       ├── classifications
       ├── quality fields
       └── timestamps
              ↓
       DOMAIN VALIDATION
              ↓
          PROVENANCE
              ↓
     RESOURCE + RESOURCE STATE
              ↓
        CANONICAL WRITE
              ↓
            EVENT
```

The raw record remains traceable after normalization. Invalid rows may be rejected or quarantined, but they cannot bypass domain validation.

A bulk import follows the same domain rules as API-created objects.

---

## 6. Demand flow

Demand is an acceptance specification, not merely a text description.

```text
DEMAND SOURCE
     ↓
REQUIRED RESOURCE STATE
     ↓
QUANTITY
     ↓
QUALITY
     ↓
LOCATION
     ↓
TIME WINDOW
     ↓
PRICE CONSTRAINTS
     ↓
CERTIFICATIONS
     ↓
REGULATORY REQUIREMENTS
     ↓
SUBSTITUTION RULES
     ↓
ACTIVE DEMAND
```

Only active demand is eligible for normal routing. Expired, paused, cancelled, or fulfilled demand cannot silently remain eligible.

---

## 7. Capability flow

```text
ORGANIZATION
     ↓
CAPABILITY
     ├── accepted inputs
     ├── transformations
     ├── outputs
     ├── capacity
     ├── operating window
     ├── location
     ├── minimum batch
     ├── cost model
     ├── certifications
     └── regulatory eligibility
```

Routing must use available capacity after existing commitments/reservations rather than theoretical capacity alone.

---

## 8. Transformation flow

```text
INPUT RESOURCE STATE
        ↓
INPUT REQUIREMENTS
        ↓
PROCESS
        ↓
YIELD / LOSS / RESIDUAL MODEL
        ↓
OUTPUT RESOURCE STATE(S)
```

The transformation definition answers whether a state **could** become another state. Execution and evidence answer whether it **did**.

Every transformation must define applicable input specifications, output specifications, yield bounds, loss/residual semantics, capacity, duration, cost, quality effects, and regulatory requirements.

---

## 9. Graph data flow

The graph is a projection of canonical reality.

```text
Organization
     │
     ├── owns → Resource → has → ResourceState
     ├── creates → Demand
     ├── provides → Capability → enables → Transformation
     └── participates → Transaction

ResourceState
     ↓
Transformation
     ↓
ResourceState
     ↓
Demand
```

The graph may answer what can happen, who can process something, who needs it, what transformations exist, which capabilities have capacity, and which routes are plausible.

If the projection is stale, canonical state wins.

---

## 10. Route data flow

A route is an ordered executable plan containing transport and transformation legs.

```text
SOURCE STATE
     ↓
TRANSPORT LEG
     ↓
INTERMEDIATE STATE
     ↓
TRANSFORMATION LEG
     ↓
NEW STATE
     ↓
TRANSPORT LEG
     ↓
TARGET / DEMAND
```

A route exposes its source, target, ordered legs, timing, capacity assumptions, distance/time, transformation requirements, regulatory results, economics, validity period, and decision references where applicable.

Every leg must produce a state compatible with the next leg.

---

## 11. Hard-constraint flow

Hard constraints are evaluated before ranking.

```text
CANDIDATE ROUTE
      ↓
QUANTITY
      ↓
UNIT
      ↓
STATE COMPATIBILITY
      ↓
QUALITY
      ↓
CAPACITY
      ↓
TIME
      ↓
LOCATION / LOGISTICS
      ↓
REGULATION / SAFETY
      ↓
AUTHORIZATION
      ↓
FEASIBLE / INFEASIBLE
```

An infeasible route cannot re-enter the feasible set because of a higher score, model confidence, or Jev recommendation.

---

## 12. Economic data flow

Authoritative economics are deterministic and reproducible.

```text
GROSS VALUE
+
BUYER PAYMENT
+
OTHER VALUE
-
TRANSPORT
-
PROCESSING
-
HANDLING
-
CERTIFICATION
-
APPLICABLE TAXES / FEES
=
NET ECONOMIC OUTCOME
```

Each model records currency, inputs, assumptions, calculation version, timestamp, components, and result.

A negative outcome remains a valid mathematical result; it becomes economically infeasible only when the route's objective or policy requires a non-negative outcome.

---

## 13. Decision data flow

```text
AUTHORITATIVE CONTEXT
       ↓
FIXED CANDIDATE SET
       ↓
DETERMINISTIC VALIDATION
       ↓
STRUCTURED DECISION REQUEST
       ↓
DECISION PROVIDER / JEV
       ↓
STRUCTURED OUTPUT
       ↓
SCHEMA VALIDATION
       ↓
CANONICAL FACT CHECK
       ↓
ACCEPT / REJECT / ESCALATE
```

The candidate set is fixed and auditable. A decision cannot select a candidate outside that set or an option that fails authoritative constraints.

---

## 14. Commercial data flow

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

An opportunity is a commercial possibility. An offer proposes terms. An agreement records accepted obligations. A transaction connects the commercial commitment to physical execution.

Commercial state never constitutes proof of physical completion.

---

## 15. Execution data flow

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
```

Each step may contain a responsible party, planned values, actual values, timestamps, status, exceptions, and evidence references.

Failed or partial steps remain explicitly failed or partial.

---

## 16. Evidence data flow

```text
ACTUAL OBSERVATION
      ↓
CLAIM / ARTIFACT
      ↓
EVIDENCE SUBMISSION
      ↓
EVIDENCE VALIDATION
      ↓
AUTHORIZED VERIFICATION
      ↓
VERIFIED FACT
```

Evidence must be attributable and tied to a protocol object, state, execution step, event, or transaction claim.

For immutable evidence artifacts, a content hash should be recorded so that the referenced artifact can be integrity-checked.

---

## 17. Event flow

```text
DOMAIN COMMAND
      ↓
VALIDATION
      ↓
CANONICAL STATE CHANGE
      ↓
EVENT RECORD
      ↓
OUTBOX / PUBLISHER
      ↓
WEBHOOKS / PROJECTIONS / ANALYTICS / INTEGRATIONS
```

Events are immutable. Delivery may be at least once. Consumers therefore deduplicate by event ID and preserve required aggregate ordering using aggregate versions.

Recommended event envelope fields:

- `event_id`;
- `event_type`;
- `event_version`;
- `occurred_at`;
- `published_at` where available;
- `aggregate_type`;
- `aggregate_id`;
- `aggregate_version`;
- `actor`;
- `organization_id`;
- `correlation_id`;
- `causation_id`;
- `idempotency_key` where applicable;
- `payload`;
- `provenance`;
- `schema_version`.

---

## 18. Feedback and learning flow

```text
VERIFIED TRANSACTION
       ↓
OBSERVED OUTCOME
       ├── quantity
       ├── quality
       ├── yield
       ├── processing cost
       ├── transport cost
       ├── duration
       ├── distance
       └── failure / acceptance
       ↓
DERIVED NETWORK KNOWLEDGE
       ↓
BETTER ROUTING / ECONOMICS
```

The feedback loop changes derived models, not the historical record.

---

## 19. Data ownership and authority

| Object/data | Primary semantic authority |
|---|---|
| Organization | Organization / authorized administrator |
| Resource identity | Owning organization / protocol |
| ResourceState | Controlling organization plus accepted evidence |
| Demand | Demand owner |
| Capability | Capability owner |
| Transformation definition | Capability/process owner |
| Route | CRR computation |
| Decision | Decision engine/provider record |
| Opportunity | Authorized commercial participants |
| Offer | Proposer until accepted |
| Agreement | Agreement participants |
| Transaction | Authorized transaction participants |
| Execution observation | Responsible operator/system |
| Evidence | Issuer + verifier |
| Graph | Derived projection |
| Search/embedding | Derived computation |
| Economic model | Recorded deterministic calculation |
| Event history | Protocol event system |

---

## 20. Data lifecycle and historical integrity

Canonical information follows controlled transitions:

```text
INGESTED
 ↓
VALIDATED
 ↓
NORMALIZED
 ↓
CANONICAL
 ↓
ACTIVE
 ↓
RESERVED / IN USE
 ↓
TRANSFORMED / CONSUMED / COMPLETED
 ↓
HISTORICAL
```

A correction to physical reality creates a new state, revision, event, or evidence-backed correction. It does not silently erase the prior history.

---

## 21. Failure flow

Failures are first-class outcomes.

```text
INVALID INPUT        → VALIDATION_FAILURE
NO AUTHORIZATION     → AUTHORIZATION_FAILURE
INSUFFICIENT CAPACITY→ CAPACITY_INSUFFICIENT
NO FEASIBLE ROUTE    → NO_FEASIBLE_ROUTE
LEGAL BLOCK          → REGULATORY_FAILURE
ECONOMIC FAILURE     → ECONOMIC_INFEASIBILITY
LOGISTICS FAILURE    → PARTIAL_EXECUTION / FAILURE
EVIDENCE CONFLICT    → DISPUTE
JEV TIMEOUT          → JEV_UNAVAILABLE / ESCALATION
WEBHOOK FAILURE      → RETRY / DEAD-LETTER
```

No failure may silently become a successful canonical state.

---

## 22. Reference implementation data stores

A practical implementation may use:

```text
PostgreSQL
 ├── canonical domain objects
 ├── lifecycle state
 ├── economic models
 ├── event/outbox records
 └── audit metadata

PostGIS
 └── geospatial representation and deterministic spatial calculations

Object Storage
 └── evidence documents/media

Redis + Worker Queue
 └── cache and asynchronous processing

Relational Graph Projection
 └── derived network relationships

Search / Embeddings
 └── optional semantic retrieval
```

A dedicated graph database is not required for MVP. A graph database, cloud provider, queue technology, database, or frontend framework is not a protocol requirement.

---

## 23. Security data flow

```text
REQUEST
 ↓
AUTHENTICATION
 ↓
AUTHORIZATION
 ↓
TENANT SCOPE
 ↓
OBJECT ACCESS POLICY
 ↓
VALIDATION
 ↓
DOMAIN MUTATION
```

Sensitive information includes commercial pricing, internal capacity, contracts, evidence, personal data, proprietary process information, credentials, and decision-provider configuration.

Jev receives only the minimum context required for its bounded decision.

---

## 24. Complete end-to-end scenario

```text
Factory A
   ↓
100 t ResourceState S1
   ↓
Resource validation
   ↓
Demand D1 discovered
   ↓
Capability C1 discovered
   ↓
Transformation S1 → S2 identified
   ↓
Candidate routes generated
   ↓
Quantity / unit / quality validation
   ↓
Capacity validation
   ↓
Location / logistics validation
   ↓
Regulatory validation
   ↓
Economic calculation
   ↓
Feasible routes ranked
   ↓
Jev optionally assists prioritization
   ↓
Opportunity O1
   ↓
Offer
   ↓
Agreement
   ↓
Transaction T1
   ↓
Execution E1
   ↓
Pickup
   ↓
Shipment
   ↓
Receipt
   ↓
Transformation
   ↓
Output S2
   ↓
Evidence
   ↓
Verification
   ↓
Verified outcome
   ↓
Observed cost / yield / time / quality
   ↓
Network learning
```

This is the minimum complete CRR data-flow proof.

---

## 25. Data-flow invariants

1. Physical reality is authoritative.
2. Raw inputs remain traceable.
3. Invalid inputs cannot become canonical facts.
4. Canonical physical history is not destructively overwritten.
5. ResourceState remains the physical primitive.
6. Quantity and unit semantics remain exact.
7. Lineage survives split, merge, and transformation.
8. Planned, actual, claimed, and verified values remain distinct.
9. Derived projections remain derived.
10. Graph data cannot override canonical data.
11. Hard constraints are deterministic.
12. AI cannot fabricate physical facts.
13. AI cannot override hard constraints.
14. Route existence is not execution proof.
15. Transaction completion is not automatically verification.
16. Evidence cannot become verified without authorization.
17. Events remain immutable.
18. Event replay cannot duplicate domain effects.
19. Cross-tenant information cannot leak through derived projections or events.
20. Historical economic calculations remain reproducible.
21. Verified outcomes feed future computation without rewriting history.

---

## 26. Relationship to the other CRR specifications

This document is cross-cutting and must remain aligned with the other canonical documents:

- `CRR_PROTOCOL_SPEC.md` — protocol meaning and normative semantics.
- `CRR_DOMAIN_MODEL.md` — canonical objects, relationships, and lifecycle states.
- `SYSTEM_DESIGN.md` — reference system architecture and implementation boundaries.
- `CRR_DECISION_AND_ROUTING_SPEC.md` — route construction, hard constraints, economics, optimization, and decision/Jev boundaries.
- `CRR_API_CONTRACT.md` — externally observable API behavior.
- `CRR_VALIDATION_AND_INVARIANTS.md` — validation and invariant enforcement.

No implementation layer may silently weaken a rule established by the normative specifications.

---

## 27. Final data-flow principle

CRR is successful only when this loop is closed:

```text
PHYSICAL REALITY
      ↓
COMPUTABLE REPRESENTATION
      ↓
VALIDATED REALITY
      ↓
ROUTE
      ↓
DECISION
      ↓
COMMERCIAL COMMITMENT
      ↓
PHYSICAL EXECUTION
      ↓
EVIDENCE
      ↓
VERIFICATION
      ↓
TRUSTED OUTCOME
      ↓
BETTER FUTURE ROUTING
```

The purpose of this architecture is not merely to move records between services. It is to preserve the relationship between computation and physical reality from the first observation through the final verified outcome.
