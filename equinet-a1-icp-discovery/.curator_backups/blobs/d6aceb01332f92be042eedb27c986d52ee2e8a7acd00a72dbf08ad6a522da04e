# Direct REST Company and Person staging worker

Use this reference when operating or debugging `scripts/stage_twenty_rest.py`.

## Purpose and contracts

The worker stages a persisted `a1.discovery-result.v1` as one Twenty Company and, when `name` is present, one linked Person. It keeps lead rows and public contact values out of model-visible stdout. It validates:

- `configurations/crm/twenty-company-field-manifest-v1.json`;
- `configurations/crm/twenty-person-field-manifest-v1.json`;
- `references/staging-payload.schema.json`;
- `references/staging-index.schema.json`.

Required environment: `TWENTY_API_KEY`; optional `TWENTY_BASE_URL`, `TWENTY_REQUEST_DELAY`, and `TWENTY_API_TIMEOUT`.

## Mapping

| n8n fields | Twenty result |
|---|---|
| `business_name` + `name` | Company named `business_name`; linked Person named `name`; phone/email on Person |
| `name` only | Company named `name`; linked Person named `name`; phone/email on Person |
| `business_name` only | Company named `business_name`; no Person; phone/email on Company |
| neither | `blocked_missing_company_name`; no records |

Twenty `name` is a FULL_NAME composite. Preserve the complete source value without guessing:

```json
{"name":{"firstName":"<complete n8n name>","lastName":""}}
```

## Execution

```text
python3 skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_rest.py --check-connection

python3 skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_rest.py \
  --input <discovery-result.json> \
  --overlays <lane-overlays.json> \
  --field-manifest configurations/crm/twenty-company-field-manifest-v1.json \
  --person-field-manifest configurations/crm/twenty-person-field-manifest-v1.json \
  --output-dir <new-empty-directory>
```

Never reuse a non-empty staging directory.

## Company-first algorithm

1. Validate source, overlays, both live manifests and aggregate E.164 phone safety.
2. Scan soft-deleted Companies; exact fingerprint/domain matches are held.
3. Preflight active Companies by fingerprint, verified domain, and conservative name/location.
4. Create or UUID-update exactly one Company, then read it back and reconcile.
5. If `name` is absent, finish as `company_staged_no_person_required`.
6. If `name` is present, use the verified Company UUID as Person `companyId`.
7. Scan soft-deleted People within that Company, then preflight active People in this precedence: exact email, exact phone, normalized full name.
8. Ambiguity or a soft-deleted exact match produces `company_staged_person_possible_match` with no Person write.
9. Create or UUID-update one Person, read it back, and verify both fields and relation.
10. After verified Person reconciliation, clear any pre-existing Company phone/email copies and verify that migration.
11. Finalize one entity-aware terminal disposition per fingerprint.

## Write safety and recovery

Persist a write-attempt marker before every POST/PATCH. Never retry a Company or Person write after transport loss, a malformed success response, 5xx ambiguity, or failed reconciliation. Preserve the verified Company if Person staging fails. Use a separately named corrective run only after proving no uncertain write will be repeated.

Terminal states:

- `company_staged_person_staged`
- `company_staged_no_person_required`
- `company_staged_person_possible_match`
- `company_staged_person_sync_failed`
- `company_possible_match`
- `company_sync_failed`
- `blocked_missing_company_name`

## REST filter and soft-delete rules

Twenty uses `field[operator]:value`. JSON-quote exact values so commas do not become filter separators. Composite fields use dotted paths. Soft-deleted records may still reserve unique values; never restore, delete, update, or recreate them automatically.

## Audit artifacts

Retain batch and phone validation, soft-delete scans, Company plans/lookups/decisions/write markers/read-backs/reconciliation, Person scans/decisions/write markers/read-backs/reconciliation, optional Company-contact migration, item disposition, and final staging index. Files are mode `0600`; directories are mode `0700`.

## Verification

```text
python3 -m py_compile \
  skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_company.py \
  skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_rest.py
python3 -m unittest -v \
  skills/crm/evidence-aware-crm-staging/tests/test_stage_twenty_company.py \
  skills/crm/evidence-aware-crm-staging/tests/test_stage_twenty_rest.py
```

Coverage must include all four name combinations, exclusive contact routing, Company-before-Person ordering, relation read-back, rerun idempotency, active ambiguity, soft-deleted People, Company success plus Person failure, no retry of uncertain Person writes, and migration of existing Company contact values.
