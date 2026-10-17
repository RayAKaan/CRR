# CRR Data Flow Architecture

**Status:** Reference architecture / design specification
**Version:** 0.1
**Scope:** Computational Resource Routing (CRR)

> CRR is a proposed computational infrastructure layer for physical-resource circulation. It is not an established industry standard. This document defines the reference data-flow architecture for the proposed CRR system.

## 1. Purpose

CRR exists to represent physical resources, discover demand and capabilities, compute feasible resource routes, coordinate commercial execution, and verify real-world outcomes.

The canonical loop is:

```text
PHYSICAL REALITY
    ↓
RESOURCE INGESTION
    ↓
RESOURCE STATE
    ↓
DEMAND + CAPABILITY REALITY
    ↓
RESOURCE / TRANSFORMATION GRAPH
    ↓
ROUTE GENERATION
    ↓
DETERMINISTIC VALIDATION
    ↓
DECISION SUPPORT
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
NETWORK UPDATE
```

## 2. Data authority

The system distinguishes canonical reality from derived computation.

| Data class | Meaning | Authority |
|---|---|---|
| Raw | Original submitted input | Source record |
| Canonical | Normalized protocol object | CRR domain authority |
| Derived | Graph, ranking, cache, embedding | Regenerable computation |
| Planned | Intended future action | Route/transaction plan |
| Actual | Observed execution fact | Execution record/evidence |
| Claimed | Submitted assertion | Unverified |
| Verified | Accepted evidence-backed fact | Authorized verifier |

Derived data can never replace canonical truth.

## 3. Ingestion flow

```text
CSV / XLSX / JSON / API / MANUAL
        ↓
RAW CAPTURE
        ↓
SCHEMA VALIDATION
        ↓
AUTHORIZATION
        ↓
NORMALIZATION
        ↓
UNIT + LOCATION + CLASSIFICATION VALIDATION
        ↓
PROVENANCE ATTACHMENT
        ↓
RESOURCE / RESOURCE STATE
```

Raw inputs are retained. Invalid records are rejected or quarantined; they are never silently converted into authoritative reality.

## 4. Market flow

Demand and capabilities enter through the same validation boundary.

```text
DEMAND
→ required state
→ quantity
→ quality
→ location
→ timing
→ price constraints
→ certifications
→ regulation

CAPABILITY
→ accepted inputs
→ process
→ outputs
→ capacity
→ location
→ operating window
→ certification
→ regulation
```

## 5. Transformation flow

A transformation is a declared rule describing how an input state may become an output state.

```text
INPUT STATE
   ↓
TRANSFORMATION REQUIREMENTS
   ↓
PROCESS
   ↓
YIELD / LOSS / RESIDUAL MODEL
   ↓
OUTPUT STATE(S)
```

A transformation definition is not proof that the transformation occurred. Execution and evidence establish actual outcomes.

## 6. Routing flow

```text
SOURCE STATE
    ↓
CANDIDATE DEMANDS
    ↓
CANDIDATE CAPABILITIES
    ↓
CANDIDATE TRANSFORMATIONS
    ↓
TRANSPORT + PROCESSING LEGS
    ↓
HARD CONSTRAINT FILTER
    ↓
FEASIBILITY
    ↓
ECONOMICS
    ↓
OPTIMIZATION
    ↓
OPTIONAL JEV ADVISORY DECISION
    ↓
RANKED FEASIBLE ROUTES
```

A route violating a hard constraint is invalid regardless of score, model confidence, or Jev output.

## 7. Commercial flow

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

An opportunity is not a transaction. A transaction is not execution. Execution is not verification.

## 8. Execution and evidence flow

```text
TRANSACTION
 ↓
EXECUTION PLAN
 ↓
PICKUP / SHIPMENT
 ↓
RECEIPT
 ↓
PROCESSING
 ↓
OUTPUT
 ↓
EVIDENCE
 ↓
VERIFICATION
 ↓
VERIFIED OUTCOME
```

Typical evidence includes weighbridge records, laboratory reports, pickup records, delivery records, processing records, and buyer acceptance.

## 9. Event flow

All material state changes produce immutable events.

```text
CANONICAL WRITE
    ↓
EVENT RECORD
    ↓
OUTBOX / EVENT PUBLISHER
    ↓
WEBHOOKS / PROJECTIONS / ANALYTICS / INTEGRATIONS
```

Consumers must be idempotent because event delivery may be at least once.

## 10. Feedback loop

Verified outcomes improve future routing without rewriting history.

```text
VERIFIED OUTCOME
 ↓
OBSERVED YIELD
OBSERVED COST
OBSERVED DISTANCE/TIME
OBSERVED QUALITY
OBSERVED FAILURE
 ↓
NETWORK KNOWLEDGE
 ↓
BETTER ROUTES
```

## 11. Reference implementation

The protocol is implementation-independent. A recommended implementation is FastAPI/Pydantic, PostgreSQL/PostGIS, object storage for evidence, Redis plus a worker queue for asynchronous work, React/TypeScript for the reference UI, and an adapter-based Jev integration.

No database, graph database, cloud, frontend framework, or AI provider is a protocol requirement.

## 12. End-to-end example

```text
Factory A has 100 t of Resource State S1
        ↓
CRR validates quantity, state, ownership, location and evidence
        ↓
Demand D1 requires S1 or an accepted transformed state
        ↓
Capability C1 can transform S1 → S2
        ↓
Routing engine evaluates transport + transformation + delivery
        ↓
Hard constraints pass
        ↓
Economics are calculated deterministically
        ↓
Decision layer ranks feasible alternatives
        ↓
Opportunity O1 created
        ↓
Offer → Agreement → Transaction
        ↓
Execution records shipment and processing
        ↓
Evidence is submitted and verified
        ↓
Outcome O1 is verified
        ↓
Observed facts feed the network
```

## 13. Data-flow invariants

1. Physical reality is authoritative.
2. Raw inputs remain traceable.
3. Canonical state cannot be silently overwritten.
4. Derived projections are regenerable.
5. Planned, actual, claimed and verified values remain distinct.
6. Every material mutation is attributable.
7. Hard constraints are deterministic.
8. AI cannot fabricate physical facts.
9. Evidence cannot become verified without authorized verification.
10. Every transaction outcome must be traceable to its resource lineage.
