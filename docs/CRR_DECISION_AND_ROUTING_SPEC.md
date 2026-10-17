# CRR Decision and Routing Specification

**Status:** Normative decision and routing specification  
**Version:** 0.1  
**Protocol:** Computational Resource Routing (CRR)  
**Role:** Defines how CRR discovers candidate routes, validates feasibility, computes economics, ranks feasible routes, and uses bounded decision support.

> CRR is a proposed technical/category specification. This document defines the project's routing and decision semantics; it is not an existing external industry standard.

---

# 1. Purpose

The routing system determines which physically, operationally, legally/safely, temporally, and economically feasible path a resource can take toward a valid demand or target state.

CRR therefore does not answer only:

> Who wants this?

It answers:

> **What is the highest-value executable next state or route that can be justified by available physical, operational, economic, regulatory, and evidentiary information?**

Routing is a computation over canonical reality. Decision support is a bounded layer over already validated candidates.

---

# 2. Core routing principle

The routing pipeline is:

```text
SOURCE RESOURCE STATE
        ↓
TARGET DEMAND / TARGET STATE
        ↓
CANDIDATE DISCOVERY
        ↓
HARD CONSTRAINT VALIDATION
        ↓
PHYSICAL FEASIBILITY
        ↓
CAPACITY + TIME
        ↓
LOGISTICS
        ↓
TRANSFORMATION FEASIBILITY
        ↓
REGULATORY / SAFETY / ELIGIBILITY
        ↓
ECONOMICS
        ↓
OPTIMIZATION
        ↓
DECISION SUPPORT
        ↓
RANKED FEASIBLE ROUTES
```

The order is conceptual. Independent checks may execute in parallel, but the semantic dependency is preserved.

---

# 3. Routing inputs

A routing request requires sufficient context to determine a valid source and target.

Conceptually:

```json
{
  "source_resource_state_id": "rst_123",
  "target_demand_id": "dem_123",
  "constraints": {},
  "optimization": {},
  "decision_mode": "optional",
  "valid_until": "2026-10-18T12:00:00Z"
}
```

The request must reference canonical objects rather than allowing clients to invent authoritative state inline.

---

# 4. Candidate discovery

Candidate discovery is intentionally permissive compared with feasibility validation.

It may use:

- exact classifications;
- normalized attributes;
- semantic search;
- graph traversal;
- geographic proximity;
- capability indexes;
- historical outcomes;
- embeddings.

Candidate discovery can produce false positives.

The next layers determine whether candidates are actually feasible.

---

# 5. Hard constraints

Hard constraints are authoritative blockers.

Examples:

- insufficient quantity;
- incompatible physical state;
- incompatible quality;
- invalid unit conversion;
- unavailable capability;
- insufficient capacity;
- impossible location/time requirement;
- expired demand;
- missing required authorization/certification;
- prohibited material/process combination;
- ownership/custody conflict;
- impossible transformation yield;
- required evidence absent where execution cannot proceed.

A route failing a hard constraint MUST be marked infeasible.

No score, probability, model confidence, or Jev output can change that.

---

# 6. Physical feasibility

Physical feasibility asks whether the route could actually occur in the physical world.

Checks include:

- input state compatibility;
- material classification;
- quality compatibility;
- quantity availability;
- transformation input requirements;
- output requirements;
- conservation/yield rules;
- physical process constraints;
- location transitions;
- storage/handling requirements.

A route that is semantically similar but physically impossible is rejected.

---

# 7. Quantity and yield

All authoritative quantities use exact decimal semantics.

For applicable transformations:

```text
INPUT QUANTITY
      ↓
YIELD / LOSS / RESIDUAL MODEL
      ↓
OUTPUT QUANTITY
```

Where conservation applies:

```text
inputs = outputs + declared losses/residuals ± explicit tolerance
```

Silent loss is invalid.

The transformation's declared bounds constrain possible outputs.

---

# 8. Capacity

Available capacity is generally:

