# CRR API Contract

**Status:** Proposed normative external API contract  
**Version:** v1 / schema 0.1  
**Protocol:** Computational Resource Routing (CRR)  
**Role:** Defines observable API behavior for a conforming CRR implementation.

> The API contract is implementation-independent. FastAPI/OpenAPI is the reference implementation choice, not a protocol requirement.

---

# 1. Purpose

This document defines how applications and independent implementations interact with CRR through a reference versioned API.

The API must preserve the protocol's most important distinctions:

```text
CANONICAL REALITY
      ↓
DERIVED COMPUTATION
      ↓
PLAN
      ↓
EXECUTION
      ↓
EVIDENCE
      ↓
VERIFICATION
```

The API must not allow a client to bypass domain invariants merely because the request is syntactically valid.

---

# 2. API principles

1. API behavior MUST preserve protocol semantics.
2. Authorization MUST occur before protected disclosure.
3. Domain validation MUST occur before canonical mutation.
4. Lifecycle changes MUST use validated transitions.
5. Retriable mutations MUST be idempotent where required.
6. Stale writes MUST NOT silently overwrite newer state.
7. Verification MUST require authorization.
8. Derived data MUST remain distinguishable from canonical data.
9. Planned, actual, claimed, and verified values MUST remain distinct.
10. API versioning MUST protect backward compatibility.
11. Long-running operations MUST expose observable status.
12. Errors MUST be machine-readable and traceable.
13. Tenant isolation MUST be enforced for every protected object.

---

# 3. Base API

Reference prefix:

`/v1`

Recommended content type:

`application/json`

Timestamps use RFC 3339 and are canonicalized to UTC.

Binary evidence should use a file/object upload mechanism rather than embedding arbitrary binary data inside JSON resources.

---

# 4. IDs

IDs are opaque and stable.

Reference prefixes include:

```text
org_
act_
loc_
res_
rst_
dem_
cap_
trn_
rte_
dec_
opp_
off_
agr_
txn_
exe_
evd_
eco_
evt_
wh_
```

These prefixes are implementation conventions. The protocol requires stable unique identity, not semantic interpretation of an ID string.

---

# 5. Timestamps

Authoritative timestamps SHOULD be RFC 3339/ISO 8601 values in UTC.

Example:

`2026-10-17T12:34:56Z`

Naive timestamps MUST NOT be used for authoritative cross-system event or execution semantics.

---

# 6. Precision

Authoritative physical and monetary values MUST NOT use binary floating point.

Recommended quantity representation:

```json
{
  "quantity": {
    "value": "100.000",
    "unit": "t"
  }
}
```

Recommended monetary representation:

```json
{
  "amount": "125000.00",
  "currency": "SAR"
}
```

Implementations may use minor-unit integers internally, provided the API preserves exact semantics.

---

# 7. Common response envelope

Single-object response:

```json
{
  "data": {},
  "meta": {
    "request_id": "req_123",
    "api_version": "v1",
    "schema_version": "0.1"
  }
}
```

Collection response:

```json
{
  "data": [],
  "pagination": {
    "cursor": "cursor_123",
    "has_more": true,
    "limit": 50
  },
  "meta": {
    "request_id": "req_123",
    "api_version": "v1",
    "schema_version": "0.1"
  }
}
```

---

# 8. Error contract

Canonical error shape:

```json
{
  "error": {
    "code": "RESOURCE_VALIDATION_FAILED",
    "category": "VALIDATION_FAILURE",
    "severity": "BLOCKING",
    "message": "Human-readable explanation",
    "details": [
      {
        "rule_id": "VAL-RST-001",
        "path": "quantity.value",
        "message": "Quantity must be non-negative"
      }
    ],
    "retryable": false,
    "request_id": "req_123",
    "correlation_id": "corr_123",
    "object_id": "rst_123"
  }
}
```

Errors should identify:

- code;
- category;
- severity;
- message;
- rule ID;
- field/path;
- retryability;
- request ID;
- correlation ID;
- affected object where applicable.

---

# 9. HTTP semantics

Reference status codes:

