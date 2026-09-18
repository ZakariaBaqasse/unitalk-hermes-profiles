---
name: a2-foundation-integrity-and-release
description: "Use when A2 repairs or publishes foundation manifests."
version: 0.1.0
author: Unitalk
license: Proprietary
metadata:
  hermes:
    tags: [equinet, a2, governance, integrity, release]
---

# A2 Foundation Integrity and Release

## When to use

Use when an active foundation manifest reports missing files, byte-size drift, SHA-256 mismatches, stale references, or when a corrected successor manifest must be published.

## Integrity model

- Hash exact raw file bytes with SHA-256. Do not canonicalise JSON, normalise Unicode, rewrite newlines or trim whitespace before comparison.
- Treat every active artifact as immutable after publication.
- Treat mutable runtime configuration, credentials, caches and generated run outputs as outside the immutable foundation hash set.
- Preserve every predecessor manifest and release receipt.
- A passing content test does not replace manifest integrity, and a matching hash does not replace syntax or contract validation.

## Diagnosis workflow

1. Read the active manifest and calculate current byte count and raw-byte SHA-256 for every entry.
2. Separate missing files, hash mismatches, byte-count mismatches and invalid references.
3. Compare against versioned release archives and snapshot manifests.
4. Validate the snapshots themselves; a directory named `pre-change` is not trustworthy unless its own hashes match.
5. Inspect mismatched source for token corruption such as `***`, truncated identifiers or ellipses.
6. Compile every affected Python file.
7. Distinguish accidental mutation from legitimate later configuration changes.
8. Reconstruct candidate bytes in a staging directory and require exact agreement with both the published byte count and hash before restoration.

## Repair workflow

1. Capture a pre-repair snapshot with paths, byte counts and hashes.
2. Preserve the predecessor manifest unchanged at a versioned historical path.
3. Restore accidentally mutated immutable files byte-for-byte only when reconstructed bytes match the published hash.
4. Do not restore historical mutable runtime configuration over a working current configuration merely to satisfy an old manifest.
5. Replace mutable configuration entries with a versioned, secret-free runtime-requirements artifact.
6. Publish a successor manifest rather than rewriting the historical manifest.
7. Record predecessor path/hash, repair decision, restored files, excluded mutable files and unchanged permission state.
8. Run hash validation, Python compilation, contract tests and relevant regressions after publication.
9. Verify every release-manifest reference by reading and hashing the target.

## Secret-redaction boundary

Secret redaction belongs at display, log and chat boundaries. It must never rewrite repository files, immutable snapshots or archives. Patterns such as `idempotency_key`, `field_key`, token-count settings and boolean credential controls can be false positives; redacting them in source can create syntactically invalid code while leaving a superficially plausible tree.

## Publication rules

- A successor manifest may change hashes only for deliberately changed artifacts.
- Never refresh expected hashes over unexplained content.
- Do not include `config.yaml` or other mutable operational files in the immutable active-file list.
- Manifest publication does not activate integrations, spend, CRM writes or outreach.
- Report manifest version/hash, active-file count, validation, predecessor preservation and remaining gates.

## Supporting material

Use `scripts/validate_manifest.py` for generic raw-byte integrity and Python-syntax checks. See `references/manifest-redaction-repair.md` for the proven reconstruction pattern and pitfalls.