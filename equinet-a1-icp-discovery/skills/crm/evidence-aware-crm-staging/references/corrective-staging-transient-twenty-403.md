# Corrective staging after a transient Twenty 403 preflight abort

Live-validated 2026-09-17 on ticket-1375 (Weatherford, TX horse_owner, lead `place:ChIJB3822Mv9UYYR_MavO04aocU`).

## Symptom

The discovery ticket shows `lifecycle_status: succeeded`, `consumed_at` and `delivered_at` set, but the user reports the lead is not in Twenty. The consumed `final-staging-index.json` dispositions show:

- `company_disposition: company_sync_failed`
- `reason: soft_deleted_preflight_failed`
- `write_attempted: false`, `company_id: null`, `duplicate_preflight_completed: false`
- item artifact `soft-deleted-scan-error.json` containing `error: soft_deleted_lookup_http_403`

The batch soft-deleted Company scan received a transient HTTP 403, so the deterministic worker aborted before any write. Ticket-level success state does NOT prove staging — always read the final staging index dispositions before reporting a prior run as staged.

## Validated recovery recipe

1. Probe the credential: `python3 skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_rest.py --check-connection`. All filters returning HTTP 200 confirms the 403 was transient, not a permissions change.
2. Re-run the worker with the same immutable lane discovery result and overlays into a NEW empty directory named `<original-staging-dir>-corrective-N` (the worker requires a new/empty output dir). Do not rerun discovery and do not mutate the original failed index.
3. Verify the run summary reports `complete: true` and each item disposition is `company_staged_*` with a real `company_id` and a `company_reconciliation_artifact` path before telling the user it staged.

## Reporting boundary

The corrective run produces its own staging index; it does not rewrite the discovery ticket's consumed artifact. When reporting, reference both the original failed index and the corrective index so the audit trail shows the abort and the remediation. Never describe the lead as staged from ticket state alone.
