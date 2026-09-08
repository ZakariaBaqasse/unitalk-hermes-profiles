# Cursor contract failures and failed-batch persistence

Use this reference when an n8n parent reports a source failure even though an asynchronous provider completed successfully.

## Diagnostic sequence

1. Separate the n8n execution status from the workflow's business result. An execution may be technically `success` while returning `discovery_failed` through a controlled result envelope.
2. Compare the parent request context with the child result at three levels:
   - top-level `source_scope_key` and `location_key`;
   - `next_cursor.source_id`, `segment`, and `location_key`;
   - `next_cursor.scope_key` or `source_scope_key`.
3. Inspect provider evidence separately: provider run status, dataset ID, raw offset, exhausted flag, filtered-record count, and usage cost.
4. Trace the parent normalizer output and persistence input. Confirm whether a contract failure preserved records or exhaustion state by mistake.
5. Inspect durable state for every skipped source. A final result may list only sources executed in the current run even when other sources were skipped because their cross-run cursors were already terminal.

## External scope versus provider scope

The parent owns one canonical discovery scope, for example:

```text
<policy>|<segment>|<country>|<region>|<city>|<focus>
```

The source ID is normally a separate database key. A child may build a more specific internal provider key for request/job reuse:

```text
<parent-scope>|<source-id>|<query-plan-version>
```

Keep these separate:

- external `source_scope_key` and `next_cursor.scope_key` must equal the parent scope exactly;
- internal `provider_scope_key` may include source ID, actor/query version, and provider inputs;
- use the provider scope for provider-job lookup and request keys, never as the external cursor owner.

Do not weaken the parent's strict cursor validator to accept arbitrary suffixes. Fix the child contract.

## Failure-state persistence guard

When a parent detects a source contract error:

- clear accepted `records`;
- preserve the previously committed cursor;
- preserve prior exhaustion rather than accepting the failed response's exhaustion claim;
- persist zero accepted records;
- retain the structured error for audit.

Persistence SQL must independently gate incoming records to successful normalized statuses such as `partial` and `exhausted`. Failed or blocked batches must not update the global ledger, aliases, source provenance, or consumed-source-record table even if a child accidentally includes records.

A useful SQL boundary is:

```sql
WHERE $adapter_status IN ('partial', 'exhausted')
  AND COALESCE(value->>'lead_fingerprint', '') <> ''
```

## Paid provider recovery

If the provider run succeeded but the parent rejected cursor metadata:

- do not force a new paid run;
- verify the durable provider job retains run ID, dataset ID, raw offset, and exhausted state;
- repair the external cursor contract;
- resume or return the existing dataset terminally;
- verify `actor_runs_started` remains zero on the recovery path.

## Empty-result semantics

Do not automatically equate zero newly admitted leads with a technical failure. Distinguish:

- provider/adapter failure;
- successful source exhaustion with no globally new records;
- partial discovery;
- target completion.

If adding an explicit `discovery_exhausted` status, update every downstream schema and consumer together.