| Status | Meaning |
|---|---|
| `200` | Successful read/action |
| `201` | Resource created |
| `202` | Accepted asynchronous operation |
| `204` | Successful no-content operation |
| `400` | Malformed request |
| `401` | Unauthenticated |
| `403` | Authenticated but unauthorized |
| `404` | Not found / intentionally indistinguishable object |
| `409` | Domain conflict |
| `412` | Concurrency precondition failed |
| `422` | Semantic validation failure |
| `429` | Rate limit |
| `500` | Internal failure |
| `502` | Upstream failure |
| `503` | Service unavailable |
| `504` | Upstream timeout |

Implementations should avoid leaking cross-tenant object existence through error differences.

---

# 10. Authentication

Reference implementation:

- OAuth2/OIDC for human/user access;
- API keys or service accounts for machine access.

Representative scopes:

```text
organizations:read
organizations:write
resources:read
resources:write
demands:read
demands:write
capabilities:read
capabilities:write
transformations:read
transformations:write
routes:compute
decisions:read
decisions:write
transactions:read
transactions:write
execution:read
execution:write
evidence:read
evidence:write
evidence:verify
events:read
webhooks:manage
```

Exact scope naming can evolve, but authorization must remain least-privilege.

---

# 11. Authorization and tenant isolation

Authorization MUST be evaluated before returning protected object data.

Every request is evaluated against:

```text
IDENTITY
  ↓
ORGANIZATION
  ↓
ROLE / SCOPE
  ↓
OBJECT OWNERSHIP / ACCESS POLICY
  ↓
OPERATION
```

Cross-organization relationships do not imply unrestricted access.

Sensitive economics, evidence, proprietary process information, and private capabilities must be protected.

---

# 12. Common object metadata

Canonical API objects generally expose:

- `id`;
- `type`;
- `schema_version`;
- `version`;
- `status`;
- ownership/organization context where applicable;
- `created_at`;
- `updated_at`;
- creator/updater attribution where applicable;
- `provenance`;
- `metadata`;
- `extensions`.

Not every field applies to every object.

---

# 13. Idempotency

Retriable mutation requests MUST support `Idempotency-Key` where duplicate effects are possible.

Rules:

1. same key + equivalent request = same logical effect;
2. same key + materially different request = conflict;
3. a timeout followed by retry must not create duplicate transactions/reservations/effects;
4. idempotency records must remain available for the policy-defined retention period.

Idempotency does not replace domain validation.

---

# 14. Optimistic concurrency

Mutable objects should expose a version.

A reference implementation can use:

```http
ETag: "version-7"
If-Match: "version-7"
```

A stale write should return `412 Precondition Failed` or an equivalent explicit concurrency error.

The server MUST NOT silently overwrite newer canonical state.

---

# 15. Pagination, filtering, sorting

Collections should support:

- `limit`;
- cursor pagination;
- stable sort;
- filtering;
- time ranges;
- status filters.

Cursor pagination is preferred for large mutable collections.

Domain filters may include:

### Resources

- resource type;
- state type;
- location;
- quantity range;
- availability;
- status.

### Demands

- required state;
- location;
- active window;
- status.

### Capabilities

- input/output;
- location;
- capacity;
- status.

### Routes

- source;
- target;
- feasibility;
- score;
- generated time;
- expiry.

### Transactions

- participant;
- status;
- date range.

---

# 16. Canonical endpoints

