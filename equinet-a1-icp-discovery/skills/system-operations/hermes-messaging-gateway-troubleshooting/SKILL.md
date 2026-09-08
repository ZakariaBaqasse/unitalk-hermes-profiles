---
name: hermes-messaging-gateway-troubleshooting
description: Use when Telegram or profile gateways will not connect.
version: 1.0.0
status: validated
---

# Hermes Messaging Gateway Troubleshooting

Use this skill when a configured messaging platform shows `connecting`, does not answer, appears attached to the wrong profile, or behaves differently under a multi-profile gateway.

Treat the current Hermes documentation as authoritative. Load the bundled `hermes-agent` skill when available; if it is unavailable, inspect the live documentation instead of guessing commands or configuration keys.

## Evidence ladder

Diagnose these as separate states:

1. **Credential persisted** — the intended profile's `.env` or supported secret source contains the required key.
2. **Credential valid** — a bounded provider API probe accepts it.
3. **Adapter loaded** — the owning gateway process has enumerated that profile and platform.
4. **Adapter connected** — current logs/status show a successful live connection rather than a retry loop.
5. **Sender authorized** — the user/chat allowlist or pairing state permits the incoming message.
6. **Message delivered** — platform privacy, mention, webhook, and group rules permit the update to reach Hermes.

Do not treat a UI badge such as `Credentials set` as proof of states 2–6.

## Profile-aware diagnosis

1. Identify the intended profile explicitly; do not trust a cached dashboard selection or process-global `HERMES_HOME` alone.
2. Run profile-qualified status checks, for example:

   ```bash
   hermes -p <profile> gateway status
   hermes gateway list
   ```

3. Inspect the intended profile's actual configuration files. Report only whether required keys are present and how many allowlist entries exist; never print secret values.
4. Compare the intended profile with other installed profiles by key presence only. A credential may have been saved under the launch profile rather than the profile visible in the UI.
5. Check the relevant profile gateway log for connection, authorization, duplicate-token, webhook, timeout, proxy, or circuit-breaker evidence.

## Multiplexed gateways

When the default profile has `gateway.multiplex_profiles: true`:

- the default gateway is the sole inbound process;
- named-profile status can look stopped until that profile's adapters have been loaded by the multiplexer;
- each named profile must persist its own credentials in its own secret scope;
- the same polling bot token cannot be assigned to two profiles concurrently;
- after changing a profile `.env` or messaging config, restart the **default multiplexer**, not a separate named-profile gateway;
- do not use `--force` merely to bypass the multiplexer guard, because that risks two pollers and token/port conflicts.

## Safe credential repair

Moving or copying a bot credential between profiles is a security-boundary change. Require explicit user direction before modifying another profile.

For an authorized move:

1. Confirm the source contains the required platform keys and the destination does not already contain conflicting values.
2. Move all related keys together, including the allowlist and any webhook/proxy/home-channel settings that are actually present.
3. Remove the keys from the source so the same polling token is not active in two profiles.
4. Write atomically and preserve restrictive permissions (`0600`).
5. Validate only with redacted output: key presence, destination/source state, permission mode, provider API success, and non-secret bot identity.
6. Restart the gateway owner and then verify live adapter status.

Never expose tokens in command output, process listings, logs, chat, hashes intended as identifiers, or tool arguments when a secret-safe method is available. Avoid broad `ps` output because launch commands can embed encoded configuration or credentials.

## Restart boundary

A gateway restart requested from a process currently hosted by that gateway may be blocked because terminating the parent would kill the command before it completes. Do not bypass that safeguard.

If restart is blocked:

- use the dashboard's gateway restart control, or
- ask the user to run the restart from a separate host/container shell.

In multiplex mode, restart the default profile's gateway. Do not claim the repair is live until status/log evidence confirms that the target profile's adapter connected after restart.

## Telegram-specific checks

- Validate the token with Telegram `getMe`, emitting only success and the public bot username.
- Confirm at least one allowed user, global allow rule, or approved pairing exists.
- For DMs, test with `/start` or `/whoami` after connection.
- For groups, check BotFather privacy mode, group allowlists, mention requirements, and whether the bot was removed/re-added after a privacy-mode change.
- If webhook mode is configured, verify the public HTTPS endpoint and secret; otherwise expect long polling.
- Treat repeated `ReadError`, timeout, 429, or circuit-breaker messages as a network/runtime issue distinct from credential persistence.

## Verification checklist

- [ ] Intended profile identified from explicit profile-qualified checks.
- [ ] Required credentials are persisted in that profile without exposing values.
- [ ] No duplicate polling token remains in another active profile.
- [ ] Credential validity was tested independently when safe.
- [ ] Correct gateway owner was restarted after configuration changes.
- [ ] Adapter connected according to current status/log evidence.
- [ ] Sender authorization and Telegram DM/group delivery rules were checked.
- [ ] User received a real response before declaring end-to-end success.

## Reference

See `references/multiplex-profile-telegram-diagnostics.md` for a compact diagnostic matrix and secret-safe command patterns.
