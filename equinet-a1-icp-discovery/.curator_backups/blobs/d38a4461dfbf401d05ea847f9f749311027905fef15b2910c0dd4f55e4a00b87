# Equinet A1 Enrichment Hardening — Implementation Verification

## Result

- Status: **PASSED — offline contract and regression validation**
- Verified at: 2026-09-10
- Live post-change n8n/Twenty execution: **not performed**
- `external_writes_performed: false`

The earlier production acceptance remains evidence for the broader production path. It is not live execution evidence for the changed V2 enrichment state machine.

## Implemented behavior

- `a1.website-enrichment-state.v2` separates research, assessment and scoring.
- Verified research without assessment inputs becomes `assessment_pending`; it is non-terminal and blocks overlay generation and Twenty staging.
- Mutable lead transitions require owner, lease ID, expiry and compare-and-swap revision.
- Expired claims are safely reclaimable using the revision advertised by `next_batch`.
- Research and assessment use separate versioned contracts.
- Classification, qualification and confidence submissions are validated against their dedicated schemas and may reference only accepted evidence IDs.
- Accepted website evidence is preserved during assessment updates.
- Evidence-backed `out_of_scope` is explicit and produces a blocked overlay rather than an unexplained unscored record.
- Verified-unscored fallback requires explicit terminal assessment failure, a structured failure code, persisted matching failure history and non-retryable/exhausted retry handling.
- Unexplained verified `NOT_SCORED` overlays are rejected by the router, CRM mapper, REST stager and final-index consumption gate.
- V1 state migration writes a separate V2 artifact and does not rerun n8n or repeat CRM writes.
- Website overlay provenance is retained through lane staging, combined-index merge and V2 polling-ticket consumption.
- New V2 polling tickets support configuration snapshots, drift detection, monitor identity and finite action budgets; legacy V1 tickets remain readable.
- Weaker unscored rediscovery does not clear an existing complete scored Company assessment.

## Versioned policy and skill updates

- Runtime policy: `4.3.0`
- Public website enrichment policy: `1.5.0`
- `post-n8n-public-website-enrichment`: `3.1.0`
- `equinet-n8n-discovery-control`: `4.1.0`
- `evidence-aware-crm-staging`: `4.3.0`

ICP criteria, scoring weights, approved countries, source permissions, no-outreach controls and the Company-plus-optional-linked-Person boundary were not changed.

## Main changed paths

### Profile and policy

- `SOUL.md`
- `configurations/operations/a1-runtime-policy-v1.yaml`
- `configurations/evidence/public-website-enrichment-policy-v1.yaml`
- `scripts/validate_source_execution_policy.py`

### Website enrichment

- `skills/post-n8n-public-website-enrichment/SKILL.md`
- `skills/post-n8n-public-website-enrichment/scripts/manage_enrichment.py`
- `skills/post-n8n-public-website-enrichment/scripts/route_and_overlay.py`
- `skills/post-n8n-public-website-enrichment/scripts/migrate_state_v1_to_v2.py`
- `skills/post-n8n-public-website-enrichment/scripts/verify_hardening.py`
- `skills/post-n8n-public-website-enrichment/scripts/test_enrichment_state_v2.py`
- `skills/post-n8n-public-website-enrichment/scripts/test_migrate_state_v1_to_v2.py`
- `skills/post-n8n-public-website-enrichment/scripts/test_hardening_acceptance.py`
- `skills/post-n8n-public-website-enrichment/tests/test_manage_enrichment.py`
- `skills/post-n8n-public-website-enrichment/tests/test_route_and_overlay.py`
- `skills/post-n8n-public-website-enrichment/references/enrichment-state-v2.schema.json`
- `skills/post-n8n-public-website-enrichment/references/enrichment-results.schema.json`
- `skills/post-n8n-public-website-enrichment/references/assessment-submissions-v2.schema.json`
- `skills/post-n8n-public-website-enrichment/references/explicit-fallback-v2.schema.json`
- `skills/post-n8n-public-website-enrichment/references/staging-overlays.schema.json`
- `skills/post-n8n-public-website-enrichment/references/twenty-company-overlays-v2.schema.json`
- `skills/post-n8n-public-website-enrichment/references/combined-staging-index.schema.json`

