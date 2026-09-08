# Model-boundary redaction and item-level CRM staging

Use this reference when a deterministic CRM plan validates locally but the agent reports that it cannot submit the exact write arguments.

## Failure signature

The following combination identifies a model-boundary transmission block rather than a payload defect:

- the raw persisted batch passes its local validator;
- duplicate preflight and the deterministic create/update decision completed;
- a rendered `read_file`, terminal, or tool result masks a value that remains valid in the raw file;
- the current MCP invocation schema requires inline JSON and exposes no verified file/reference or opaque structured pass-through;
- no CRM write was attempted.

A common trigger is E.164 phone data. Hermes may redact `+` followed by 7–15 digits before file/tool output enters model context. Confirm against the current Hermes implementation and configuration rather than assuming this behaviour is permanent. In the observed implementation, `agent/redact.py` defines the E.164 matcher and masking pass, while `tools/file_tools.py` applies `redact_sensitive_text(..., file_read=True)` to returned file content.

## Diagnostic procedure

1. Preserve the immutable discovery result and emitted plan.
2. Run the deterministic raw-file validator. Treat its aggregate result as authoritative for raw payload validity.
3. Compare only non-sensitive facts: whether the raw field exists, validator counts/status, and whether rendered output contains masking characters. Never reconstruct hidden digits.
4. Inspect the current CRM MCP execution schema. Determine whether it supports a secure file handle, artifact reference, opaque payload, or other exact pass-through. Do not carry forward a historical negative capability claim.
5. If the tool requires the model to provide complete inline JSON and a required value is redacted before reaching model context, record an orchestration/capability block with `write_attempted: false`.
6. Apply that result per item. Continue with items whose complete emitted arguments remain exactly visible and transmissible. Never fail an unaffected phone-less item merely because another item contains a redacted value.
7. Do not omit, guess, reformat, or manually reconstruct a blocked value to force a write.

## Classification

This condition is not:

- a CRM API rejection;
- failed authentication;
- an invalid raw phone value;
- a duplicate-match outcome; or
- an n8n discovery failure.

It is a transport/orchestration limitation between a valid local artifact and the tool invocation boundary. Record the precise unavailable capability and retain all preflight/decision evidence.

## Remediation boundary

Use a separately named corrective staging batch linked to the original result and terminal index. Do not rerun discovery and do not mutate the original index. A durable platform fix requires a tested exact-value path that does not expose protected values to model context, such as a verified opaque/file-backed tool invocation or a deterministic trusted adapter. Until such a path is proven in the current runtime, block only affected items and continue safe independent items.