```text
GET/POST        /v1/organizations
GET/PATCH       /v1/organizations/{id}
GET/POST        /v1/actors
GET/PATCH       /v1/actors/{id}
GET/POST        /v1/locations
GET/PATCH       /v1/locations/{id}
GET/POST        /v1/resources
GET/PATCH       /v1/resources/{id}
GET/POST        /v1/resource-states
GET/PATCH       /v1/resource-states/{id}
POST            /v1/resource-states/{id}/transitions
GET/POST        /v1/demands
GET/PATCH       /v1/demands/{id}
GET/POST        /v1/capabilities
GET/PATCH       /v1/capabilities/{id}
GET/POST        /v1/transformations
GET/PATCH       /v1/transformations/{id}
POST            /v1/routes/compute
GET             /v1/routes/{id}
POST            /v1/routes/{id}/validate
GET/POST        /v1/decisions
GET             /v1/decisions/{id}
POST            /v1/decisions/{id}/accept
POST            /v1/decisions/{id}/reject
POST            /v1/decisions/{id}/escalate
GET/POST        /v1/opportunities
GET/PATCH       /v1/opportunities/{id}
GET/POST        /v1/offers
GET/PATCH       /v1/offers/{id}
GET/POST        /v1/agreements
GET/PATCH       /v1/agreements/{id}
GET/POST        /v1/transactions
GET/PATCH       /v1/transactions/{id}
GET/POST        /v1/executions
GET/PATCH       /v1/executions/{id}
GET/POST        /v1/evidence
GET/PATCH       /v1/evidence/{id}
GET/POST        /v1/economic-models
GET             /v1/events
GET             /v1/events/{id}
GET/POST        /v1/webhooks
GET/PATCH/DELETE /v1/webhooks/{id}
```

---

# 17. Organization API

Organization creation establishes a participant boundary.

It must validate:

- stable identity;
- operating status;
- jurisdiction metadata;
- creator authorization.

Organization updates cannot silently transfer ownership of historical physical resources.

---

# 18. Actor API

Actors represent human or service identities.

The API must support attribution and role/scope enforcement.

An actor cannot escalate its own permissions through object mutation.

---

# 19. Location API

Locations must validate:

- coordinate ranges;
- address structure where provided;
- jurisdiction;
- provenance;
- uncertainty where material.

Locations referenced by routing must be sufficiently precise for the requested calculation.

---

# 20. Resource API

Resource creation establishes identity and lineage.

Physical facts belong primarily to ResourceState.

A resource with history should be archived/deactivated rather than destructively deleted.

Example conceptual object:

```json
{
  "data": {
    "id": "res_123",
    "type": "resource",
    "resource_type": "ALUMINUM_SCRAP",
    "organization_id": "org_123",
    "current_state_id": "rst_123",
    "status": "ACTIVE",
    "schema_version": "0.1",
    "version": 3
  }
}
```

---

# 21. ResourceState API

ResourceState is the physical truth boundary.

Conceptual object:

```json
{
  "data": {
    "id": "rst_123",
    "resource_id": "res_123",
    "state_type": "MIXED_ALUMINUM_SCRAP",
    "quantity": {
      "value": "100.000",
      "unit": "t"
    },
    "location_id": "loc_123",
    "effective_at": "2026-10-17T12:00:00Z",
    "provenance": {}
  }
}
```

Material state transitions should use explicit transition operations.

---

# 22. Demand API

Demand creation requires:

- organization;
- required state specification;
- quantity semantics;
- acceptance criteria;
- timing;
- relevant quality/regulatory conditions.

Only active demand can participate in normal routing.

Demand allocation must respect remaining quantity.

---

# 23. Capability API

Capability registration requires:

- organization;
- accepted input specifications;
- output/process definition;
- capacity;
- operating constraints;
- relevant certifications;
- regulatory eligibility.

Revoked, expired, or suspended capabilities cannot be selected for execution.

---

# 24. Transformation API

Transformation definitions are versioned.

They must expose:

- input specifications;
- output specifications;
- yield/loss model;
- capacity;
- duration;
- cost;
- quality effects;
- regulatory requirements.

A transformation definition is not an execution record.

---

# 25. Routing API

`POST /v1/routes/compute`

Conceptual request:

```json
{
  "source_resource_state_id": "rst_123",
  "target_demand_id": "dem_123",
  "constraints": {},
  "optimization": {
    "objective": "NET_ECONOMIC_VALUE"
  },
  "decision_mode": "OPTIONAL"
}
```

Conceptual response:

```json
{
  "data": {
    "routes": [
      {
        "id": "rte_123",
        "feasibility": "FEASIBLE",
        "economic_model_id": "eco_123",
        "score": "0.912",
        "expires_at": "2026-10-18T12:00:00Z"
      }
    ]
  }
}
```

