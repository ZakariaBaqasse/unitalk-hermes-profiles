# Twenty live write compatibility

Company behavior was validated on 2026-08-31 and 2026-09-01. The People field contract was confirmed on 2026-09-04 and is persisted in `configurations/crm/twenty-person-field-manifest-v1.json`.

- `create_many_companies` returned `result: [{"id":"<uuid>"}]`, not a `record` or one-element `records` envelope. Use the returned UUID only to issue `find_one_company(select:["*"])`; normalize and reconcile the read-back.
- Formatted US phone values such as `270-402-4174` were rejected with `Provided phone number is invalid ...`. The staging-plan producer needs an API-valid phone representation (typically E.164) or must omit the field before the write operation is emitted.
- Twenty stores a written US E.164 phone as a national `primaryPhoneNumber` plus `primaryPhoneCallingCode: "+1"`; reconciliation must compare their canonical concatenation.
- **URL round-trip behavior:** Twenty strips a final `/` from `domainName.primaryLinkUrl` and `sourceUrl.primaryLinkUrl` on Company read-back. Until the deterministic reconciler explicitly accepts this equivalence and has regression coverage, retain the exact expected/returned URLs in `reconciliation-error.json`, set the terminal disposition to `sync_failed`, and never retry the create. This affected both website and source URLs in the 2026-09-01 run.
- A `sync_failed` disposition is required for payload rejections, reconciliation mismatches, and a write whose remote outcome cannot be confirmed. Do not retry an uncertain create.

This is API compatibility guidance, not a substitute for a tested helper update.

## Direct REST findings — 2026-09-01

- REST list filters use the DSL `field[operator]:value`, not JSON-encoded GraphQL filter objects. Exact string values must be JSON-quoted. For example, `name[eq]:"J. T. Holub, APF"` is valid, while leaving the comma-bearing name unquoted makes the parser treat the suffix as another filter token and return HTTP 400.
- Composite fields use dotted paths, for example `domainName.primaryLinkUrl[eq]:"https://example.com"`.
- A live read-only capability probe confirmed quoted fingerprint, composite-domain, and suffix-bearing Company-name filters with HTTP 200.
- Twenty's default Company list excludes soft-deleted rows, while unique indexes can still reserve their `discoveryFingerprint` or domain values. Seven explicit duplicate-create rejections from one batch were reconciled read-only to seven exact soft-deleted fingerprint matches. The same read-only corrective preview found that all five pre-write name-filter failures in that batch also had one exact soft-deleted fingerprint match. The worker must scan `deletedAt[is]:NOT_NULL` before writes and hold exact soft-deleted matches as `possible_match`; it must not automatically restore, hard-delete, update, or recreate them.
- A direct REST create returns the Company under `body.data.createCompany`; read-back remains mandatory before `staged`.

## People REST contract — 2026-09-04

- Endpoint collection: `/rest/people`; UUID-scoped read/update: `/rest/people/{id}`.
- `name` is `FULL_NAME`. The mapper sends the complete unsplit n8n `name` as `firstName` and `lastName: ""`.
- `emails` and `phones` are composite fields with maximum one value; send one primary value and an empty additional-values array.
- Link the Person only after Company reconciliation by sending the verified Company UUID as `companyId`.
- Person read-back must verify the Person ID, contact/name fields and `companyId` relation before the lead can be `company_staged_person_staged`.
- The deterministic mock integration suite exercises Person create/update, relation read-back, rerun idempotency, soft-deleted holds, partial failure, no automatic retry after an uncertain write, and existing Company-contact migration. A mock test is not a claim about a specific live write execution.