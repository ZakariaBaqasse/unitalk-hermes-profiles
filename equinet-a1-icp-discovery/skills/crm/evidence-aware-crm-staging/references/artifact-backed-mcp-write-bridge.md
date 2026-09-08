# Artifact-backed MCP writes for redacted payloads

Use this pattern when a deterministic local plan contains values that Hermes intentionally redacts before file or tool output reaches model context, but an MCP write must receive the exact original bytes semantically represented by that plan.

## Why model-side relay fails

Hermes redacts E.164 values in model-visible file and tool output. A locally persisted plan can therefore be valid while the agent sees a masked rendering. Returning the plan through terminal output has the same limitation. If the destination MCP tool accepts only inline JSON, the model cannot faithfully copy the raw value into its arguments.

Do not disable global redaction, reconstruct masked values, or silently omit fields from an already-approved deterministic payload.

## Bridge pattern

Keep the JSON artifacts for durability and auditability. Add a narrowly scoped local executor that:

1. accepts an immutable `decision.json` path and expected SHA-256;
2. restricts the path to the approved runtime artifact tree and rejects traversal/symlink escape;
3. validates the decision and sibling plan schema versions;
4. proves duplicate-preflight artifacts exist and that the decision agrees with normalized match sets;
5. permits only the intended Company operations and fields;
6. verifies that decision arguments exactly equal the deterministic plan payload;
7. validates raw E.164 values locally without rendering them;
8. creates an exclusive write-attempt marker before network I/O;
9. sends the raw in-memory arguments directly to the configured MCP session;
10. persists the raw write response before extracting identifiers;
11. performs and persists authoritative read-back;
12. returns only non-sensitive metadata to the agent.

## Non-idempotent retry rule

Do not route create operations through a generic MCP wrapper that automatically retries after authentication or session-expiry errors. A remote create may have committed before the response was lost. The bridge must make one transport call only. If the call raises, times out, returns an unusable response, or crashes after the marker is written, retain the marker and classify the outcome as uncertain; automatic retry is prohibited.

## Per-item failure scope

Capability checks and failures are per item. If one payload contains a value that cannot be transported, that does not justify blocking a different phone-less payload whose exact arguments are available. Never convert an item-specific transport limitation into a batch-wide failure.

## Current Equinet implementation

The Equinet profile provides the enabled plugin `twenty-company-artifact-bridge` and tool `twenty_company_write_from_artifact`.

Inputs:

- `decision_path`: `decision.json` below `runtime/n8n-poll-tickets/<ticket>/.../staging`
- `expected_sha256`: SHA-256 of the exact decision bytes
- `dry_run`: validation only when true

The implementation is profile-scoped under `plugins/twenty-company-artifact-bridge/`. It verifies raw lookup responses against normalized evidence and `matches.json`, rejects a Company `id` inside the plan payload, enforces exact-match cardinality, and performs one direct call through the already-connected Twenty MCP session. It stores and directory-fsyncs `write-attempt.json`, `raw-create.json` or `raw-update.json`, and `raw-readback.json`, and refuses a second write when any attempt/response artifact already exists. Because the current Hermes release has no public single-attempt MCP dispatch API, the plugin guards its use of internal transport primitives by verifying registry ownership, server identity, and the advertised `execute_tool`; rerun compatibility tests after Hermes upgrades.

## Verification checklist

- Unit-test that the fake MCP transport receives the complete unredacted E.164 value while the tool result does not contain it.
- Test path containment, SHA mismatch, masked raw values, incomplete preflight evidence, duplicate-match conflicts, update status preservation, and retry refusal.
- Test that the MCP transport is called exactly once.
- Run a real artifact with `dry_run: true`; require `validated: true` and `write_attempted: false`.
- Confirm plugin discovery, enablement, and tool registration in a fresh session.
- Never use a live create merely as a connectivity test.
