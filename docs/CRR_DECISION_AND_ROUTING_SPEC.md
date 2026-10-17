# CRR Decision and Routing Specification

**Status:** Normative decision/routing specification
**Version:** 0.1

## 1. Purpose

The routing system determines which physically, operationally, legally/safely and economically feasible path a resource can take toward a valid demand or target state.

The system does not answer only “who wants this?” It answers:

> What is the highest-value executable next state or route that can be justified by the available physical, economic, operational and regulatory evidence?

## 2. Routing pipeline

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

## 3. Hard constraints

Hard constraints are authoritative blockers. Examples:

- insufficient quantity;
- incompatible physical state;
- unavailable capability;
- insufficient capacity;
- impossible location/time requirement;
- expired demand;
- missing required authorization/certification;
- prohibited material/process combination;
- ownership/custody conflict;
- impossible transformation yield;
- invalid unit conversion;
- required evidence absent where execution cannot proceed.

A route failing a hard constraint MUST be infeasible.

## 4. Candidate route structure

A route contains:

- source state;
- target demand/state;
- ordered legs;
- resource transformations;
- transport requirements;
- capacity reservations;
- timing;
- regulatory checks;
- economic model;
- decision reference;
- validity/expiry.

## 5. Leg semantics

Transport legs move a physical state between locations.

Transformation legs change the state.

Each leg consumes an expected input and produces an expected output. The next leg must accept the previous leg's output.

## 6. Capacity

Available capacity is capacity minus existing commitments/reservations for the relevant time window.

The routing engine MUST NOT schedule more than available capacity.

## 7. Quantity and yield

All quantity calculations use exact decimal semantics.

Transformation output is bounded by declared yield rules. Where conservation applies:

```text
inputs = outputs + declared losses/residuals ± explicit tolerance
```

Silent loss is invalid.

## 8. Geographic routing

Distance and travel time are computed from authoritative locations and routing assumptions. A client or model cannot alter distance merely to make economics pass.

## 9. Economics

The economic model must be reproducible:

```text
value
- acquisition/payment
- transport
- processing
- handling
- certification
- applicable fees/taxes
= net outcome
```

All assumptions and calculation versions are recorded.

Negative net value is a valid mathematical outcome but is economically infeasible when the selected objective requires non-negative value.

## 10. Ranking

Only feasible routes may be ranked.

A reference ranking may combine:

- economic value;
- distance/time;
- confidence/evidence quality;
- capacity reliability;
- transformation risk;
- delivery timing;
- quality compatibility.

Weights and scoring versions MUST be recorded.

A score can rank feasible options but cannot make an infeasible option feasible.

## 11. Jev decision layer

Jev may assist with:

- semantic compatibility;
- ambiguous classification;
- candidate prioritization;
- qualitative tradeoffs;
- contextual interpretation;
- escalation decisions;
- explanation.

Jev may not:

- override deterministic constraints;
- invent facts;
- create capacity;
- invent regulations;
- fabricate evidence;
- execute transactions;
- write canonical physical state directly.

## 12. Decision contract

A decision request contains:

- decision type;
- candidate IDs;
- authoritative constraints;
- evidence references;
- economic context;
- uncertainty;
- allowed action space.

A decision result contains:

- selected candidate;
- rationale;
- confidence;
- uncertainty;
- evidence references;
- provider/model/version;
- escalation flag;
- validation result.

The selected candidate must belong to the original candidate set and must pass deterministic validation.

## 13. Fallback

If Jev is unavailable:

1. deterministic routing continues where possible;
2. contextual decisions may fall back to deterministic rules;
3. ambiguous cases escalate to human review;
4. the system never silently changes hard-constraint semantics.

## 14. Route lifecycle

`GENERATED → VALIDATING → FEASIBLE | INFEASIBLE → SELECTED | REJECTED → EXPIRED`

The exact implementation may use separate status and validation fields, but the semantic distinction must remain.

## 15. Route expiry

A route becomes stale when relevant source state, demand, capability, price, capacity, authorization or other validity assumptions change beyond the recorded validity boundary.

Stale routes must be revalidated before execution.

## 16. Routing invariants

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
13. Decision candidates are fixed and auditable.
14. Jev cannot create facts.
15. Expired routes cannot execute.
16. Actual execution cannot be inferred from a route alone.
