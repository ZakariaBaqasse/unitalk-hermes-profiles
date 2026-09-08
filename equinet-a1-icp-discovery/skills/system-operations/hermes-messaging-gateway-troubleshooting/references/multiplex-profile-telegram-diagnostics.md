# Multiplex Profile and Telegram Diagnostic Matrix

Use this reference when a profile UI says credentials are configured but Telegram remains `connecting` or silent.

## Symptom-to-evidence matrix

| Symptom | Likely layer | Verify | Corrective action |
|---|---|---|---|
| `Credentials set`, but profile `.env` lacks Telegram keys | UI/profile-context mismatch | Check the intended profile path directly and compare key presence across profiles | Re-enter credentials in the intended profile, or explicitly authorize a move |
| Named profile reports stopped while default gateway runs | Multiplex ownership | Check default config for `gateway.multiplex_profiles: true` | Restart the default multiplexer; do not launch a second poller |
| Credentials were changed but state remains `connecting` | Stale running adapter | Compare file modification time with gateway start time and inspect current logs | Restart the owning gateway from outside the hosted session |
| Token accepted but messages are ignored | Authorization or Telegram delivery gate | Check allowed-user count/pairing; distinguish DM from group | Correct allowlist/pairing; for groups check privacy and mention settings |
| Repeated timeout or `ReadError` | Network/proxy/Telegram runtime | Inspect current platform logs and proxy settings | Correct network/proxy state; resume/restart only after upstream is healthy |
| Duplicate/conflict response | Same token polled twice | Compare token ownership internally without printing values | Keep the token in exactly one profile/process |

## Secret-safe inspection pattern

Emit only facts such as:

```text
TELEGRAM_BOT_TOKEN_SET=true
TELEGRAM_ALLOWED_USERS_SET=true
ALLOWED_USER_COUNT=1
```

Do not print `.env`, broad environment dumps, or full process command lines. Process arguments may contain encoded configuration and credentials.

## Token validity probe

A bounded Telegram `getMe` call can distinguish invalid credentials from gateway lifecycle problems. The output should contain only:

```text
TOKEN_VALID=true
BOT_USERNAME=<public username>
```

Never print the request URL because it contains the token.

## Authorized credential move

When the user explicitly chooses to move a bot between profiles:

1. Read source and destination internally.
2. Move every present `TELEGRAM_*` assignment as one transaction.
3. Refuse if the destination already has conflicting Telegram keys.
4. Atomically rewrite both files and preserve mode `0600`.
5. Verify required keys exist only at the destination.
6. Validate the token with a redacted `getMe` probe.
7. Restart the default multiplexer when multiplexing is enabled.
8. Verify a real inbound `/whoami` or `/start` round trip before declaring success.

## Restart ownership

For a default-profile multiplexer, use the default profile's restart control. A named profile must not be force-started beside it. If the current agent turn is hosted by the gateway and restart is refused by the self-termination guard, leave the files in a validated state and require the user to restart through the dashboard or a separate shell. Report the remaining restart as an explicit blocker, not as completed work.
