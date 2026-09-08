# n8n MCP HTTP probe reference

## Purpose

Use this as a non-destructive connectivity probe for an n8n HTTP MCP endpoint. It verifies reachability and, when a live credential is available, can be extended to authenticated protocol testing. It must not execute an n8n workflow as a health check.

## Minimal unauthenticated probe

Send both a simple request and a JSON-RPC initialize request to the configured endpoint, with no credential:

```python
import json
import urllib.error
import urllib.request

url = "https://<n8n-host>/<mcp-path>"
initialize = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-03-26",
        "capabilities": {},
        "clientInfo": {"name": "connectivity-test", "version": "1.0"},
    },
}

for method, payload in [("GET", None), ("POST", json.dumps(initialize).encode())]:
    request = urllib.request.Request(
        url,
        data=payload,
        method=method,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            print(method, response.status, response.headers.get("content-type"))
    except urllib.error.HTTPError as error:
        print(method, error.code, error.headers.get("content-type"))
```

Do not print request headers containing Authorization. Summarise only the status, content type and a short redacted response prefix if useful.

## Response interpretation

- `401` with a message that Authorization was not sent: DNS/TLS and application routing succeeded; authentication was not tested.
- `401` or `403` with an Authorization header: endpoint rejected the supplied credential or scope; do not expose the credential.
- Successful `initialize`: protocol negotiation passed. Follow the server's returned session/header requirements before calling `tools/list`.
- Successful `tools/list`: server capabilities are available to the caller. Record names/count, not secrets.
- Timeout, DNS, TLS or 5xx: endpoint reachability or service health issue; retry only for transient failures and preserve the error class.

## Session-specific observation

The Equinet A1 profile's configured n8n endpoint responded to both unauthenticated probes with HTTP `401` and `Authorization not sent`. This established reachability but did not establish authenticated MCP access. The active session did not expose n8n-specific MCP tools, and no workflow execution was attempted.
