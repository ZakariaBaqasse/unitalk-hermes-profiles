# Runtime Redaction Verification for Direct Twenty MCP Staging

Use this check before a cron or interactive agent directly relays phone-bearing `decision.json.mcp_arguments` into Twenty MCP.

## Why this check exists

A configuration change is not proof that the running Hermes process stopped redacting model-visible tool output. The redaction flag is loaded during process startup, and a fresh cron tick may reuse the same long-lived scheduler process. A normally formatted phone number remaining visible also does not prove E.164 values are visible because the redactor specifically recognizes `+`-prefixed digit sequences.

Disabling redaction is global for that Hermes profile and can expose API keys, tokens and passwords as well as public phone numbers. Use it only after the operator explicitly accepts that broader effect.

## Verification procedure

1. Target the intended Equinet profile explicitly:

   ```bash
   hermes -p equinet-a1-icp-discovery config set security.redact_secrets false
   ```

   Then inspect `/opt/data/profiles/equinet-a1-icp-discovery/config.yaml` and confirm the setting is uncommented under `security`. A successful command against the current/default profile may update a different profile and is not evidence that Equinet changed.

2. Ensure no environment or managed configuration overrides the setting. In particular, check the effective `HERMES_REDACT_SECRETS` value without printing unrelated environment secrets.
3. Fully restart the Hermes process that will perform staging. Editing configuration without restarting is insufficient because redaction state is captured during process startup.
4. Create a temporary JSON file inside the active profile's `runtime/` directory containing a synthetic E.164 test value such as `+15551234567`. Do not use a real prospect phone number for this probe.
5. Read the file through the same model-facing `read_file` tool and process type that will perform staging.
6. Pass only if the returned value is exactly `+15551234567`. A value such as `+155****4567` means redaction remains active and direct model-mediated phone submission must stop.
7. Remove the temporary probe file.

## Fresh-process diagnostic

When the active session is known to be stale, launch a separate process with the intended `HERMES_HOME`, import the normal Hermes startup module before `agent.redact`, and compare `redact_sensitive_text(test_value) == test_value`. Print only the Boolean result. This confirms whether a newly started process will honor the profile setting without exposing any real phone number; it does not prove the still-running scheduler or TUI has reloaded.

## Decision rule

- **Exact E.164 value survives `read_file`:** direct Twenty MCP submission may proceed, subject to normal deterministic plan validation, duplicate preflight, write-response persistence and read-back reconciliation.
- **E.164 value is masked or altered:** do not reconstruct it from memory or another rendered source and do not attempt the Company write. Correct the effective configuration, restart the relevant Hermes process, and repeat this probe.

This check verifies only the model-visible file-read boundary. It does not replace `validate-batch-phones`, duplicate preflight, Twenty schema validation, or read-back reconciliation.
