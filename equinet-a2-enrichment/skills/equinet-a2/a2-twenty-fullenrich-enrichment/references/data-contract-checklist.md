# Data Contract Checklist

Use this checklist before implementing or activating the Twenty–FullEnrich workflow. All artifacts must carry schema/version identifiers, stable IDs, UTC timestamps, an input hash, idempotency key, explicit terminal status, errors/warnings and an audit reference.

## Twenty boundary

1. **Workspace metadata snapshot** — Company and Person object IDs, internal field names, types, enum options, nullability, uniqueness, relation cardinality and API permissions. Verify against live metadata.
2. **Company pull request/result** — eligible A2 statuses, enrichment version, cursor and bounded limit; Company snapshot with nullable domain, structured address and zero-to-many linked People.
3. **Company claim request/receipt** — expected prior status, `processing` transition, run ID, processing timestamp and read-back. A failed claim blocks provider calls.
4. **Write plan** — explicit create/update/associate/status operations, expected baselines, source decision IDs and write-set hash. Only validated plans may reach the push connector.
5. **Write receipt and reconciliation** — operation-level IDs/statuses plus post-write Company, Person and association read-back. API success without semantic read-back match is not success.

## FullEnrich boundary

6. **Lookup request/result** — known Twenty Person, Company identifiers, provider request ID, exact returned title/employer/profile URL and terminal state. Lookup does not supply trusted email/phone.
7. **Search request/result** — segment, approved role keys, maximum two, and organisation identifiers. Domain is optional; at least one provider-supported identifier is required. Preserve all returned source titles.
8. **Contact Enrichment request/job/result** — selected People only; request `contact.work_emails` and `contact.phones`, never personal email. Record async job ID, polls, timeout, retries, terminal result, usage and cost. Isolate incidental personal email.

## LLM decision boundary

9. **Lookup decision packet/decision** — identity, Company match, role priority, freshness, retention and Search-required decision, all tied to packet IDs and evidence refs.
10. **Candidate packet/selection decision** — per-candidate Company attribution, role priority, duplicate result, retain/reject rationale and zero-to-two selected provider IDs.
11. **Field merge decision** — baseline, provider proposal, evidence ref and one allowed action: `add`, `update_a2_owned`, `no_change`, `preserve_manual`, `hold_conflict`, `privacy_review`, `reject_invalid`.

Validators must reject invented IDs or values, changed source titles, more than two new selections, non-primary selections, Company mismatches, unresolved duplicates and decisions without evidence references.

## State and audit

12. **Company state model** — at least `not_enriched`, `processing`, `enriched`, `partially_enriched`, `completed_no_target`, `retryable_error`, `blocked`, with allowed transitions, stale-lock recovery and version-based reprocessing.
13. **Person state model** — separate identity, role/freshness, Company-match and enrichment states plus FullEnrich person ID and timestamps.
14. **Run ledger** — Company stage, artifact paths/hashes, provider jobs, Twenty operations, retries and terminal outcomes for interruption-safe resume.
15. **Audit/consumption** — actor/profile, model, scripts, endpoints, policy versions, evidence, decisions, retries, credits/cost and external-action receipts.

## Pre-code evidence required

- Live Twenty metadata and field mapping.
- API-key read and approved write scopes.
- FullEnrich request/response fixtures, including domainless Search.
- Verified polling/status endpoint for asynchronous Contact Enrichment.
- Approved target-role, stale-person, deduplication and Company-attribution policies.
- Synthetic create/update/associate/read-back fixture before any existing record is modified.
