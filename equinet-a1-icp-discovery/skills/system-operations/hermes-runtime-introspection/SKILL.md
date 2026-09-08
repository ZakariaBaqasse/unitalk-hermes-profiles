---
name: hermes-runtime-introspection
description: Use when identifying the active Hermes session and endpoint.
version: 1.0.0
status: validated
---

# Hermes Runtime Introspection

Use this skill when a user asks for the identity or live configuration of the active Hermes conversation, including its discussion/session ID, active model/provider, profile, transport context, or configured API endpoint.

## Principles

- Treat runtime metadata and the active environment as authoritative for the current conversation; do not infer values from prior assistant messages or remembered profile names.
- Use a live tool check before answering. Runtime state can change during a conversation, including model/provider selection.
- Never print API keys, tokens, passwords, or opaque configuration blobs. Report only the specifically requested non-secret field.
- Distinguish a model-provider gateway endpoint from a separately configured Hermes API-server endpoint. Do not describe one as the other without direct configuration evidence.

## Session identity

Read `HERMES_SESSION_ID` from the live process environment to answer a question about the current discussion ID. If the user needs a routing identifier rather than the discussion ID, inspect the corresponding non-secret `HERMES_SESSION_*` fields (platform, chat ID, thread ID) and label them precisely.

Do not substitute a session ID retrieved from history search for the active session ID.

## Model and provider

For the active model/provider, prefer the most recent runtime metadata supplied by Hermes. If it is absent or needs verification, inspect the relevant non-secret environment fields, such as `OPENAI_MODEL` and `OPENAI_PROVIDER_NAME`, and clearly label their scope.

## Endpoint discovery

1. Inspect the active profile configuration for explicit `base_url`, `endpoint`, `api_server`, `server_url`, host, or port settings.
2. If necessary, decode `HERMES_CONFIG_BASE64` locally and search only for endpoint-like keys. Do not emit the decoded configuration or any credential-bearing lines.
3. Report the URL with its configuration scope, for example: “configured OpenAI-compatible provider gateway.”
4. State that no separate Hermes API-server endpoint is configured only after inspecting endpoint-like configuration fields.

A profile may have feature-specific endpoint values (for example TTS/STT) and a runtime provider gateway value. Preserve the distinction instead of assuming every `base_url` applies to the general chat model.

## Provider configuration provenance

When asked whether a tool provider is configured for a profile, distinguish three separate states:

1. **Declared locally:** inspect the active profile config for an explicit backend selection or credential reference.
2. **Inherited and selected:** inspect shared configuration or dotenv files by printing key names/presence only, then confirm the provider actually selected from a live tool response or provider-scoped log entry.
3. **Operational:** make a bounded live call and report whether it succeeds. An installed plugin or present key does not prove the credential/account is usable.

Answer with precise scope, such as: “available to this profile through shared configuration, not configured profile-locally, and currently failing at the provider API.” Do not collapse “configured” and “working” into one claim.

Avoid broad process listings when checking provider configuration: launch commands can embed encoded configuration and secrets. Prefer focused parsers that emit only booleans such as `TAVILY_API_KEY_PRESENT=true`, and never print credential values or complete environment/process arguments.

See `references/provider-configuration-diagnostics.md` for the reusable evidence ladder, safe probes, and reporting template.

## Safe shell pattern

Use a focused command that prints only non-secret facts. Example:

```sh
printf 'discussion_id=%s\n' "$HERMES_SESSION_ID"
printf 'model=%s\nprovider=%s\n' "$OPENAI_MODEL" "$OPENAI_PROVIDER_NAME"
```

For encoded configuration, use a local parser/search that retains only lines or values whose keys are endpoint-like, and redact any credential fields before output. Never use a broad environment dump in the user-facing result.

## Response format

Lead with a short bullet list of requested values. Add one concise qualification when needed to avoid conflating:

- a conversation/discussion ID with a chat or thread ID;
- an OpenAI-compatible model gateway with a Hermes API server; or
- a feature-specific endpoint with the chat-provider endpoint.

Do not include unrelated configuration, research workflow details, or credentials.

## Verification checklist

Before finalizing, verify:

- each value came from the current runtime or active profile configuration;
- no secret was exposed;
- endpoint terminology accurately reflects its configuration scope;
- the answer directly addresses every requested identifier.