A long-running calculation MAY return `202 Accepted` with an operation/job reference.

---

# 26. Decision API

Decision objects record:

- decision type;
- candidate set;
- context;
- constraints;
- selected candidate;
- rationale;
- confidence;
- uncertainty;
- evidence references;
- provider/model/version;
- escalation.

The API must validate the decision result against authoritative facts before acceptance.

Jev credentials and provider internals are not client-controlled fields.

---

# 27. Opportunity API

An Opportunity references:

- route;
- participants;
- source/target;
- economics;
- requirements;
- validity;
- decision context.

It cannot be approved if the underlying route is infeasible or stale.

---

# 28. Offer API

Offers contain explicit commercial terms:

- proposer;
- recipient;
- quantity;
- price/currency;
- timing;
- route/delivery terms;
- conditions;
- expiry.

Acceptance must reference the exact offer/version accepted.

---

# 29. Agreement API

Agreements record accepted obligations and may reference external legal documents.

An agreement must not silently change accepted terms. Amendments must be explicit and auditable.

---

# 30. Transaction API

Transactions connect commercial commitments to physical execution.

Lifecycle transitions are explicit:

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

The API must prevent illegal transitions.

---

# 31. Execution API

Execution records:

- transaction;
- ordered steps;
- responsible parties;
- planned values;
- actual values;
- timestamps;
- exceptions;
- evidence references.

Actual values cannot silently overwrite planned values.

---

# 32. Evidence API

Evidence records claims and artifacts.

Conceptual object:

```json
{
  "data": {
    "id": "evd_123",
    "type": "WEIGHBRIDGE_RECORD",
    "subject_refs": ["exe_123"],
    "submitted_by": "act_123",
    "captured_at": "2026-10-18T08:30:00Z",
    "content_hash": "sha256:...",
    "verification_status": "SUBMITTED"
  }
}
```

Clients cannot force `VERIFIED` without authorized verification.

---

# 33. EconomicModel API

Economic models retain:

- currency;
- value/cost components;
- assumptions;
- calculation version;
- source references;
- computed timestamp;
- result.

Historical calculations remain reproducible.

---

# 34. Event API

Events are immutable.

`GET /v1/events` should support filtering by:

- event type;
- aggregate type/id;
- organization;
- occurred-at range;
- cursor.

There should be no ordinary update operation for protocol events.

---

# 35. Webhook API

Webhook subscriptions contain:

- webhook ID;
- organization;
- URL;
- subscribed event types;
- status;
- secret metadata;
- timestamps.

Payloads should be signed.

Delivery is at least once.

Retries should use controlled backoff.

Repeatedly failing endpoints may be dead-lettered or disabled.

Webhook failure MUST NOT change canonical transaction truth.

---

# 36. Bulk ingestion API

A reference implementation may expose:

```text
POST /v1/ingestion/jobs
GET  /v1/ingestion/jobs/{id}
```

An ingestion job may contain:

- source file/reference;
- schema mapping;
- validation mode;
- dry-run flag;
- idempotency key;
- import policy.

The job should report:

- accepted records;
- rejected records;
- warnings;
- row-level errors;
- created/updated object IDs.

Bulk ingestion MUST use the same domain validation as normal API mutation.

---

# 37. File/evidence upload

Binary evidence may be uploaded using a pre-signed object-store URL or equivalent mechanism.

The protocol-facing API should record:

- content reference;
- content type;
- size where relevant;
- content hash;
- ownership/access scope;
- evidence association.

The API should not expose storage credentials to clients.

---

# 38. Asynchronous operations

Long-running operations such as route computation or bulk ingestion may return:

```http
202 Accepted
```

with:

```json
{
  "data": {
    "job_id": "job_123",
    "status": "QUEUED",
    "operation": "ROUTE_COMPUTATION"
  }
}
```

The operation status must remain observable.

An async worker must still execute the same domain validation as synchronous operations.

---

# 39. State transition API

Authoritative lifecycle changes should not be performed by arbitrary:

```http
PATCH { "status": "VERIFIED" }
```

