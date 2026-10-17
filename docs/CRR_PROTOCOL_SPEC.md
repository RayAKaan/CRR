# CRR Protocol Specification

**Status:** Proposed protocol specification
**Version:** 0.1
**Protocol name:** Computational Resource Routing (CRR)

## 1. Scope

CRR defines an implementation-independent protocol for representing, discovering, routing, executing and verifying physical resource flows across organizational boundaries.

CRR is a proposed technical/category specification, not an existing external industry standard.

## 2. Normative principles

The terms MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are normative.

1. ResourceState MUST be the canonical representation of physical state.
2. Physical history MUST NOT be destructively overwritten.
3. Quantities MUST use exact decimal semantics.
4. Money MUST use exact decimal or minor-unit semantics.
5. Units MUST be explicit and canonicalizable.
6. Every canonical physical state MUST have provenance and authority context.
7. Transformations MUST define input/output requirements and yield/loss rules.
8. Hard constraints MUST be deterministic.
9. An infeasible route MUST NOT become feasible because of an AI recommendation.
10. Jev MUST be advisory only.
11. Evidence MUST be attributable and verifiable.
12. Events MUST be immutable and consumers MUST be idempotent.
13. Tenant boundaries MUST be enforced.
14. Derived projections MUST remain derived.
15. Implementations MUST be replaceable without changing protocol meaning.

## 3. Canonical objects

`Organization`, `Actor`, `Location`, `Resource`, `ResourceState`, `Demand`, `Capability`, `Transformation`, `Route`, `Decision`, `Opportunity`, `Offer`, `Agreement`, `Transaction`, `Execution`, `Evidence`, `EconomicModel`, `Event`.

## 4. Resource semantics

A Resource identifies a physical lineage/container. ResourceState identifies a specific physical condition, quantity, location, ownership/custody and quality at a point or interval in time.

Historical states are immutable in meaning. Corrections are represented through new versions/events.

## 5. Lineage

Splits and merges MUST preserve lineage.

For a split:

```text
Parent quantity ≈ sum(child quantities) + declared loss/residual
```

For a merge:

```text
sum(parent quantities) ≈ child quantity + declared loss/residual
```

Tolerance MUST be explicit and appropriate to the resource/transformation.

## 6. Transformation

A transformation defines:

- accepted input state specifications;
- output specifications;
- process;
- yield bounds;
- loss/residual model;
- capacity;
- duration;
- cost;
- quality effects;
- regulatory requirements.

A definition is not evidence of occurrence.

## 7. Route

A Route is a proposed executable sequence of transport and transformation legs.

A route MUST:

- start from a valid source state;
- reference valid demand or target state;
- contain ordered legs;
- satisfy hard constraints;
- respect capacity and timing;
- maintain state compatibility between legs;
- expose economics and assumptions;
- have an explicit validity/expiry boundary.

## 8. Decision

A Decision records reasoning over a fixed candidate set and context.

The selected option MUST be among candidates and MUST survive deterministic validation.

Confidence is not proof. Rationale is not canonical truth.

## 9. Jev

Jev is an optional decision provider. The protocol MUST continue operating when Jev is unavailable.

Jev MUST NOT:

- override hard constraints;
- invent facts;
- set verification status;
- directly mutate canonical state;
- execute physical or commercial actions.

## 10. Opportunity and transaction

Opportunity proposes a route and commercial possibility. Transaction records an accepted commercial execution.

Transaction lifecycle:

`DISCOVERED → PROPOSED → ACCEPTED → AGREED → SCHEDULED → EXECUTING → COMPLETED → VERIFIED`

Opportunity lifecycle:

`DISCOVERED → VALIDATING → PROPOSED → APPROVED | REJECTED | EXPIRED`

## 11. Evidence

Evidence lifecycle:

`CLAIMED → SUBMITTED → VERIFIED | REJECTED | DISPUTED`

Clients MUST NOT self-assign verified status without authorized verification.

## 12. Events

Events are immutable. Event delivery MAY be at least once. Consumers MUST deduplicate using `event_id` and preserve required aggregate ordering using `aggregate_version`.

## 13. Protocol versioning

Major breaking changes require a new major protocol/API version. Additive changes SHOULD remain backward compatible. Schema versions MUST be explicit.

## 14. Conformance

- Level 0: schema conformance
- Level 1: reality conformance
- Level 2: routing conformance
- Level 3: transaction conformance
- Level 4: evidence/verification conformance
- Level 5: full network conformance

## 15. Reference API

Canonical versioned REST resources are exposed under `/v1/` in the reference implementation. The protocol does not require REST; an independent implementation may use another transport if semantics remain equivalent.

## 16. Protocol evolution

The protocol should be extended by additive capabilities and namespaced extensions rather than silently redefining existing semantics.

## 17. Core protocol loop

```text
RESOURCE REALITY
→ MARKET REALITY
→ CAPABILITY REALITY
→ GRAPH
→ TRANSFORMATIONS
→ ROUTES
→ DECISIONS
→ OPPORTUNITY
→ TRANSACTION
→ EXECUTION
→ EVIDENCE
→ VERIFIED OUTCOME
```