```text
DECLARED CAPACITY
- EXISTING COMMITMENTS
- EXISTING RESERVATIONS
- PROTECTED CAPACITY
=
AVAILABLE CAPACITY
```

The router must account for time-window overlap.

A route cannot reserve capacity already committed to an incompatible operation.

Concurrent route proposals must be revalidated before commitment.

---

# 9. Timing

Routing must consider:

- source availability;
- demand window;
- facility operating window;
- processing duration;
- transport duration;
- inspection time;
- storage constraints;
- reservation windows;
- expiration.

A route whose required operation occurs outside an authoritative availability window is infeasible.

A route can become stale if any material timing assumption changes.

---

# 10. Geographic routing

Distance and travel time are derived from authoritative locations and explicit routing assumptions.

A geographic calculation may include:

- straight-line distance for candidate filtering;
- road-network distance for economics;
- estimated travel time;
- transport restrictions;
- location eligibility.

A client, model, or ranking function cannot alter authoritative location merely to make a route economically viable.

Distance calculations must remain reproducible from stored location and routing assumptions.

---

# 11. Logistics

A transport leg represents movement of a physical state.

It may require:

- vehicle capacity;
- loading constraints;
- handling requirements;
- timing;
- permitted routes;
- hazardous-material handling where applicable;
- pickup and delivery windows;
- transport cost.

A transport leg is a plan. It is not proof that shipment occurred.

Shipment proof belongs to execution/evidence.

---

# 12. Transformation feasibility

A transformation leg is valid only if:

1. input state satisfies input specification;
2. capability is active;
3. required capacity exists;
4. operating window permits execution;
5. output is within declared specification;
6. yield/loss model is coherent;
7. regulatory/safety requirements are satisfied;
8. economics are calculated.

A transformation definition cannot be used as evidence of actual transformation.

---

# 13. Regulatory and safety validation

The routing engine must represent applicable eligibility requirements.

Examples:

- authorization;
- certification;
- material restrictions;
- hazardous handling;
- facility eligibility;
- transport restrictions;
- jurisdictional requirements.

The protocol does not attempt to replace jurisdiction-specific legal counsel or regulatory authorities.

Where a material regulatory question cannot be deterministically resolved, the system must escalate rather than invent permission.

---

# 14. Economics

Economic computation is deterministic.

A reference model is:

```text
RESOURCE / BUYER VALUE
- ACQUISITION / PAYMENT
- TRANSPORT
- PROCESSING
- HANDLING
- CERTIFICATION
- TAXES / FEES
= NET ECONOMIC OUTCOME
```

All assumptions and calculation versions are recorded.

A negative net outcome is a valid mathematical result. It becomes economically infeasible only when the route's objective/policy requires non-negative or minimum economic value.

---

# 15. Economic perspectives

CRR may calculate multiple economic perspectives:

### Supplier economics

```text
avoided disposal / recovery value
+ sale value
- supplier-side incremental costs
= supplier outcome
```

### Processor economics

```text
processing revenue / material value
- processing cost
- handling
- energy / auxiliary costs
= processor outcome
```

### Buyer economics

```text
avoided virgin-material purchase
- delivered resource cost
- qualification / processing cost
= buyer outcome
```

### Logistics economics

```text
transport revenue
- transport operating cost
= logistics outcome
```

### Network economics

The platform may calculate transaction fees or service value separately from physical economics.

The protocol must not silently combine participant economics into one number without labeling the perspective.

---

# 16. Optimization

Optimization operates only over routes that have passed hard feasibility.

Potential objectives include:

- maximum net economic value;
- minimum total cost;
- minimum transport distance/time;
- maximum resource recovery;
- maximum reliability;
- minimum transformation risk;
- minimum environmental impact where the metric is valid and evidenced;
- balanced multi-objective optimization.

Every optimization result must expose the objective and version used.

---

# 17. Ranking

A reference ranking can combine:

- economic value;
- distance/time;
- evidence quality;
- capacity reliability;
- transformation risk;
- timing fit;
- quality compatibility;
- historical execution performance.

Weights must be explicit when weights are used.

A ranking score is not truth.

