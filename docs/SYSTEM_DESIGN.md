# CRR System Design

**Status:** Reference system design
**Version:** 0.1

## 1. System thesis

CRR is a proposed computational infrastructure layer that allows the physical economy to discover, route, transform, trade, execute and verify resource flows across organizational boundaries.

The fundamental primitive is **Resource State**, not waste.

```text
Resource Identity
      ↓
Resource State
      ↓
Transformation
      ↓
New Resource State
```

## 2. Objectives

- Represent physical reality as computable protocol objects.
- Connect supply, demand and organizational capabilities.
- Compute executable routes rather than simple matches.
- Separate deterministic truth from probabilistic/advisory reasoning.
- Coordinate transactions and physical execution.
- Capture evidence and verified outcomes.
- Expose the system through stable APIs so other companies can build on it.

## 3. Non-goals

CRR is not initially a waste marketplace, logistics company, recycling company, ERP, consumer recycling application, generic chatbot, blockchain system, principal trading operation, or global ontology project.

## 4. Architecture principles

1. Physical reality is authoritative.
2. ResourceState is the physical primitive.
3. Historical physical facts are append-only in meaning.
4. Hard constraints are deterministic.
5. AI is advisory and bounded.
6. Every important decision is explainable and auditable.
7. APIs are first-class interfaces.
8. Human approval is the initial execution boundary.
9. Evidence distinguishes claims from verified outcomes.
10. Implementations must be replaceable without changing protocol semantics.

## 5. Logical architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     PHYSICAL ECONOMY                        │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ RESOURCE / DEMAND / CAPABILITY REALITY                      │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ RESOURCE + TRANSFORMATION GRAPH                             │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ ROUTING ENGINE                                               │
│ hard constraints → feasibility → economics → optimization  │
└─────────────────────────────┬───────────────────────────────┘
                              ↓
              ┌───────────────┴───────────────┐
              ↓                               ↓
       Deterministic Engine                 Jev
              └───────────────┬───────────────┘
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
                       NETWORK UPDATE
```

## 6. Canonical domain objects

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
Transformation consumes ResourceState / produces ResourceState
Route starts from ResourceState and terminates at Demand or target state
Opportunity proposes Route
Transaction executes Opportunity
Execution produces Evidence
Evidence verifies claims
Event records state changes
Decision records decision provenance
```

## 7. Resource architecture

A Resource is the stable identity/lineage container. ResourceState represents a particular physical state.

A state may change through reservation, movement, receipt, processing or transformation, but historical physical facts must not be destructively rewritten.

Splits and merges preserve lineage.

## 8. Demand architecture

Demand specifies what a participant needs:

- required resource state
- quantity
- quality
- location
- timing
- pricing constraints
- certifications
- regulatory constraints
- substitution tolerance
- status

Expired, paused, cancelled or fulfilled demand is not active matching demand.

## 9. Capability architecture

Capabilities describe what an organization can physically do:

- accepted inputs
- processes
- outputs
- capacity
- operating windows
- locations
- minimum batches
- costs
- certifications
- regulatory eligibility

## 10. Transformation architecture

A transformation is a versioned, testable relationship between input and output states. It declares yield bounds, losses/residuals, capacity, duration, cost and requirements.

A transformation template is not proof of actual execution.

## 11. Graph architecture

The graph is a projection of canonical reality. It connects:

- organizations
- resources
- states
- demands
- capabilities
- transformations
- locations
- routes
- transactions
- evidence

A dedicated graph database is not required for the MVP. A relational graph projection is sufficient and easier to audit.

## 12. Routing architecture

Routing has five conceptual layers:

1. Hard constraints.
2. Physical feasibility.
3. Economic feasibility.
4. Optimization.
5. Contextual decision support.

The output is a set of feasible candidate routes with traceable calculations and invalidation reasons.

## 13. Jev architecture

Jev is an advisory decision provider behind a stable provider interface.

```text
Decision Engine
   ├── deterministic rules
   ├── optimization
   ├── evidence validation
   └── DecisionProvider
          └── JevProvider
```

Jev cannot:

- override hard constraints;
- create physical facts;
- fabricate evidence;
- mutate canonical state directly;
- execute transactions;
- invent costs, quantities, capacities or regulations.

Every decision records provider/model/version, context hash, candidate set, result, rationale, uncertainty and escalation status.

## 14. Opportunity and transaction architecture

```text
Route
 ↓
Opportunity
 ↓
Offer
 ↓
Agreement
 ↓
Transaction
```

The state machine is explicit. Arbitrary status mutation is not permitted for authoritative lifecycle changes.

## 15. Execution architecture

Execution coordinates:

- pickup
- shipment
- receipt
- inspection
- processing
- delivery
- acceptance

Execution records planned versus actual values. Completion alone does not imply verification.

## 16. Evidence and trust

Evidence has a type, subject, issuer, submitter, timestamp, content reference/hash, verification status and verifier.

Verification is an authorized act and cannot be self-declared by an untrusted client.

## 17. Economics

Authoritative economic calculations use exact decimal semantics or integer minor units.

```text
Gross value
+ buyer payment
+ other value
- transport
- processing
- handling
- certification
- taxes/fees where applicable
= Net economic outcome
```

The calculation version and assumptions are retained so results can be reproduced.

## 18. Events

Events are immutable protocol records. Recommended envelope fields:

- event_id
- event_type
- event_version
- occurred_at
- published_at
- aggregate_type
- aggregate_id
- aggregate_version
- actor
- organization_id
- correlation_id
- causation_id
- idempotency_key
- payload
- provenance
- schema_version

Delivery may be at least once; consumers must deduplicate by event ID.

## 19. API architecture

Canonical API surface:

`/v1/organizations` · `/actors` · `/locations` · `/resources` · `/resource-states` · `/demands` · `/capabilities` · `/transformations` · `/routes` · `/decisions` · `/opportunities` · `/offers` · `/agreements` · `/transactions` · `/executions` · `/evidence` · `/economic-models` · `/events` · `/webhooks`

Mutations use idempotency where retries can repeat effects and optimistic concurrency for stale writes.

## 20. Reference implementation

Recommended reference stack:

- Python + FastAPI + Pydantic
- PostgreSQL + PostGIS
- object storage for evidence
- Redis plus worker queue for asynchronous processing
- React + TypeScript
- OpenAPI
- adapter-based Jev integration
- CI with unit, integration, contract and end-to-end tests

This is a reference implementation, not a protocol dependency.

## 21. Repository architecture

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
    failure/
  docs/
    protocol/
    architecture/
    data-flow/
    system-design/
    adr/
  infra/
  scripts/
```

## 22. MVP architecture

The MVP is narrow in commercial scope but broad in architectural coverage. It should prove one complete resource loop with 1–3 resource categories, one industrial cluster, and a small set of real organizations.

The MVP must demonstrate:

```text
real resource
→ canonical state
→ demand
→ capability
→ transformation
→ route
→ decision
→ opportunity
→ transaction
→ execution
→ evidence
→ verified outcome
```

## 23. Scaling architecture

Scale by network density, not by premature infrastructure complexity:

```text
one cluster
→ multiple companies
→ more resource classes
→ more processors
→ logistics
→ verified transactions
→ more clusters
→ Saudi
→ GCC
→ MENA
→ global
```

## 24. Final architecture invariant

If PostgreSQL, the graph projection, the UI, the AI provider, the cloud provider, or the worker implementation is replaced, the protocol semantics and canonical physical history must remain valid.
