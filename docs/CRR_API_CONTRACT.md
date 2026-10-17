# CRR API Contract

**Status:** Proposed external API contract
**Version:** v1 / schema 0.1

## 1. Purpose

This document defines observable API behavior for a conforming CRR implementation. It does not prescribe database, framework, cloud or UI technology.

## 2. Base API

Reference API prefix:

`/v1`

Recommended content type:

`application/json`

Timestamps use RFC 3339 and are canonicalized to UTC.

## 3. IDs

IDs are opaque and stable. Prefixes such as `org_`, `res_`, `rst_`, `dem_`, `cap_`, `trn_`, `rte_`, `dec_`, `opp_`, `txn_`, `exe_`, `evd_` are reference conventions, not semantic requirements.

## 4. Common response envelope

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

Collection responses include cursor pagination.

## 5. Error envelope

```json
{
  "error": {
    "code": "RESOURCE_VALIDATION_FAILED",
    "message": "Human-readable explanation",
    "details": [],
    "retryable": false,
    "request_id": "req_123",
    "correlation_id": "corr_123"
  }
}
```

Validation details SHOULD include rule ID and field path.

## 6. Authentication

Reference implementation supports OAuth2/OIDC for user access and API keys/service accounts for machine access.

Representative scopes:

`resources:read`, `resources:write`, `routes:compute`, `transactions:write`, `evidence:verify`, `events:read`, `webhooks:manage`.

## 7. Tenant isolation

Authorization MUST be evaluated before returning object data. Unauthorized cross-tenant objects SHOULD be indistinguishable from nonexistent objects where appropriate.

## 8. Idempotency

Retriable mutation requests MUST support `Idempotency-Key`. Repeating a request with the same key and equivalent payload MUST NOT produce duplicate domain effects.

## 9. Concurrency

Reference implementations SHOULD use `ETag`/`If-Match` or an equivalent version precondition. Stale writes return a concurrency conflict rather than silently overwriting newer state.

## 10. Canonical endpoints

```text
GET/POST     /v1/organizations
GET/PATCH    /v1/organizations/{id}
GET/POST     /v1/actors
GET/PATCH    /v1/actors/{id}
GET/POST     /v1/locations
GET/PATCH    /v1/locations/{id}
GET/POST     /v1/resources
GET/PATCH    /v1/resources/{id}
GET/POST     /v1/resource-states
GET/PATCH    /v1/resource-states/{id}
POST         /v1/resource-states/{id}/transitions
GET/POST     /v1/demands
GET/PATCH    /v1/demands/{id}
GET/POST     /v1/capabilities
GET/PATCH    /v1/capabilities/{id}
GET/POST     /v1/transformations
GET/PATCH    /v1/transformations/{id}
POST         /v1/routes/compute
GET          /v1/routes/{id}
POST         /v1/routes/{id}/validate
GET/POST     /v1/decisions
GET          /v1/decisions/{id}
POST         /v1/decisions/{id}/accept
POST         /v1/decisions/{id}/reject
POST         /v1/decisions/{id}/escalate
GET/POST     /v1/opportunities
GET/PATCH    /v1/opportunities/{id}
GET/POST     /v1/offers
GET/PATCH    /v1/offers/{id}
GET/POST     /v1/agreements
GET/PATCH    /v1/agreements/{id}
GET/POST     /v1/transactions
GET/PATCH    /v1/transactions/{id}
GET/POST     /v1/executions
GET/PATCH    /v1/executions/{id}
GET/POST     /v1/evidence
GET/PATCH    /v1/evidence/{id}
GET/POST     /v1/economic-models
GET           /v1/events
GET           /v1/events/{id}
GET/POST      /v1/webhooks
GET/PATCH/DELETE /v1/webhooks/{id}
```

## 11. Resource API semantics

Resource creation establishes identity and lineage. Physical facts belong primarily to ResourceState.

Resource state mutations that affect authoritative lifecycle MUST use explicit transitions rather than arbitrary status patches.

## 12. Demand API

Demand creation requires a valid required-state specification, quantity semantics, acceptance criteria and lifecycle status. Only active demand is eligible for routing.

## 13. Capability API

Capability registration requires accepted inputs, process/output definitions, capacity and relevant operating constraints. Revoked or expired capabilities cannot be selected for execution.

## 14. Transformation API

Transformation definitions are versioned. They must expose input/output specifications and yield/loss semantics. A transformation definition is not an execution record.

## 15. Routing API

`POST /v1/routes/compute` accepts source state, target demand, constraints and optimization preferences.

The response contains candidate routes, deterministic feasibility results, economic models, invalidation reasons and optional decision references.

Long-running computation MAY return `202 Accepted` with a job reference.

## 16. Decision API

Decision objects record candidate IDs, context, constraints, selected option, rationale, confidence, uncertainty, provider/model/version and escalation.

The API MUST validate decision output against authoritative facts before acceptance.

## 17. Opportunity API

Opportunities reference routes and participants and contain commercial/economic context. They cannot become approved if mandatory route, demand, capability or authorization conditions are invalid.

## 18. Offer and agreement APIs

Offers contain explicit quantity, price, timing, route and conditions. Agreements record accepted terms and obligations.

## 19. Transaction API

Transactions link commercial agreement to physical resource and execution. Lifecycle transitions are explicit and auditable.

## 20. Execution API

Execution records ordered steps, responsible parties, planned/actual values, exceptions and evidence.

## 21. Evidence API

Evidence records claims and artifacts. Clients cannot set `VERIFIED` without the required authorization and verification process.

## 22. Economic model API

Economic models use exact numeric semantics and retain calculation version, assumptions and components.

## 23. Events

`GET /v1/events` supports filtering by event type, aggregate, organization and time range. Events are immutable.

## 24. Webhooks

Webhook delivery is at least once. Payloads SHOULD be signed. Failed deliveries are retried according to policy and may be dead-lettered or disabled.

Webhook failure MUST NOT change canonical transaction truth.

## 25. Bulk ingestion

A reference implementation may expose an ingestion-job API for CSV/XLSX/JSON. Imported objects must pass the same domain validation as API-created objects and retain provenance.

## 26. HTTP semantics

`200` success · `201` created · `202` accepted · `204` no content · `400` malformed · `401` unauthenticated · `403` unauthorized · `404` not found · `409` domain conflict · `412` concurrency precondition · `422` semantic validation · `429` rate limited · `500` internal · `502/503/504` upstream/service failure.

## 27. Precision

Authoritative quantities and monetary amounts MUST NOT use binary floating-point representations. JSON examples should represent decimal values as strings or use an explicitly exact numeric representation.

## 28. Extensions

Implementations may provide namespaced extensions without altering core semantics. Example:

```json
{
  "extensions": {
    "com.example.extension": {}
  }
}
```

## 29. API invariants

- Authorization precedes disclosure.
- Canonical physical state cannot be mutated into an invalid state.
- Verification cannot be client-forced.
- Route feasibility is independent of AI.
- Resource lineage is preserved.
- Mutations are retry-safe where required.
- Request and correlation IDs are observable.
- Async operations expose status.
- Planned, actual, claimed and verified values remain distinct.
- Breaking API changes require a new major version.