A score can order feasible routes but cannot legalize, authorize, or physically validate a route.

---

# 18. Candidate set integrity

Once the decision stage begins, the candidate set must be fixed or content-addressed.

A decision record must be able to answer:

- which candidates existed;
- which candidates were feasible;
- which constraints were applied;
- which economic assumptions were used;
- which candidates were passed to Jev;
- which candidate was selected;
- why the selected candidate was accepted.

Jev cannot introduce an unseen candidate as though it had been part of the validated candidate set.

---

# 19. Decision architecture

```text
ROUTE CANDIDATES
      ↓
DETERMINISTIC VALIDATION
      ↓
CANDIDATE SET
      ↓
STRUCTURED DECISION CONTEXT
      ↓
DECISION PROVIDER
      ↓
STRUCTURED RESULT
      ↓
DETERMINISTIC FACT CHECK
      ↓
ACCEPT / REJECT / ESCALATE
```

The decision layer does not own physical truth.

---

# 20. Jev decision boundary

Jev may assist with:

- semantic compatibility;
- ambiguous classification;
- candidate prioritization;
- qualitative tradeoffs;
- contextual interpretation;
- explanation;
- escalation recommendations.

Jev cannot:

- override hard constraints;
- invent organizations;
- invent capabilities;
- invent demand;
- invent quantities;
- create capacity;
- invent regulatory permission;
- fabricate evidence;
- change authoritative location;
- change authoritative economic inputs;
- directly mutate canonical state;
- directly execute transactions.

Jev is therefore a bounded provider, not a system-of-record component.

---

# 21. Decision request contract

A decision request contains:

- decision type;
- candidate IDs;
- authoritative constraints;
- evidence references;
- economic context;
- uncertainty;
- allowed action space;
- relevant policy;
- context hash.

A decision result contains:

- selected candidate;
- rationale;
- confidence;
- uncertainty;
- evidence references;
- provider/model/version;
- deterministic validation result;
- escalation requirement.

The selected candidate must belong to the candidate set and pass deterministic validation.

---

# 22. AI output validation

AI/provider output is untrusted input.

It must be validated for:

- schema correctness;
- candidate membership;
- reference existence;
- hard-constraint compliance;
- numerical validity;
- regulatory claims;
- evidence claims;
- authority boundaries.

Adversarial tests should include:

- hallucinated organizations;
- hallucinated capabilities;
- hallucinated demand;
- fabricated evidence;
- impossible quantities;
- invalid units;
- nonexistent candidates;
- invented regulations;
- prompt injection through resource descriptions;
- attempts to trigger unauthorized execution.

---

# 23. Fallback behavior

If Jev is unavailable:

1. deterministic routing continues where possible;
2. deterministic ranking can continue when sufficient;
3. ambiguous cases escalate to human review;
4. no hard-constraint semantics change;
5. no canonical state is corrupted;
6. the provider failure is recorded.

The system must never silently treat Jev failure as authorization to bypass decision controls.

---

# 24. Route lifecycle

Reference lifecycle:

```text
GENERATED
    ↓
VALIDATING
    ↓
FEASIBLE / INFEASIBLE
    ↓
SELECTED / REJECTED
    ↓
EXPIRED
```

The exact implementation may separate status and validation fields, but the semantic distinction must remain.

---

# 25. Route validity and staleness

A route becomes stale when material assumptions change, including:

- source quantity;
- source location;
- source quality;
- demand status;
- demand quantity;
- capability status;
- capability capacity;
- transformation version;
- regulatory authorization;
- transport assumptions;
- price assumptions;
- economic model validity;
- timing windows.

A stale route must be revalidated before execution.

---

# 26. Route explainability

Every route should be explainable in terms of:

```text
SOURCE
TARGET
LEGS
CONSTRAINTS PASSED
CONSTRAINTS FAILED
CAPACITY
TIMING
LOGISTICS
TRANSFORMATIONS
ECONOMICS
OBJECTIVE
SCORE
DECISION
EXPIRY
```

