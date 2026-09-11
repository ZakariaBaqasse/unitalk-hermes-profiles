# Provider configuration diagnostics

Use this provider-independent check when a user asks whether a web, model, extraction, or auxiliary provider is configured for an active profile.

## Evidence ladder

1. **Profile declaration** — inspect the active profile's config for an explicit backend/provider and credential reference.
2. **Shared inheritance** — inspect shared config or dotenv sources, but emit only key names and presence booleans.
3. **Runtime selection** — confirm which provider handled the request from a provider-scoped live response or log line.
4. **Operational check** — make one bounded live call and report success or the exact provider response.

These layers support different claims:

- Key absent locally does not mean the provider is unavailable; it may be inherited.
- Plugin registration proves capability, not provider selection.
- Credential presence proves configuration, not validity, quota, or account status.
- A provider-scoped API error proves selection and attempted use, but not successful operation.

## Safe probes

Prefer a small parser that reports only whether expected keys exist. Never display values. Inspect only the active profile and documented shared configuration roots.

Do not use broad `env`, `export`, `ps`, `pgrep -af`, service command-line dumps, or decoded bootstrap payloads for this task. Process arguments may contain plaintext or encoded secrets even when file-reading tools normally redact them.

## Reporting template

> Provider X is [declared locally / inherited from shared configuration / not found]. Runtime evidence shows [selected / not selected]. A bounded live check [succeeded / failed with exact status], so it is [operational / configured but not operational / not proven configured].

Name the configuration scope and avoid guessing the root cause of an API status unless the provider response explicitly states it.
