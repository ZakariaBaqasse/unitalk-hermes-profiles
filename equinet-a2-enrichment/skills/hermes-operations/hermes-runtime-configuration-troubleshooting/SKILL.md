---
name: hermes-runtime-configuration-troubleshooting
description: "Use when Hermes runtime settings conflict with tools."
version: 0.1.0
author: Hermes Curator
license: Proprietary
metadata:
  hermes:
    tags: [hermes, troubleshooting, configuration, profiles, terminal]
---

# Hermes Runtime Configuration Troubleshooting

## When to use

Use when a Hermes tool behaves as though a different backend, profile, working directory, model, provider, or environment setting is active than the value shown in the current profile.

## Goal

Identify the effective runtime value, its winning source, and any cross-profile or long-lived-process leakage. Apply the narrowest safe correction and verify it against the failure mode rather than merely reading the configuration file.

## Authoritative sources

1. Load the `hermes-agent` skill when available.
2. Consult the current Hermes documentation, especially Configuration Precedence and the relevant subsystem page.
3. Treat live files, process state, logs, and controlled reproductions as evidence. Do not infer runtime state from a settings screen alone.

## Investigation workflow

### 1. Establish every configuration scope

Record separately:

- active profile home (`HERMES_HOME`);
- root/default Hermes home;
- selected profile `config.yaml` and `.env`;
- root/default `config.yaml` and `.env`;
- managed-scope configuration, if present;
- launcher, gateway, dashboard, cron, or container configuration that may seed values.

Never assume “configured local” means an explicit profile setting. Distinguish an explicit key from a merged default.

### 2. Resolve precedence and ownership

For non-secret settings, an explicit `config.yaml` value normally wins over `.env`; CLI arguments may override both. Check whether the active profile explicitly owns the key or only inherits a default. A profile with no explicit section may preserve an already-exported environment value by design.

For terminal issues, compare at least:

```bash
HERMES_HOME=<root> hermes config get terminal.backend
HERMES_HOME=<profile> hermes config get terminal.backend
```

Also inspect only the relevant `TERMINAL_*` keys. Do not print an entire environment or process command line because those surfaces may contain credentials.

### 3. Reproduce the effective value, not just the file value

Use a fresh subprocess and deliberately inject the suspected inherited value. For terminal configuration:

```bash
HERMES_HOME=<profile> TERMINAL_ENV=ssh <python> -c \
  "from tools.terminal_tool import _get_env_config; print(_get_env_config()['env_type'])"
```

This determines whether explicit profile configuration overrides an inherited backend. Keep the probe read-only and report only booleans for credential presence.

### 4. Correlate the first failure with environment lifecycle

Inspect logs around:

- initial environment creation;
- idle cleanup or command timeout;
- the first recreation under the wrong backend;
- profile/gateway/dashboard start or reload events.

A cached environment can hide a wrong global value until cleanup. A late switch after timeout often means recreation sampled different process-global state; the timeout itself may be incidental.

### 5. Inspect implementation and version when behavior contradicts docs

Locate the code that bridges config into environment variables and determine whether it is:

- process-global;
- profile-scoped;
- one-shot or repeated;
- applied before or after the selected profile is established.

Compare the installed build/version with newer source and regression tests. Do not claim a fix is released merely because it exists in a local checkout or upstream branch.

### 6. Apply the narrowest safe correction

Preferred order:

1. Make the active profile’s intended setting explicit.
2. Verify the effective runtime under a deliberately conflicting inherited environment.
3. Correct the root/deployment template only with explicit authorization when it belongs to another profile or deployment owner.
4. Upgrade/rebuild Hermes when the installed implementation has a confirmed profile-scoping defect.

Do not configure fake SSH host/user values to silence a backend-selection error.

### 7. Verify completion

A terminal-backend correction is verified only when all are true:

- the profile file explicitly shows the intended backend;
- `hermes config get` resolves the intended backend;
- a poisoned-inheritance probe still resolves the intended backend;
- a real terminal command succeeds;
- no external/default profile was silently modified.

If a process restart is required for global state to clear, say so explicitly and do not claim the live process is fixed before retesting after restart.

## Common pitfalls

- Reading only the selected profile and missing the root launcher profile.
- Treating `.env` as authoritative over an explicit non-secret YAML key.
- Confusing a built-in default with an explicit profile override.
- Retrying SSH and adding credentials when the intended backend is local.
- Assuming the backend changed at the failure timestamp; cached environments can delay visibility.
- Dumping full `ps`, environment, or container command output into chat when it may expose secrets.
- Editing a default/root profile from a profile-scoped session without authorization.
- Describing a newer source-tree fix as deployed before the running build is updated and verified.

## Session-derived reference

See `references/terminal-backend-profile-leak.md` for a concrete multi-profile terminal investigation, reproduction pattern, and safe mitigation.
