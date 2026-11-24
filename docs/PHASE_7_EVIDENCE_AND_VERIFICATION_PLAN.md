# Phase 7 — Evidence and Independent Verification

**Status:** PLANNED  
**Scope:** PRs #37–#40  
**Predecessor:** Phase 6 Physical Execution Foundation (PR #36 merged; main CI green)  
**Protocol position:** Execution → Evidence → Verified Outcome → Network Learning

## Objective

Introduce the evidence and verification layers that turn actor-reported operational claims into independently reviewable, attributable outcomes. Evidence records preserve source provenance and integrity. Verification decisions are explicit, authorized, versioned and traceable to the exact evidence and operational facts reviewed.

Phase 7 does not implement network learning, financial settlement, title transfer, autonomous dispatch or external regulatory attestation.

## Normative boundaries

1. **Evidence is not a claim and is not a decision.** An Evidence record describes a submitted artifact or observation and its provenance. It does not establish that an ExecutionOperation occurred or that a ResourceState is true.
2. **Verification is a separate decision.** A submitted artifact remains unverified until an authorized verifier records a decision against a specific subject and evidence set.
3. **Separation of duties.** The evidence submitter, originating operational reporter and verifier are distinct identities. A verifier cannot verify evidence they submitted or the operation they reported.
4. **Append-only history.** Evidence metadata, review actions and verification decisions are immutable. Corrections, withdrawals, supersessions, re-openings and reversals are new records referencing prior records with actor, time and reason.
5. **Tenant isolation.** Every read, write, relationship and storage operation is scoped to the owning organization. Cross-tenant identifiers must not disclose whether a record exists.
6. **Integrity.** Every artifact has a server-computed SHA-256 digest, byte length, media type and storage identity. Client-supplied digests are never trusted.
7. **First-class provenance.** Records identify submitter, source type/reference, optional observation time, submission time, related Execution/operation/Transaction and declared chain-of-custody metadata. Client-declared provenance is distinguished from server-observed metadata.
8. **Authoritative time.** Observation, submission, review and decision timestamps are separate, timezone-aware values.
9. **No implicit state mutation.** Evidence submission, review and verification do not mutate ResourceState, ownership, custody, Reservation, Transaction or Execution. A VerifiedOutcome is a separate immutable object.
10. **Deterministic concurrency.** Mutations require idempotency keys and optimistic version preconditions. Duplicate, stale, unauthorized and conflicting transitions fail deterministically.
11. **Storage safety.** Artifact storage is behind a narrow interface. Object keys are server-generated; filenames are display metadata only. Downloads require tenant authorization. Raw bytes and secrets are excluded from logs and outbox payloads.
12. **Outbox consistency.** Canonical writes and their outbox events commit atomically. Events contain identifiers and safe metadata, never artifact bytes or credentials.
13. **Bounded trust claims.** A verifier decision records a conclusion under a named policy; it is not a legal, regulatory, scientific or cryptographic attestation beyond that policy.
14. **No destructive deletion.** Evidence referenced by reviews or decisions cannot be hard-deleted through the API. Retention and legal deletion require a later audit-preserving policy.

## Domain concepts

### Evidence

An Evidence aggregate is tenant-scoped and references exactly one subject in the initial implementation. Supported subjects are an Execution, ExecutionOperation or ExecutionException.

The model records a stable ID, subject type and ID, artifact metadata, SHA-256 digest, byte length, media type, storage key, submitter, source/provenance metadata, optional observed time, submitted time, status and version.

Evidence status describes only the submission lifecycle (for example SUBMITTED, WITHDRAWN or SUPERSEDED). It must not encode VERIFIED or REJECTED; those are verification decisions.

Evidence may be a file or a structured observation. Structured observations use a versioned, validated schema and retain the same provenance/integrity guarantees. Arbitrary client-controlled object graphs are not authoritative facts.

### Evidence review

Review records are append-only and attributable. They capture reviewer, action, rationale, timestamp, and the evidence version/digest reviewed. Actions may request clarification, flag a conflict or recommend a decision. Review is not verification unless the actor has the explicit verifier permission and submits through the verification command.

### Verification and VerifiedOutcome

A VerificationDecision is immutable and records tenant and subject identity; decision (VERIFIED, NOT_VERIFIED or INCONCLUSIVE); policy/rule-set identifier and version; exact evidence IDs, versions and digests considered; verifier identity and authorization context; rationale and decision time; and supersession/reversal linkage.

A VerifiedOutcome is a separate immutable record created only by a VERIFIED decision. It references the exact decision and subject version. NOT_VERIFIED and INCONCLUSIVE decisions do not create outcomes. Later decisions may supersede prior decisions; historical decisions and outcomes remain queryable and are never rewritten.

The initial policy is human-verifier-led. Automated scoring, quorum verification, external trust registries and dispute adjudication are deferred.

## PR plan

| PR | Scope | Required acceptance |
|---|---|---|
| **#37 — planning** | This plan, domain boundaries, lifecycle and test gates | Scope agrees with Phase 6 boundaries and protocol object model |
| **#38 — Evidence foundation** | Evidence domain contract, immutable metadata/provenance, SQLAlchemy models, migration, storage interface and safe local test adapter | Domain invariants; digest/size/media validation; tenant-scoped foreign keys; append-only behavior; migration upgrade/downgrade/rebuild; storage path and integrity tests |
| **#39 — Evidence workflow/API** | Upload and authorized retrieval, submit/withdraw/supersede lifecycle, subject linking, review records, idempotency, ETags/concurrency, outbox events and API documentation | Tenant isolation; upload/download authorization; server-computed digest; no path traversal; bounded streaming/size limits; duplicate/stale/unauthorized transition tests; immutable review history; PostgreSQL conformance |
| **#40 — Verification and closure** | Verifier scopes and separation-of-duty enforcement, immutable decisions, VerifiedOutcome, supersession/reversal semantics, end-to-end integration and closure documentation | Self-verification rejected; exact evidence version/digest pinned; only VERIFIED creates an outcome; non-verified decisions do not; no ResourceState mutation; transactional outbox; full regression and PostgreSQL CI green |

## API contract targets

Final route names and schemas must follow existing CRR API envelope, scope, idempotency, pagination and ETag conventions.

- POST /v1/evidence — submit an artifact and bind it to one supported subject.
- GET /v1/evidence — tenant-scoped evidence list with bounded filters and pagination.
- GET /v1/evidence/{id} — metadata and immutable history.
- GET /v1/evidence/{id}/content — authorized artifact retrieval; never expose storage keys.
- POST /v1/evidence/{id}/withdraw — append a withdrawal action when policy permits.
- POST /v1/evidence/{id}/supersessions — submit replacement evidence while preserving the original.
- POST /v1/evidence/{id}/reviews — append a review action against a specific evidence version/digest.
- POST /v1/verifications — record an authorized decision against a subject and exact evidence set.
- GET /v1/verifications and GET /v1/verifications/{id} — tenant-scoped decision history.
- GET /v1/verified-outcomes and GET /v1/verified-outcomes/{id} — query immutable verified outcomes.

The implementation must reconcile these targets with current router registration and authorization conventions before coding. No endpoint may bypass the domain transition contract.

## Authorization model

Add narrow scopes compatible with existing naming: evidence:read, evidence:submit, evidence:review, verification:decide and verified_outcome:read.

Existing organization/actor authentication remains authoritative. A verifier must be active, belong to the same organization, hold verification:decide, and be distinct from the submitter and originating reporter for the subject under review. Scope checks are necessary but not sufficient; domain-level separation-of-duty checks are mandatory.

## Persistence and migration requirements

- Use existing SQLAlchemy Base, AwareDateTime, composite tenant foreign keys and migration conventions.
- Add explicit uniqueness/check constraints and indexes for tenant-scoped lookup, subject relationships and aggregate versions.
- Keep artifact bytes outside relational rows. Persist only server-generated storage keys and verified metadata.
- Storage writes must be atomic from the API's perspective: never commit an Evidence row pointing to missing content. Handle orphaned content safely if the database transaction fails.
- Migration downgrade must not silently discard evidence data. If safe downgrade is impossible after evidence exists, document and enforce a guarded downgrade or retain data-bearing tables. Migrations must not delete stored blobs as an incidental side effect.

## Required quality gates

Every PR must pass the repository CI workflow: Ruff lint and formatting, mypy (including new domain modules in configured targets), full pytest regression suite, Alembic upgrade/downgrade/rebuild and model-alignment checks, and PostgreSQL conformance.

Phase-specific tests must cover:
- digest correctness, empty/oversized payloads, media-type validation and storage failure cleanup;
- immutable metadata/history and supersession/withdrawal semantics;
- tenant isolation for metadata, content and subject relationships;
- upload/download authorization and non-disclosure of storage paths;
- idempotency and optimistic concurrency;
- reviews pinned to exact evidence versions/digests;
- submitter/reporter/verifier separation of duties;
- VERIFIED, NOT_VERIFIED and INCONCLUSIVE outcomes;
- superseded/reversed decisions without historical mutation;
- no ResourceState, Execution, Transaction, Reservation, ownership or custody mutation;
- outbox atomicity and safe event payloads.

No PR may merge until its own PR CI is green. After each merge, verify main CI before starting the next PR. The final PR must leave all four PRs merged and main CI green.

## Explicitly deferred

- Automated authenticity scoring, OCR/ML judgment or autonomous verification.
- Multi-verifier quorum, challenge windows, appeals and full dispute adjudication.
- Legal title, custody, payment, settlement, invoicing or regulatory attestation.
- External object-storage providers, public evidence URLs and cross-organization sharing.
- ResourceState mutation based on verification; this requires a later explicit transition policy.
- Network learning, trust/reputation scoring and incentives based on verified outcomes.
- Retention schedules, legal holds, privacy erasure and jurisdiction-specific evidence policies.

## Completion definition

Phase 7 is complete only when PRs #37–#40 are merged in order, each PR's required CI passes, post-merge main CI passes after each merge, and tests prove the evidence/verification boundaries above. A submitted artifact or operational report must never be described as a verified fact merely because it exists in the system.
