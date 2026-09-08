# Corrective staging after a pre-write abort

Use when an immutable discovery result was retrieved successfully but the original staging attempt reached terminal `sync_failed` outcomes **before any Twenty Company write**.

## Invariants

- Preserve the original discovery result, batch, ticket and staging index. Do not edit the consumed index or portray it as successful.
- Do not rerun n8n discovery merely to repair staging.
- A correction is a new, separately named remediation batch linked to the original execution, result SHA-256 and prior staging-index reference.
- If the original audit lacks raw, normalized lookup and deterministic decision artifacts for every item, repeat all Twenty duplicate preflights. Do not rely on an unverified `completed_no_matches` claim.
- Validate the actual emitted batch locally with `validate-batch-phones`; display-layer redaction is never payload evidence.
- No uncertain create may be retried. This procedure applies only when the prior index proves `write_attempted: false` for the item.

## Remediation flow

1. Confirm every remediation item has `write_attempted: false` in the prior index.
2. Create a new artifact directory such as `runtime/twenty-staging/<original-ticket>/remediation-<UTC>/`.
3. Prepare and locally validate a new batch from the immutable compact discovery result; retain both input SHA-256 values.
4. Persist raw and normalized Twenty lookups and a deterministic decision for every ready item.
5. Create or UUID-scoped update only after the per-item preflight and decision are complete. Persist raw write responses before extracting IDs.
6. Read back, normalize and reconcile every write. Finalize a distinct remediation staging index and human-review summary.

## Audit statement

The remediation report must state that the original staging run made no Twenty write and name the concrete pre-write failure class. It must not claim the remediation altered the original terminal index.
