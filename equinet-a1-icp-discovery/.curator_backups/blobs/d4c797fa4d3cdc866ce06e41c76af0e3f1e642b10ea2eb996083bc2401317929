---
name: mcp-server-connectivity-testing
description: Use when testing MCP server connectivity and tool access.
version: 1.0.0
status: validated
---

# MCP Server Connectivity Testing

Use this skill when a user asks whether an MCP server is reachable, connected, authenticated or usable from the current Hermes session. The goal is an evidence-backed connectivity result, not a claim based only on configuration files.

## Test layers

Report the layers separately:

1. **Configuration** — identify the configured server name, transport and endpoint without exposing headers, tokens or credentials.
2. **Network/TLS reachability** — make a safe request to the configured endpoint and record the HTTP status and non-sensitive response summary.
3. **Authentication** — test with the real runtime-configured credential only when it is available through the active connection/configuration. Never print or persist the credential.
4. **MCP protocol handshake** — send a minimal `initialize` JSON-RPC request with a current protocol version, then inspect the response.
5. **Tool discovery** — call `tools/list` only after a successful authenticated handshake, preserving the returned tool names and count as the evidence of usable server capabilities.
6. **Non-destructive execution** — invoke only a read-only health/status operation when the server exposes one and the user explicitly asked for an execution test. Do not create, update, publish, trigger or delete workflows merely to test connectivity.

## Interpretation rules

- A DNS/TLS connection or HTTP `401` proves the endpoint is reachable, not that the MCP server is connected or usable.
- A configured MCP entry does not prove that Hermes connected it. Confirm the live tool registry or a successful protocol handshake.
- If the current tool catalog contains no server-specific MCP tools, report that tool access is not exposed in the session even if the endpoint itself is reachable.
- Distinguish `configured`, `reachable`, `authenticated`, `protocol-ready`, `tools-discovered` and `execution-tested` in the result.
- Never claim a workflow was executed, changed or verified unless a real tool call returned a verifiable result.
- Historical logs are secondary evidence. Prefer the current live handshake/tool registry over old discovery messages.

## Safe procedure

1. Inspect the active configuration for the server entry and endpoint, redacting secret values.
2. Check the current tool catalog for server-specific tools before attempting an execution call.
3. Probe the endpoint without credentials if needed to establish basic reachability; a `401` is a useful result and is not a failure of reachability.
4. If the active runtime exposes the credential, perform an authenticated `initialize` request and then `tools/list`.
5. If credentials are unavailable or only redacted placeholders are present, stop at the authentication boundary and state the exact limitation; do not guess, recover or print secrets.
6. If the server is configured but discovery repeatedly reports no connected servers, report the distinction and avoid claiming access.
7. Validate the configuration shape before treating transport errors as authentication failures. Under `mcp_servers`, each immediate child is one server and must contain its own `url` (HTTP) or `command` (stdio); do not add an extra provider/server-name nesting layer.
8. Preserve the raw status/error class, endpoint, timestamp and test scope in a concise audit note, excluding secrets.

See `references/mcp-config-shape.md` for transport selection, the misleading missing-`command` symptom, and known-good HTTP examples.

## n8n-specific caution

For n8n MCP, use a read-only discovery or metadata operation for validation. Do not run a workflow as a connectivity probe because a workflow may send messages, change records or otherwise cause side effects. Treat workflow execution as a separate user-authorized action requiring a named workflow and explicit scope.

A reusable n8n HTTP probe and the observed response classes are documented in `references/n8n-http-probe.md`.

## Common pitfalls

- **401 without Authorization header:** endpoint is live; authentication was not supplied. Do not call this an outage.
- **Redacted token in a file:** do not send the redacted value as if it were a credential. Use the live MCP connection or stop with an authentication blocker.
- **No MCP namespace in the session:** do not fabricate tool names or emulate a successful MCP call from HTTP reachability alone.
- **Historical “no connected servers” log:** useful diagnostic context, but re-test the live endpoint before concluding current state.
- **Destructive test request:** replace it with protocol handshake/tool listing or a documented read-only operation.

## Verification checklist

Before reporting success, verify which of these actually passed:

- [ ] Configuration identified without exposing secrets
- [ ] Endpoint reachable
- [ ] Authentication accepted
- [ ] MCP `initialize` succeeded
- [ ] `tools/list` succeeded
- [ ] Read-only operation returned a verifiable result
- [ ] No workflow or external side effect occurred

Report failed or untested layers explicitly rather than collapsing them into a binary “working/not working” conclusion.
