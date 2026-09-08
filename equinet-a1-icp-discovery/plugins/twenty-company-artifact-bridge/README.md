# Twenty Company Artifact Bridge

Profile-scoped Hermes plugin for executing deterministic Twenty Company staging decisions directly from persisted JSON artifacts.

## Tool

`twenty_company_write_from_artifact`

Required inputs:

- `decision_path`: a `decision.json` below `runtime/n8n-poll-tickets/<ticket>/.../staging`
- `expected_sha256`: SHA-256 of the exact decision file
- `dry_run`: optional validation-only mode

The tool validates the sibling plan and duplicate-preflight artifacts, permits only `create_many_companies` or `update_one_company`, creates an exclusive write-attempt marker, forwards the raw arguments internally to `mcp__twenty__execute_tool`, persists raw write/read-back responses, and returns only non-sensitive metadata.

The bridge calls the connected Twenty MCP transport exactly once instead of using Hermes's generic MCP reconnect-and-retry wrapper. It intentionally refuses retries when a write marker or response artifact already exists. A full Hermes process restart is required after first installation or enablement so plugin discovery runs again. A fresh cron tick alone is not sufficient because cron agent sessions share the scheduler process's already-cached plugin registry. Code changes to an already-loaded plugin also require a process restart before runtime use.

Compatibility note: the installed Hermes release has no public single-attempt MCP dispatch API, so this profile plugin uses guarded internal MCP transport functions and verifies that the registered bridge tool is owned by the `twenty` MCP server. Re-run the plugin tests after Hermes upgrades until a supported no-retry dispatch API is available.
