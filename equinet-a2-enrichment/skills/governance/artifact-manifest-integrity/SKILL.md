---
name: artifact-manifest-integrity
description: "Use when a versioned release manifest reports hash drift."
version: 1.0.0
author: Unitalk
license: Proprietary
metadata:
  hermes:
    tags: [governance, manifests, sha256, release-integrity, recovery]
---

# Artifact Manifest Integrity

Use this skill when an immutable release, foundation, package, or deployment manifest no longer matches files on disk.

## Principle

A mismatch is evidence of a state change, not permission to replace the expected hash. Determine whether the file was corrupted, intentionally changed, transformed during transport, or incorrectly treated as immutable before selecting a remedy.

Hash exact raw bytes unless the manifest explicitly defines another canonicalisation method.

## Workflow

1. **Freeze and inventory**
   - Copy the manifest and every mismatching file to a timestamped pre-repair directory.
   - Record path, byte size, raw-byte SHA-256, and modification time.
   - Do not edit the active manifest yet.

2. **Validate the hashing contract**
   - Inspect the manifest builder and validators.
   - Confirm raw bytes versus canonical JSON, line-ending rules, and encoding.
   - Independently calculate every digest.

3. **Trace provenance**
   - Search historical manifests, immutable archives, release packages, snapshots, and release records for the expected digest.
   - Validate snapshots against their own manifests; a directory named `pre-change` is not trusted unless its hashes still match.
   - Treat timestamps as supporting evidence only.

4. **Classify each mismatch**
   - **Exact corruption:** intended bytes can be reconstructed and reproduce the published digest.
   - **Intentional immutable change:** content changed legitimately and requires a new artifact version.
   - **Mutable-file drift:** the manifest incorrectly pinned operational configuration or generated state.
   - **Unknown:** no trustworthy reconstruction exists; hold publication and escalate.

5. **Check for destructive redaction**
   - Scan source and policy files for `***`, truncated identifiers such as `foo...bar`, malformed comparisons, and replaced scalar values.
   - Compile every affected Python file.
   - Secret masking belongs at display/log boundaries; it must never rewrite source, snapshots, or release artifacts.

6. **Repair in staging first**
   - Reconstruct candidate bytes under a staging directory.
   - Require exact expected size and SHA-256 for a restoration.
   - Run syntax and applicable behavioural tests against staged or restored files.
   - Do not call a semantically similar file an exact restoration unless its digest matches.

7. **Choose the publication path**
   - Restore an immutable artifact in place only when the reconstructed bytes exactly match its published digest.
   - Never silently update an old manifest to bless unexplained content.
   - When content changed intentionally, preserve the predecessor and publish a successor manifest.
   - Exclude mutable runtime configuration from immutable hash sets. Replace it with a versioned, secret-free requirements or policy artifact.

8. **Publish a successor safely**
   - Preserve the predecessor manifest under a versioned historical path.
   - Increment the manifest version.
   - Recompute path, byte count, and raw-byte SHA-256 for every active entry.
   - Record the predecessor hash, repair decision, restored files, excluded mutable paths, unchanged permissions, and external-action count.
   - Keep release records outside the active manifest when including them would create a circular hash dependency.

9. **Verify after publication**
   - Validate every active path, byte count, and digest.
   - Compile all active Python files.
   - Validate referenced runtime policies and requirements separately.
   - Run the release’s behavioural regression suite.
   - Verify every release-record reference by reading it back.
   - Confirm the predecessor copy still matches its original release digest.

## Decision rules

- **Restore:** exact intended bytes are recoverable and match the old digest.
- **Supersede:** semantics changed, mutable configuration evolved, or the old digest cannot be reproduced safely.
- **Hold:** provenance is missing or two authoritative artifacts conflict.

Do not restore a historical operational configuration merely to make a checksum green if doing so would alter the current runtime. Preserve it as history and remove it from the successor’s immutable scope.

## Required evidence

- expected and actual byte counts and SHA-256 values;
- reconstruction source and method;
- staged exact-match result;
- syntax/test results;
- predecessor manifest path and digest;
- successor manifest path and digest;
- explicit statement of whether permissions or external actions changed.

## Support files

- `scripts/verify_manifest.py` performs generic raw-byte hash, size, duplicate-path, optional Python compilation, and redaction-marker checks.
- `references/redaction-corruption-recovery.md` records the validated recovery pattern and diagnostic indicators.

## Pitfalls

- Updating checksums before explaining the content change destroys the integrity signal.
- Backups may have been transformed by the same faulty process as active files.
- File names such as `pre-change` or `frozen` do not prove immutability.
- Whole-tree secret scrubbers can corrupt ordinary identifiers containing words such as `key`, `token`, or `credential`.
- Mutable application configuration should not be a release-foundation dependency.
- A passing manifest check does not replace syntax and behavioural tests.
