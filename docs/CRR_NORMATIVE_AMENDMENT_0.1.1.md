# CRR Normative Amendment 0.1.1

**Status:** Normative clarification and consistency amendment  
**Protocol:** Computational Resource Routing (CRR)  
**Applies to:** All CRR 0.1 documentation and conforming implementations  
**Authority:** This amendment resolves ambiguities or contradictions in earlier 0.1 wording without changing CRR's core thesis.

> CRR is a proposed technical/category specification created by this project. This amendment does not imply that CRR is an established external standard.

---

# 1. Why this amendment exists

The original CRR 0.1 specification set established the architecture, domain vocabulary, routing model, API, validation model, and reference system. A strict cross-document review identified several places where wording could be interpreted too broadly by an implementer.

This amendment makes those semantics explicit so that two independent teams cannot reasonably implement contradictory behavior while both believing they conform.

The amendment is intentionally narrow. It does **not** redesign CRR.

---

# 2. Normative precedence

For CRR 0.1.1, this document has authority only where it explicitly clarifies or constrains an ambiguity in the existing specification set.

Otherwise, the normal document authority order remains:

1. `CRR_PROTOCOL_SPEC.md`
2. `CRR_DOMAIN_MODEL.md`
3. `CRR_VALIDATION_AND_INVARIANTS.md`
4. `CRR_DECISION_AND_ROUTING_SPEC.md`
5. `CRR_API_CONTRACT.md`
6. `SYSTEM_DESIGN.md`
7. `CRR_DATA_FLOW_ARCHITECTURE.md`

Explanatory README material never overrides normative protocol semantics.

---

# 3. Epistemic classifications are dimensions, not one universal state machine

CRR uses the concepts:

```text
RAW
VALIDATED
NORMALIZED
CANONICAL
DERIVED
PLANNED
ACTUAL
CLAIMED
VERIFIED
```

These MUST NOT be interpreted as one mandatory linear lifecycle.

For example:

- a source record can be `RAW` and also describe a `CLAIMED` observation;
- a canonical plan can be `CANONICAL` and `PLANNED`;
- an execution record can be `CANONICAL` and `ACTUAL`;
- an evidence submission can be `CANONICAL` and `CLAIMED` before verification;
- a verified fact can be `CANONICAL` and `VERIFIED`;
- a route score can be `DERIVED` and `PLANNED`.

Implementations MUST model these as separable properties or equivalent semantics.

A derived object MUST NOT become authoritative merely because it reaches a later-looking stage in a visual pipeline.

---

# 4. ResourceState authority and evidence

`ResourceState` is the canonical protocol representation of a physical resource state after applicable validation and acceptance.

Evidence is supporting material used to establish provenance, substantiate observations, or verify claims.

Therefore:

- evidence MUST NOT be treated as the physical resource state itself;
- evidence MUST NOT silently replace the canonical state;
- a verification result MUST reference the evidence and the claim/state/event it verifies;
- the canonical state MUST retain attribution to its controlling organization/source and provenance;
- contradictory evidence MUST be represented as a conflict/dispute or correction process, not silently deleted.

A verifier establishes whether a claim is supported. The verifier does not thereby become the owner of the physical resource.

---

# 5. ResourceState mutation and API safety

`PATCH /v1/resource-states/{id}` is a general API shape, not unrestricted permission to rewrite physical reality.

A conforming implementation MUST prevent arbitrary mutation of authoritative physical semantics through generic patch operations.

The following classes of change require explicit validation and, where material, an explicit transition/correction operation:

- quantity;
- unit;
- physical classification/state type;
- quality;
- contamination/purity;
- location when physically material;
- ownership/custody;
- availability;
- effective time;
- lineage;
- provenance;
- verification status.

The preferred operation for a material physical change is:

```text
POST /v1/resource-states/{id}/transitions
```

A transition MUST:

1. identify the predecessor state;
2. identify the resulting state or state version;
3. validate all applicable invariants;
4. record actor and organization attribution;
5. record time semantics;
6. preserve lineage;
7. emit an auditable event;
8. prevent stale concurrent updates;
9. preserve the prior physical history.

A correction to an erroneous state is not permission to erase the erroneous historical record. It must itself be auditable.

---

# 6. State transitions are not arbitrary status assignments

Canonical lifecycle fields MUST NOT be treated as free-form strings that clients may set arbitrarily.

For lifecycle-controlled objects, the server determines whether a transition is legal.

Examples include:

```text
Opportunity:
DISCOVERED → VALIDATING → PROPOSED → APPROVED / REJECTED / EXPIRED

Transaction:
DISCOVERED → PROPOSED → ACCEPTED → AGREED → SCHEDULED
→ EXECUTING → COMPLETED → VERIFIED

Evidence:
CLAIMED → SUBMITTED → VERIFIED / REJECTED / DISPUTED

Decision:
REQUESTED → EVALUATING → GENERATED → VALIDATED
→ ACCEPTED / REJECTED / ESCALATED
```

Implementations MAY use different internal representations, but externally observable behavior MUST preserve the transition semantics.

---

# 7. Hard constraints and AI authority

A hard constraint is a blocking condition derived from authoritative rules or facts.

Examples include:

- impossible quantity;
- incompatible unit;
- insufficient capacity;
- invalid operating window;
- unavailable source state;
- incompatible physical quality;
- authorization failure;
- safety blocker;
- regulatory blocker;
- expired capability;
- expired demand;
- prohibited route leg;
- violated contractual execution constraint where contract is authoritative.

AI/Jev output MUST be treated as advisory input unless explicitly represented through a deterministic, validated protocol rule.

No AI-generated score, confidence, explanation, or classification can override a blocking hard constraint.

---

# 8. Decision provider isolation

All external decision providers MUST sit behind a bounded interface equivalent to:

```text
Decision Engine
    ↓
DecisionProvider
    ↓
JevProvider / other provider
```

Provider input MUST be limited to the context necessary for the decision.

Provider output MUST be:

1. parsed;
2. schema-validated;
3. checked against authoritative facts;
4. checked against hard constraints;
5. recorded with provider/model/version metadata where applicable;
6. attributed;
7. rejected or escalated when inconsistent.

The provider MUST NOT receive implicit authority to mutate canonical state.

---

# 9. Economics are deterministic at the protocol boundary

An economic result used for route feasibility or decisioning MUST be reproducible from recorded inputs and a versioned calculation model.

At minimum, the model should make explicit:

```text
VALUE
− TRANSPORT
− PROCESSING
− HANDLING
− CERTIFICATION
− TAXES / FEES
− OTHER DECLARED COSTS
= NET ECONOMIC VALUE
```

Additional terms may exist.

The following MUST be recorded where material:

- currency;
- quantity basis;
- price basis;
- cost assumptions;
- conversion factors;
- calculation version;
- source references;
- calculation timestamp;
- rounding policy.

A model may use uncertain or estimated inputs, but the fact that an input is estimated MUST remain visible.

---

# 10. Quantity, conservation, and transformation semantics

CRR does not assume that every transformation conserves mass exactly.

Each transformation MUST declare its applicable balance/yield model.

Where conservation applies:

```text
INPUT QUANTITY
=
OUTPUT QUANTITY
+
DECLARED LOSS / RESIDUAL
```

within an explicit, versioned tolerance.

Splits, merges, and transformations MUST preserve traceable lineage and reconcile quantities according to the declared model.

Silent loss is prohibited.

A transformation that intentionally consumes auxiliary material, produces by-products, or changes measurement basis must represent those semantics explicitly.

---

# 11. Capacity semantics

For a capacity-constrained operation:

```text
AVAILABLE CAPACITY
=
TOTAL CAPACITY
− RESERVED CAPACITY
− COMMITTED CAPACITY
```

The exact capacity model may include time windows, resource-specific capacity, maintenance, minimum batch size, throughput, or other constraints.