Instead, use explicit transitions such as:

```text
POST /resource-states/{id}/transitions
POST /decisions/{id}/accept
POST /decisions/{id}/reject
POST /decisions/{id}/escalate
```

The transition endpoint validates:

- current state;
- requested transition;
- actor permission;
- prerequisites;
- invariants;
- concurrency.

---

# 40. Routing/decision API boundary

The API must not expose Jev as an unrestricted canonical-state mutation interface.

Instead:

```text
API
 ↓
Decision Request
 ↓
Deterministic Validation
 ↓
DecisionProvider
 ↓
JevProvider
 ↓
Structured Decision
 ↓
Validation
 ↓
Accepted Decision
```

The provider receives only the context required for the decision.

---

# 41. API security invariants

1. Authorization precedes disclosure.
2. Authorization precedes mutation.
3. Tenant isolation applies to nested relationships.
4. Verification cannot be client-forced.
5. Provider credentials never enter client-controlled fields.
6. Sensitive economics require appropriate scopes.
7. Evidence access follows object permissions.
8. Audit records are protected from ordinary mutation.
9. API keys/service credentials have bounded scopes.
10. Rate limiting cannot be used as a substitute for authorization.

---

# 42. API versioning

The reference API uses `/v1`.

Within v1:

- additive response fields are preferred;
- existing semantics must remain stable;
- breaking changes require v2;
- schema versions remain explicit;
- deprecated behavior should have a documented migration path.

Clients should ignore unknown response fields.

Servers should reject ambiguous or invalid request fields unless they are inside a declared extension namespace.

---

# 43. Extension model

Namespaced extensions are allowed:

```json
{
  "extensions": {
    "com.example.extension": {
      "custom_field": "value"
    }
  }
}
```

Extensions MUST NOT alter the meaning of core fields or lifecycle states.

---

# 44. API observability

Every response should expose a request ID.

Operations spanning multiple services should carry a correlation ID.

Events should preserve causation where possible.

Long-running jobs should expose progress/status where meaningful.

The API should make it possible to trace:

```text
REQUEST
 ↓
DOMAIN COMMAND
 ↓
STATE CHANGE
 ↓
EVENT
 ↓
ASYNC WORK
 ↓
DECISION
 ↓
EXECUTION
```

---

# 45. API conformance levels

### Level 0 — Schema

Canonical endpoints, object structure, precision, IDs, timestamps, and errors.

### Level 1 — Reality

ResourceState, demand, capability, provenance, lifecycle, and tenant controls.

### Level 2 — Routing

Transformation and route computation with deterministic feasibility.

### Level 3 — Transaction

Opportunity, offer, agreement, transaction, and execution.

### Level 4 — Evidence

Evidence, verification, dispute, and verified outcome.

### Level 5 — Network

Events, webhooks, developer integration, and ecosystem interoperability.

---

# 46. API invariants

- API inputs pass domain validation before canonical acceptance.
- Arbitrary lifecycle status mutation cannot bypass state machines.
- Verification cannot be client-forced.
- Route feasibility is independent of AI.
- Resource lineage is preserved.
- Retriable mutations are idempotent where required.
- Stale writes are rejected.
- Request/correlation IDs are observable.
- Async operations expose status.
- Planned, actual, claimed, and verified values remain distinct.
- Events remain immutable.
- Breaking changes require a new major API version.
- Derived graph/ranking data cannot become canonical through the API.
- Cross-tenant data cannot leak through filtering, relationships, events, or errors.

---

# 47. Relationship to other CRR documents

- `CRR_PROTOCOL_SPEC.md` defines protocol semantics.
- `CRR_DOMAIN_MODEL.md` defines canonical objects.
- `SYSTEM_DESIGN.md` defines reference architecture.
- `CRR_DATA_FLOW_ARCHITECTURE.md` defines data movement.
- `CRR_DECISION_AND_ROUTING_SPEC.md` defines route/decision behavior.
- `CRR_VALIDATION_AND_INVARIANTS.md` defines validation/invariant enforcement.

The API is an external contract over those semantics, not a competing source of truth.