### Controller

- `skills/system-operations/equinet-n8n-discovery-control/SKILL.md`
- `skills/system-operations/equinet-n8n-discovery-control/references/two-lane-processing-runbook.md`
- `skills/system-operations/equinet-n8n-discovery-control/references/poll-ticket-v2.schema.json`
- `skills/system-operations/equinet-n8n-discovery-control/scripts/poll_ticket.py`
- `skills/system-operations/equinet-n8n-discovery-control/scripts/build_configuration_snapshot.py`
- `skills/system-operations/equinet-n8n-discovery-control/tests/test_poll_ticket.py`

### Twenty staging

- `skills/crm/evidence-aware-crm-staging/SKILL.md`
- `skills/crm/evidence-aware-crm-staging/references/two-lane-enrichment-staging.md`
- `skills/crm/evidence-aware-crm-staging/references/staging-index.schema.json`
- `skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_company.py`
- `skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_rest.py`
- `skills/crm/evidence-aware-crm-staging/scripts/test_overlay_admission_v2.py`
- `skills/crm/evidence-aware-crm-staging/tests/test_stage_twenty_company.py`

## Verification commands and results

Primary command:

```bash
.venv/bin/python skills/post-n8n-public-website-enrichment/scripts/verify_hardening.py
```

Result:

```text
status: passed
command_count: 9
tests_run: 87
json_schemas_validated: 21
schema_error_count: 0
yaml_documents_validated: 2
policy_error_count: 0
external_writes_performed: false
```

Suites included:

| Suite | Tests | Result |
|---|---:|---|
| Normal V2 enrichment and routing tests | 21 | Passed |
| Standalone V2 state tests | 7 | Passed |
| Cross-component hardening acceptance tests | 8 | Passed |
| V1-to-V2 migration tests | 1 | Passed |
| Poll-ticket V1/V2 controller tests | 16 | Passed |
| Twenty Company/Person staging mock tests | 30 | Passed |
| Overlay admission tests | 4 | Passed |
| **Total** | **87** | **Passed** |

Additional validations in the primary command:

- Python compilation of the affected scripts and tests: passed.
- All 21 discovered JSON Schemas: parsed and passed Draft 2020-12 schema validation.
- Runtime policy and website-enrichment policy YAML: parsed successfully.
- Policy invariants: passed.
- `scripts/validate_source_execution_policy.py`: passed.
- Real local classification, qualification, confidence and deterministic scoring wrappers executed successfully for one claimed fixture lead; resulting ICP score was 80 using scoring model `1.1.0`.
- Local mock Twenty tests exercised Company-first/optional-Person staging, duplicate handling, read-back reconciliation and preservation of existing scored fields. No external CRM was contacted.

Machine-readable detailed output:

- `skills/post-n8n-public-website-enrichment/references/hardening-verification-report.json`

## No-write fixture coverage

- no website candidate;
- verified research followed by mandatory assessment;
- actual deterministic scored path;
- evidence-backed out-of-scope path;
- explicit exhausted assessment failure;
- pending verified record blocked from overlay/staging;
- overlay provenance through lane and combined indexes;
- V2 ticket consumption gate;
- existing scored Company fields preserved from weaker unscored rediscovery;
- V1 state migration and V1 polling-ticket compatibility.

## Remaining limitations

- No live post-change n8n discovery or Twenty write/read-back was performed.
- Historical run artifacts containing `verified_site_unscored_missing_pipeline_inputs` were deliberately preserved unchanged as audit records.
- The previously staged Lexington records have not been rescored or updated by this hardening task.
- Linked-Person live validation remains limited to the evidence already recorded by the profile; this task added no new live Person write evidence.
- Human review remains mandatory before A2 or outreach.