A route MUST NOT allocate capacity that is unavailable for its required interval.

Reservations MUST be concurrency-safe so two accepted transactions cannot both consume the same finite capacity.

---

# 12. Demand semantics

Normal routing requires an active demand or an explicitly defined target state.

Demand MUST expose enough semantics to determine:

- required resource/state;
- required quantity;
- acceptable quality;
- location;
- timing;
- acceptance criteria;
- remaining quantity.

Expired, cancelled, paused, or fully satisfied demand MUST NOT be treated as active demand.

Allocation MUST NOT exceed remaining requirement.

---

# 13. Capability semantics

A capability is executable only when its relevant status, capacity, operating window, authorization, certification, and other applicable constraints are valid at the planned execution time.

A capability definition alone does not prove that an execution occurred.

Revoked, expired, suspended, or otherwise invalid capabilities MUST be excluded from execution selection.

---

# 14. Route semantics

A route is a plan and a computed claim of feasibility at a particular time under a particular input snapshot.

Therefore a route MUST retain enough context to reproduce or audit its result, including where applicable:

- source state/version;
- target demand/state/version;
- route legs;
- constraint results;
- capacity assumptions;
- timing assumptions;
- logistics assumptions;
- regulatory/safety result;
- economic model/version;
- optimization objective/version;
- decision reference;
- generated-at time;
- expiry/revalidation requirement.

A route MAY become stale.

A stale route MUST be revalidated before a material execution commitment.

A route score MUST never be used as a substitute for feasibility.

---

# 15. Events and idempotency

Events are immutable records of protocol state changes.

An event MUST carry enough metadata for traceability, including where applicable:

- event ID;
- event type/version;
- occurrence time;
- publication time;
- aggregate type/id/version;
- actor;
- organization;
- correlation ID;
- causation ID;
- idempotency key where applicable;
- payload;
- provenance;
- schema version.

At-least-once delivery is acceptable.

Consumers MUST deduplicate replayed events by stable event identity or equivalent semantics.

Aggregate versions MUST be monotonic for ordered aggregate mutation.

A consumer failure MUST NOT cause an event to be interpreted as a new physical fact merely because it was delivered again.

---

# 16. Security boundary

A conforming implementation MUST enforce:

- authentication;
- authorization;
- tenant isolation;
- least privilege;
- protected evidence access;
- protected economic data;
- auditability;
- secure secret handling;
- transport and storage protection appropriate to the deployment.

Authorization is evaluated before protected disclosure.

A client MUST NOT be able to set its own verification result merely by submitting a payload with `status = VERIFIED`.

---

# 17. Verification semantics

Verification is an authorized evaluation of a claim against required evidence and verification rules.

Verification MUST identify:

- what was claimed;
- what evidence was evaluated;
- who/what performed verification;
- when verification occurred;
- which verification rules/version applied;
- result;
- any limitations or disputes.

Verification MUST be reversible through an explicit correction/dispute process when later evidence invalidates the result. The original verification history MUST remain auditable.

---

# 18. Cross-document consistency rule

If a future document introduces a shortcut that appears to bypass one of these constraints, the shortcut is invalid unless the authoritative protocol semantics are explicitly amended.

Examples of invalid shortcuts include:

```text
AI score → automatically feasible
PATCH status → automatically verified
cached graph → canonical physical truth
transaction completed → automatically physical completion
successful API request → automatically valid domain state
```

None of these equivalences are valid in CRR.

---

# 19. Conformance statement

A CRR implementation should be able to state:

```text
CRR protocol version: 0.1.1
Conformance level: 0–5
Supported canonical objects: ...
Supported lifecycle transitions: ...
Supported evidence classes: ...
Supported routing constraints: ...
Decision providers: ...
Known implementation limitations: ...
```

A system MUST NOT claim full CRR conformance merely because it exposes the `/v1` endpoints or uses the canonical object names.

Semantic behavior is what matters.
