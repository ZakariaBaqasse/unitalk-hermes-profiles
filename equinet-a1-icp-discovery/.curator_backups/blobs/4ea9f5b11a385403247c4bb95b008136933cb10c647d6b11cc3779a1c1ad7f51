# MCP configuration shape and transport selection

Hermes treats every immediate child of `mcp_servers` as one server definition. Transport is selected from fields on that same mapping:

- `url` present → HTTP/Streamable HTTP
- `command` present → stdio

## Known-good remote HTTP shape

```yaml
mcp_servers:
  n8n:
    url: https://example.invalid/mcp
    headers:
      Authorization: Bearer <secret>
    connect_timeout: 60
    timeout: 180
```

A separate `type: http` field is unnecessary when `url` is present.

## Extra-nesting failure

This is wrong:

```yaml
mcp_servers:
  n8n:
    n8n-mcp:
      type: http
      url: https://example.invalid/mcp
```

Hermes sees `n8n` as the server definition. Because `url` is hidden one level lower, transport detection falls back to stdio and can emit the misleading error:

```text
MCP server 'n8n' has no 'command' in config
```

Do not solve this by inventing a `command`. Flatten the mapping so `url` and `headers` are direct children of `n8n`, reload/reconnect MCP, then test again. Only troubleshoot credentials if the corrected shape reaches an authenticated HTTP attempt.

## Diagnostic order

1. Confirm one-server-per-child YAML shape.
2. Confirm direct `url` or `command` transport selector.
3. Reload MCP so discovery reads the new definition.
4. Verify `initialize`, then `tools/list`.
5. If HTTP now returns `401` or `403` with authorization supplied, investigate token validity or scope without exposing the credential.
