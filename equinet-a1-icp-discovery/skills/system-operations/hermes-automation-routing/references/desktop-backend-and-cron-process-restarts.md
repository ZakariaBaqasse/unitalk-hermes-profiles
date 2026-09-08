# Desktop backend, cron ownership, and process-scoped settings

Use this reference when a configuration change appears correct in `config.yaml` but cron or Desktop chat still behaves as before.

## Distinguish the processes

- **Hermes Desktop local backend:** an app-managed `hermes serve` process. Desktop chat, tools, and any scheduler hosted there use this process.
- **Remote Desktop backend:** a separately managed remote `hermes serve` process. The Desktop client only connects to it.
- **Messaging gateway:** `hermes gateway`, used for Telegram, Discord, and similar channels. It is separate from the Desktop backend.
- **Web dashboard connection:** reconnecting its WebSocket or restarting a different profile's messaging gateway does not prove that the process owning Desktop chat or cron restarted.

A cron tick is a fresh agent session, not a fresh Python process. It inherits process-global state from the scheduler owner.

## Import-time configuration

Some security settings, including `security.redact_secrets`, are bridged to environment state and sampled when the redaction module is imported. Editing the profile config cannot change an already-running scheduler process.

## Diagnosis

1. Confirm the intended profile contains the setting. Do not assume a profile flag was applied to the right profile.
2. Identify which process owns the failing cron scheduler: Desktop `serve`, a remote `serve`, messaging `gateway`, or a TUI process.
3. Treat `hermes -p <profile> gateway status` as messaging-gateway status only. If it says the profile gateway is not running, restarting that gateway cannot reload a Desktop-owned scheduler.
4. Check logs for a real startup sequence. A WebSocket disconnect/reconnect without process startup and plugin/MCP initialization is not a restart.
5. Before any side effect, create a synthetic E.164 probe file, read it through the normal `read_file` tool, and delete it. A masked result proves the current process still has redaction enabled.
6. Optionally start a separate process under the target profile and compare the redactor result internally, emitting only a boolean. This distinguishes correct persisted config from stale process state.

## Restart the correct owner

- **Local Desktop:** use the Desktop command palette (`Cmd/Ctrl+K`) and select **Restart Gateway** (the app-managed backend), or fully quit and relaunch Hermes Desktop. Closing a chat tab is insufficient.
- **Remote Desktop:** restart the remote `hermes serve` process or its service on the remote host.
- **Messaging channels:** restart the profile-specific messaging gateway with `hermes -p <profile> gateway restart`.
- **TUI:** exit the TUI process and relaunch the target profile.

## Verification and recovery

After restart, repeat the synthetic `read_file` probe before creating or resuming a side-effecting cron job. A prior terminal staging index remains historical evidence; do not mutate it or rerun upstream discovery solely because the runtime was misconfigured. Where policy allows, create a separately named corrective staging run from the immutable discovery result, and never retry a write whose remote outcome is uncertain.
