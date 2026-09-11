---
name: hermes-profile-portability
description: Use when sharing or version-controlling a Hermes profile.
---

# Hermes Profile Portability

Use this skill when copying, exporting, sharing, backing up, or placing a Hermes profile under version control. The goal is to preserve reusable configuration and behaviour while excluding private credentials, personal/session history, machine-local state, and generated runtime artifacts.

## Core principle

Treat a live Hermes profile as a mixed directory, not as a source repository. It contains both reusable assets and host-specific operational state. Prefer constructing a sanitized repository from an explicit allowlist or a carefully reviewed copy rather than committing the profile root wholesale.

`state.db` is the canonical SQLite session/state store. It can contain complete conversation history, system-prompt snapshots, tool calls/results, usage metadata, gateway routing, and runtime bookkeeping. It is not needed to transfer the reusable profile definition. Exclude `state.db`, its WAL/SHM companions, and other runtime databases. Do not use Git LFS to share them.

## Shareable versus local material

Usually shareable after review:

- profile instructions such as `SOUL.md` and `profile.yaml`;
- curated skills and their references/templates/scripts;
- versioned business configurations and schemas;
- reusable scripts, hooks, and plugin source;
- redacted example configuration files with placeholders.

Local or sensitive by default:

- `.env`, credentials, tokens, private keys, auth files, and pairing data;
- `config.yaml` when it contains credentials, private endpoints, chat IDs, or machine-specific paths;
- SQLite databases and `-wal`/`-shm` companions;
- sessions, memories, logs, caches, runtime outputs, temporary files, process IDs, locks, backups, downloaded home directories, and generated media;
- discovery, CRM, customer, contact, or evaluation artifacts unless explicitly approved for sharing.

For necessary configuration, create a sanitized `config.example.yaml` or equivalent. Keep placeholders clearly named and document which values the recipient must supply locally.

## Safe workflow

1. Prefer a new empty repository or a new sanitized export directory.
2. Install `.gitignore` before staging the profile.
3. Stage the intended tree, but do not commit immediately.
4. Audit the staged filenames, not merely the working directory.
5. Inspect the largest staged files.
6. Scan the exact staged snapshot for embedded secrets with an approved scanner.
7. Manually review configuration, scripts, workflow definitions, and documentation for hard-coded credentials or private endpoints.
8. Commit only after the staged-index checks are clean.
9. Inspect the complete outgoing Git object range before pushing.
10. After pushing, verify the remote tree from a fresh clone when practical.

See `references/git-sanitization.md` for commands and a baseline ignore policy.

## Git-history rule

`.gitignore` affects future untracked files only. A file already committed remains in history, and deleting it in a later commit does not remove its earlier blob. Git hosting services evaluate every object reachable from the commits being pushed.

When an oversized or sensitive file exists only in unpushed commits, rewrite those local commits from the upstream base and recommit the clean final tree. Preserve a local backup ref before rewriting. Verify the outgoing range—not `--all` when a local backup branch intentionally retains the old commits.

When secrets reached a remote repository, treat them as exposed: rotate/revoke them. Rewriting or deleting repository history reduces accessibility but is not a substitute for credential rotation.

## Verification standard

Do not call a profile sanitized unless all of the following are true:

- the reviewer can read every candidate file; permission errors make the audit incomplete;
- prohibited filenames are absent from the staged index;
- large staged files have been reviewed;
- a content-level secret scan of the staged snapshot reports no unresolved findings;
- configuration files have been manually checked and use placeholders where needed;
- prohibited blobs are absent from the outgoing revision range;
- no private customer/prospect/runtime data is included without explicit authorization.

Report any unreadable directory or skipped file as a blocker rather than claiming the repository is clean.

## Pitfalls

- Do not assume a clean `git status` means history is clean.
- Do not scan only the working tree when ignored files are present; scan an export of the staged index so the scan exactly matches the proposed commit.
- Do not rely only on filename patterns. Secrets can be embedded in YAML, JSON, Markdown, scripts, workflow definitions, or URLs.
- Do not use `git add -f` during profile packaging unless each forced path was explicitly reviewed.
- Do not commit active cron state or messaging destinations merely to reproduce behaviour; provide templates and setup documentation instead.
- Do not delete a live `state.db` while Hermes processes are using it. Exclude it from the export or stop the relevant processes first.
