# Artifact-backed CRM write bridge security review

Use this checklist when implementing or reviewing a bridge that reads a local decision artifact and performs a non-idempotent CRM write.

## At-most-once write boundary

- Create an exclusive attempt marker before entering any code path that can reach the remote service.
- Ensure every layer performs exactly one transport attempt. Generic MCP handlers, authentication recovery, session reconnect, middleware, HTTP clients, and SDKs may retry unless explicitly disabled.
- Use a supported no-retry dispatch API. Do not reimplement private MCP internals merely to bypass retries; registry identity, server provenance, cancellation, circuit-breaker state, and response handling can diverge.
- Treat every exception after marker creation as an uncertain write. Never report `write_attempted: false` merely because persistence later raised `FileExistsError` or another local error.
- Make the marker crash-durable: fsync the file and its parent directory before dispatch. Apply equivalent durability to raw response creation and marker replacement.

## Artifact integrity and path safety

- Bind the exact decision bytes to an expected SHA-256 from the trusted workflow handoff.
- Validate sibling plan, matches, raw lookup responses, and normalized lookup outputs semantically; filename existence alone is not proof that duplicate preflight ran.
- Recompute or verify the decision from the plan and match evidence. Enforce action/reason consistency, exact-match precedence, and cardinality; multiple exact candidates must block writes.
- Reject payload `id` fields for creates and ensure an update payload cannot override `decision.company_id` during dict merging.
- Resolve and confine every sibling artifact, not only `decision.json`. Reject symlinks or use directory-descriptor/openat-style access with no-follow semantics to avoid sibling escape and directory-swap TOCTOU.
- Enforce the exact expected directory shape, not merely the presence of a component named `staging`.

## Sensitive data boundary

- Keep phone-bearing arguments out of model-visible tool calls, observer hooks, telemetry, middleware, and exception strings.
- Sanitize all exceptions returned to the model; transport and schema errors can embed request arguments.
- Persist the actual untransformed MCP response bytes with restrictive permissions. Do not pass the response through model-facing transform hooks before saving it.

## Response handling

- Parse the documented response envelope and extract the Company ID from the expected result location.
- Do not recursively accept every nested `id`: relation, owner, request, or metadata UUIDs can cause false ambiguity or select the wrong object.
- Persist the write response before interpretation, then perform and persist an authoritative `find_one_company` readback. Keep write retries blocked even when ID extraction or readback fails.

## Required tests

Cover at least:

1. create and update success with byte-for-byte argument equality;
2. payload `id` override rejection;
3. multiple/conflicting exact-match rejection and action/reason consistency;
4. malformed, missing, symlinked, or mutually inconsistent preflight artifacts;
5. hash mismatch and decision/sibling mutation races;
6. one transport attempt on timeout, authentication failure, and session failure;
7. post-dispatch persistence failures, including `FileExistsError`, reporting an uncertain write;
8. marker and response directory-fsync behavior;
9. exception/error paths proving no phone appears in returned model context or telemetry;
10. realistic nested write/readback responses containing unrelated UUID fields;
11. concurrent invocations and malformed staging-directory layouts.

A happy-path fake dispatcher is insufficient to prove at-most-once behavior because it bypasses the production dispatch and transport layers.