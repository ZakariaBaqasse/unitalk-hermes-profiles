# Heartbeat, cron, and Bot Chat delivery

## Session heartbeat controls

Typical command forms:

```text
/heartbeat every 5m <recurring instruction>
/heartbeat status
/heartbeat pause
/heartbeat resume
/heartbeat clear
```

`/hb` is an alias. The minimum interval is 60 seconds. Heartbeats fire only between turns; queued user input takes priority. If the process was stopped or the session busy across multiple intervals, one tick fires when eligible rather than replaying a backlog.

Example read-only workflow monitor:

```text
/heartbeat every 5m Check the external workflow execution already identified in this conversation. Use only read-only status or metadata tools. Report only if its state changed, it completed, failed, timed out, or meets the agreed stall condition. Do not trigger, rerun, publish, update, or delete anything. If nothing meaningful changed, reply briefly and stop.
```

## Cron context

A cron agent starts fresh each tick. Include the durable identifiers and policy explicitly:

- profile/integration to use;
- workflow and execution IDs;
- interval and deadline;
- prior-state source or change-detection method;
- terminal statuses;
- permitted read-only operations;
- delivery target.

Cron runs cannot recursively schedule more cron jobs.

## Delivery meanings

- `origin`: creation-origin chat/topic where supported.
- `local`: retain output without external delivery.
- explicit platform target: a supported platform/chat/thread address.
- `all`: connected home channels resolved at fire time.
- `bot-chat`: job-owning profile's canonical Bot Chat.
- `bot-chat:<profile>`: another local profile's canonical Bot Chat.

`bot-chat` differs from ordinary delivery: the receiving profile gets a real incoming message and runs a full agent turn. It is not included in `all`, though comma-separated composition such as `bot-chat,telegram` is supported.

## Canonical Bot Chat

A Hermes profile can own many conversations, but Bot Chat delivery needs one deterministic machine-local destination. The canonical Bot Chat is that profile-designated primary bot conversation. It is not automatically the currently open tab, the cron execution's isolated session, or an arbitrary historical session. Use it as a profile inbox for automation that the bot should process.

## Cost and noise controls

An agent cron tick plus `bot-chat` processing can consume two full agent turns. Choose a sensible interval and avoid unconditional progress chatter. For high-frequency deterministic polling, prefer a script/change detector that emits nothing when state is unchanged; reserve the Bot Chat turn for actionable output.

## Selection examples

- "Keep checking the CI run we just discussed" → heartbeat.
- "Check this workflow every hour even after restarts" → cron.
- "When cron finds a failure, have the profile investigate it" → cron with `bot-chat`.
- "Post a daily status to Telegram for a human" → cron with Telegram delivery.
