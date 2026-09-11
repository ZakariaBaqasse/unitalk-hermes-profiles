# MCP Large-Result Spillover and Compound Arguments

Observed while operating the Equinet n8n MCP through Hermes; applies to any MCP server whose
tools return large payloads or require compound resource identifiers.

## Compound identifier arguments

Some MCP tools need more than one ID to locate a resource. The n8n execution-detail tool
(`get_execution` / runtime-discovered alias) requires BOTH `workflowId` and `executionId`;
a call carrying only the execution ID is rejected before invocation with a
"missing required argument(s)" error naming both fields.

- Read the tool schema (or the error text, which echoes the full JSON schema) before retrying.
- Pass every persisted identifier — for Equinet runs both IDs live on the polling ticket.

## Oversized MCP responses (spillover)

Large MCP results (e.g. `search_workflows` on an instance with dozens of workflows, ~78KB)
are persisted to `cache/spillover/tool_call_*.txt` as raw JSON, with only a preview returned
inline.

- Parse the spillover file in execute_code with `open()` + `json.loads`; it is plain raw JSON.
- Do NOT parse it via read_file output: the `LINE_NUM|content` line prefixes corrupt JSON
  (`json.decoder.JSONDecodeError: Unterminated string`).
- Never re-request the same remote data — the full result is already on disk; re-calling the
  tool just pays the network and token cost again and produces another spillover file.

## Duplicate-name workflows

When several workflows share one display name (e.g. a `-v2` successor), confirm the ACTIVE,
MCP-exposed one by immutable workflow ID from live metadata. An inactive same-name predecessor
is not the production path even when it still exists.
