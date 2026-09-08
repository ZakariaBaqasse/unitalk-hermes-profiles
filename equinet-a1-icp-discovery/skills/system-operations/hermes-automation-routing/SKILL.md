---
name: hermes-automation-routing
description: Use when choosing Hermes heartbeat, cron, or bot-chat.
version: 1.0.0
status: validated
---

# Hermes Automation Routing

Use this skill when deciding how Hermes should monitor a long-running external task, run recurring work, preserve conversational context, or route scheduled output back to an agent or human channel.

Treat the current Hermes documentation as authoritative because scheduler and delivery capabilities evolve. Verify the relevant docs before making a negative capability claim.

## Choose by execution context

### Session heartbeat

Use `/heartbeat` when the recurring instruction needs the current conversation's history and tool context.

- Runs as a normal user-role turn in the same session.
- Fires only while the session is idle and never interrupts an active turn.
- Missed ticks coalesce rather than accumulating.
- State survives session resume/context rotation, but firing requires the owning CLI or gateway process to run.
- One heartbeat is allowed per session; setting another replaces it.

For external systems, make the instruction read-only unless the user separately authorizes mutations. Include a terminal-state rule so monitoring stops or becomes quiet after success/failure.

### Cron

Use cron when scheduling must be durable and self-contained.

- Each tick runs in a fresh isolated agent session.
- Put workflow IDs, execution IDs, thresholds, timeout policy, and other durable identifiers in the job prompt or attached state; do not assume chat history is inherited.
- Use `context_from` only for chaining the most recent completed output of upstream jobs, not as a substitute for the originating conversation.
- Prefer change-only reporting to repetitive "still running" messages.

### Cron delivery to Bot Chat

Use `deliver: bot-chat` when a cron result must be processed by a Hermes profile rather than merely posted to a human channel.

- Bare `bot-chat` targets the job-owning profile's canonical Bot Chat.
- `bot-chat:<profile>` targets another profile on the same machine.
- Delivery enters that canonical Bot Chat as a real incoming message and costs the target bot a full additional agent turn.
- It may compose with explicit human targets such as `bot-chat,telegram`, but is not implied by `all`.
- It targets the profile's designated canonical Bot Chat, not an arbitrary session ID or whichever conversation is currently open.

## Decision table

| Need | Mechanism |
|---|---|
| Same conversation and full discussion context | Session heartbeat |
| Durable unattended schedule | Cron |
| Deliver cron result for another agent turn | Cron with `bot-chat` |
| Human notification only | Cron with platform/origin target |
| Exact arbitrary chat/thread | Explicit supported platform routing target |

## Safe monitoring pattern

For long-running workflows such as n8n:

1. Persist the workflow and execution identifiers.
2. Poll with read-only status/metadata operations.
3. Compare with the prior known state.
4. Report only state changes, completion, failure, timeout, or a well-defined stall condition.
5. Never trigger, rerun, publish, update, or delete a workflow as a heartbeat probe.
6. End or silence monitoring after a terminal state.

### Process ownership and restart scope

Cron ticks use fresh agent sessions but run inside the scheduler's long-lived owning process. Process-global settings sampled at module import (for example `security.redact_secrets`) do not change merely because a new cron tick starts.

Identify and restart the actual scheduler owner:

- Hermes Desktop normally uses an app-managed `hermes serve` backend;
- a remote Desktop connection uses the remote host's `hermes serve` process;
- messaging channels use the separate `hermes gateway` process;
- a TUI may own its own scheduler process.

A dashboard WebSocket reconnect, a new chat, or restarting another profile's messaging gateway is not proof that the Desktop/TUI backend restarted. `hermes -p <profile> gateway status` reports the messaging gateway only; it does not report the Desktop-managed `serve` backend. After restarting the correct process, run a synthetic non-secret file-read probe before scheduling side effects.

See `references/desktop-backend-and-cron-process-restarts.md` for the diagnostic ladder, correct restart target by interface, and safe recovery rules.

## Capability claims

- Distinguish what Hermes supports from what the current agent tool surface exposes.
- A documented slash command may require a user-role command unless a callable management tool/API is available in the current session.
- Do not claim that local/TUI sessions cannot receive cron output without checking current delivery modes; `bot-chat` is machine-local and specifically exists for agent-processed delivery.
- Do not equate `bot-chat` with `origin`: the former addresses a profile's canonical Bot Chat, while the latter addresses the job's creation/delivery origin.

### Delivery verification

A task-level `delivered_at` marker proves only that the task attempted its terminal delivery step; it is not proof that the configured destination received a message. After a terminal cron run, inspect the job metadata for `last_delivery_error` and treat a non-empty value as a delivery failure. Report the completed work separately from any notification failure, and do not tell the user that a Bot Chat or human target was notified unless the scheduler confirms delivery without an error.

## References

See `references/heartbeat-cron-bot-chat.md` for command forms, lifecycle semantics, cost implications, and an n8n monitoring example.

## Verification checklist

Before creating or recommending automation, verify:

- [ ] The selected mechanism matches context and durability needs.
- [ ] Delivery targets the intended session, canonical Bot Chat, or human channel.
- [ ] The task prompt is self-contained where required.
- [ ] External-system checks are read-only unless mutation is explicitly authorized.
- [ ] Frequency and extra agent-turn cost are acceptable.
- [ ] Stop, timeout, and failure behavior are explicit.
