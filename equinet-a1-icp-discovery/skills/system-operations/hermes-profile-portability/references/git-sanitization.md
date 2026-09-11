# Git sanitization for Hermes profile exports

This reference provides a conservative baseline. Adapt the allowlist and ignore rules to the profile’s actual purpose and data-governance requirements.

## Baseline `.gitignore`

```gitignore
# Credentials and local configuration
**/.env
**/.env.*
!**/.env.example
**/config.yaml
**/config.back.yaml
**/config.yaml.*.bak
**/auth.*
**/*credentials*
**/*secret*

# SQLite and process state
**/*.db
**/*.db-wal
**/*.db-shm
**/*.lock
**/*.pid
**/.hermes_history
**/gateway_state.json
**/processes.json

# Generated/runtime directories
**/cache/
**/logs/
**/runtime/
**/tmp/
**/sessions/
**/pairing/
**/pending_messages/
**/backups/
**/home/
**/audio_cache/
**/image_cache/

# Personal/local memory; review before sharing
**/memories/
```

A basename pattern such as `state.db` matches that basename at any depth, while an explicit `**/state.db` makes the intent clearer to reviewers.

Do not blindly ignore every file containing `secret` if the repository intentionally includes secret-management documentation or schemas. Prefer an explicit allowlist for high-assurance exports.

## Stage and inspect

Install the ignore rules before staging:

```bash
git add .gitignore
git add -A
git status --short
git diff --cached --name-only
```

Check whether a specific path is ignored and identify the matching rule:

```bash
git check-ignore -v --no-index path/to/file
```

A filename gate for the staged index:

```bash
git diff --cached --name-only --diff-filter=ACMR \
  | grep -Ei '(^|/)(\.env($|\.)|state\.db|.*\.(db|db-wal|db-shm)$|.*\.(pem|key)$|id_(rsa|ed25519)$|auth[^/]*|credentials?[^/]*|secrets?[^/]*|.*\.lock$|.*\.pid$|cache/|logs/|runtime/|tmp/|sessions/|pairing/|pending_messages/|backups/|home/|memories/)'
```

Expected result: no output. Review matches rather than automatically deleting them. Unstage an unwanted path with:

```bash
git restore --staged -- path/to/file
```

Review the largest tracked working-tree files:

```bash
git ls-files -z | xargs -0 -r du -h | sort -h | tail -n 30
```

## Scan exactly what is staged

A working-directory scan includes ignored local files and can obscure what will actually be committed. Export the staged index to a temporary directory, then scan that directory. Example using Gitleaks in Docker:

```bash
(
  tmp="$(mktemp -d)"
  trap 'rm -rf "$tmp"' EXIT
  git checkout-index --all --prefix="$tmp/"
  docker run --rm \
    -v "$tmp:/repo:ro" \
    zricethezav/gitleaks:latest \
    dir --redact --no-banner /repo
)
```

Resolve every real finding. A clean scanner result lowers risk but does not replace manual review; custom tokens, private URLs, customer data, and messaging identifiers may not match generic rules.

## Verify outgoing history

Before the first push, inspect prohibited paths in all reachable history:

```bash
git rev-list --objects --all \
  | grep -Ei '(^|/)(\.env($|\.)|state\.db|.*\.(db|db-wal|db-shm)$|.*\.(pem|key)$|id_(rsa|ed25519)$)'
```

Expected result for a new sanitized repository: no output.

For an existing remote, inspect only the objects being introduced by the branch:

```bash
git rev-list --objects origin/main..main \
  | grep -Ei '(^|/)(\.env($|\.)|state\.db|.*\.(db|db-wal|db-shm)$|.*\.(pem|key)$|id_(rsa|ed25519)$)'
```

## Remove a prohibited blob from unpushed commits

If the current branch contains only local, unpushed commits and the final working tree is already sanitized:

```bash
git branch backup/before-sanitization
git reset --soft origin/main
git commit -m "Recommit sanitized profile changes"
```

This rebuilds the outgoing work as one commit from the upstream base while preserving the current index and working tree. Verify `origin/main..main` before pushing. The local backup branch intentionally retains the old commits, so an `--all` search will still find them until that backup and associated reflogs are removed.

For shared/pushed history, coordinate before rewriting. Rotate any credential that reached a remote repository, regardless of later history cleanup.

## Suggested reusable repository layout

```text
profile-repository/
├── .gitignore
├── README.md
├── profile/
│   ├── SOUL.md
│   ├── profile.yaml
│   ├── config.example.yaml
│   ├── configurations/
│   ├── hooks/
│   ├── plugins/
│   ├── scripts/
│   └── skills/
└── setup/
    └── README.md
```

Document local credential injection and runtime-directory creation in `setup/README.md`; never ship populated credential or state files as examples.
