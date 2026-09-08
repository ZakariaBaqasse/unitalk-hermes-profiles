# PostgreSQL CTE counting and persisted-cursor diagnostics

Use this reference when a sequential n8n orchestrator invokes another source after the previous source appears to have met the target, or when a source appears exhausted earlier than expected.

## Data-modifying CTE visibility pitfall

In PostgreSQL, sibling data-modifying CTEs share one statement snapshot. A later CTE that queries the base table must not be assumed to see rows inserted by an earlier sibling CTE.

A misleading pattern is:

```sql
WITH inserted AS (
  INSERT INTO run_leads (...) SELECT ... RETURNING lead_id
),
updated_run AS (
  UPDATE runs
  SET unique_leads_found = (
    SELECT COUNT(*) FROM run_leads WHERE run_id = $1
  )
  WHERE run_id = $1
  RETURNING *
)
SELECT * FROM updated_run;
```

The base-table count can lag the current source by one statement. n8n then sends the full remaining target to the next source even though the current source just claimed enough leads.

Use a pre-statement count plus the current claim CTE:

```sql
WITH existing_run_count AS (
  SELECT COUNT(*)::integer AS lead_count
  FROM run_leads
  WHERE run_id = $1
),
new_global AS (
  INSERT INTO global_ledger (...)
  SELECT ...
  ON CONFLICT DO NOTHING
  RETURNING lead_fingerprint
),
run_lead_insert AS (
  INSERT INTO run_leads (...)
  SELECT ... FROM new_global
  RETURNING lead_fingerprint
),
updated_run AS (
  UPDATE runs
  SET unique_leads_found =
    (SELECT lead_count FROM existing_run_count)
    + (SELECT COUNT(*)::integer FROM new_global)
  WHERE run_id = $1
  RETURNING *
)
SELECT * FROM updated_run;
```

Equivalent safe approaches may count `RETURNING` rows explicitly, but must distinguish inserts from conflict updates so same-run duplicates are not double-counted.

## Failed parent runs can legitimately advance source cursors

A parent workflow can fail after an earlier source response has already been validated and persisted. Subsequent application runs then resume from the advanced source cursor. Before diagnosing premature exhaustion:

1. Inspect several preceding parent executions, including failed ones.
2. Record the loaded offset, records returned, persisted next offset, globally new count, and downstream failure point.
3. Reconstruct the source sequence across executions.
4. Compare the final offset with the source's total eligible-record count.

For source-level durable semantics, retaining successful upstream progress after a later downstream failure is expected and avoids repeated crawl cost. If whole-run atomicity is required instead, stage cursors as pending and promote them only when the parent run commits; do not simply roll back evidence after the fact.

## Exhausted cursor visibility

An exhausted source may still retain a terminal cursor such as `offset: 37` with `source_exhausted: true`. This is useful audit evidence even though the status prevents further calls. Avoid erasing the cursor to `{}` unless the contract explicitly treats terminal position as disposable.

## Verification

For a fresh scope where source one claims the complete target, assert that the persistence node returns the full updated count immediately and that source two is never invoked. Also test a downstream failure followed by a new run to confirm that the chosen cursor commit semantics are explicit and documented.