The explanation is derived from authoritative inputs and recorded calculations rather than generated solely from free-form model text.

---

# 27. Route rejection reasons

Machine-readable rejection reasons should include:

- `INSUFFICIENT_QUANTITY`;
- `UNIT_INCOMPATIBLE`;
- `QUALITY_MISMATCH`;
- `CAPABILITY_INACTIVE`;
- `CAPACITY_INSUFFICIENT`;
- `TIME_WINDOW_CONFLICT`;
- `LOCATION_INFEASIBLE`;
- `REGULATORY_BLOCK`;
- `SAFETY_BLOCK`;
- `OWNERSHIP_CONFLICT`;
- `TRANSFORMATION_UNAVAILABLE`;
- `YIELD_INVALID`;
- `ECONOMIC_INFEASIBILITY`;
- `DEMAND_EXPIRED`;
- `EVIDENCE_REQUIRED`.

Each rejection should identify the relevant rule and object reference where possible.

---

# 28. Commercial conversion

Only feasible routes may produce normal opportunities.

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

An opportunity may expire if route assumptions change.

A transaction cannot be created from a route that has become stale without revalidation.

---

# 29. Reservation semantics

Routing and transaction commitment must distinguish:

- candidate capacity;
- soft reservation;
- hard reservation;
- committed capacity;
- actual consumption.

A routing calculation should not silently imply a physical capacity reservation.

Capacity becomes committed only through an explicit transactional operation.

---

# 30. Execution boundary

The routing engine proposes.

The commercial system commits.

The execution system records.

Evidence verifies.

```text
ROUTING
  ≠
EXECUTION
  ≠
VERIFICATION
```

This distinction prevents a computational plan from becoming a false physical claim.

---

# 31. Reference routing algorithm

A reference implementation may follow:

```text
1. Load canonical source ResourceState.
2. Validate source availability.
3. Resolve active target Demand.
4. Discover candidate capabilities.
5. Discover candidate transformations.
6. Build candidate route graphs.
7. Evaluate hard constraints.
8. Reject invalid routes.
9. Calculate physical feasibility.
10. Calculate capacity/time feasibility.
11. Calculate logistics.
12. Calculate regulatory/safety eligibility.
13. Calculate deterministic economics.
14. Optimize/rank feasible routes.
15. Build decision context.
16. Optionally invoke Jev.
17. Validate provider output.
18. Select or escalate.
19. Record route/decision provenance.
20. Return ranked feasible candidates.
```

This is a reference algorithm, not a requirement that every implementation use the same code structure.

---

# 32. Routing invariants

1. Every route has a valid source.
2. Every route has a valid target.
3. Every leg is ordered.
4. Every leg has compatible input/output states.
5. No hard constraint is violated.
6. Capacity is sufficient.
7. Quantity is sufficient.
8. Demand is active.
9. Capability is active.
10. Required transformation exists.
11. Economics are reproducible.
12. Scores never override feasibility.
13. Candidate sets are fixed for decision evaluation.
14. Jev cannot create facts.
15. Expired routes cannot execute.
16. Actual execution cannot be inferred from route existence.
17. Stale routes must be revalidated.
18. Route calculations remain auditable.
19. Reservation does not equal execution.
20. Execution does not equal verification.

---

# 33. Relationship to validation specification

`CRR_VALIDATION_AND_INVARIANTS.md` contains the complete cross-domain validation registry.

This document defines routing/decision-specific semantics. Where the routing engine and validation layer overlap, the stricter protocol invariant applies.

---

# 34. Final routing principle

> **CRR may use increasingly sophisticated computation to find better routes, but sophistication must never reduce the authority of physical reality, hard constraints, evidence, or explicit authorization.**

The routing system is therefore:

```text
DISCOVER BROADLY
      ↓
VALIDATE STRICTLY
      ↓
CALCULATE DETERMINISTICALLY
      ↓
OPTIMIZE EXPLICITLY
      ↓
ADVISE CONTEXTUALLY
      ↓
EXECUTE DELIBERATELY
      ↓
VERIFY EMPIRICALLY
```
