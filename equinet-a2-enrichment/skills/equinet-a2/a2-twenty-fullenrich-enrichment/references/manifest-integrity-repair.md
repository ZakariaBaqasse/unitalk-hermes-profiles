# Manifest integrity diagnosis and repair

Use this reference when a versioned A2 foundation or release manifest reports SHA-256 drift.

## Diagnose before changing anything

1. Hash the exact raw bytes of every manifest entry. Do not canonicalise JSON, normalise Unicode, or change line endings.
2. Compare both the recorded byte count and SHA-256 with the live file.
3. Validate every available snapshot against its own snapshot manifest. A directory named `pre-change` is not evidence that its contents remain intact.
4. Inspect mismatched source and policy files for redaction fingerprints such as `***` or truncated identifiers containing `...`.
5. Compile affected Python files. Redaction can turn ordinary expressions involving `key`, `token`, or similar names into invalid source.
6. Search immutable release archives for bytes matching the recorded hash. Treat a matching archived file as stronger evidence than a mutable working-tree copy.
7. Separate immutable-artifact corruption from legitimate mutable-runtime changes such as a later `config.yaml` update.

## Verified A2 incident pattern

The 1.3.1 foundation drift was not a SHA implementation or line-ending problem. A secret-redaction transform had rewritten ordinary source tokens and policy scalars after publication. Examples included:

- `idempotency_key = handoff["idempotency_key"]` becoming a truncated identifier;
- equality expressions becoming `=***` fragments;
- a tracking-key set becoming `***`;
- booleans and token limits in a runtime policy becoming `***`.

The affected snapshots had also been rewritten, so snapshot names alone were not trustworthy. Exact candidate reconstruction restored the recorded byte counts and hashes and made all affected Python files compile.

`config.yaml` was a separate case: one archived scalar had been redacted, and the live file was later legitimately rewritten by Hermes configuration changes. Mutable live configuration should not be an immutable foundation-manifest member.

## Safe repair procedure

1. Leave the active files and historical manifest unchanged during diagnosis.
2. Reconstruct candidates under a separate staging directory.
3. Accept a candidate only when all three checks pass:
   - exact recorded byte count;
   - exact recorded SHA-256;
   - applicable syntax/schema validation.
4. Restore byte-for-byte only artifacts proven to match the existing manifest. This is restoration, not a new release.
5. Do not “fix” drift by replacing expected hashes with hashes of unexplained or corrupted content.
6. Do not overwrite a currently valid mutable runtime configuration merely to reproduce a historical hash.
7. For mutable configuration drift, preserve the historical manifest and publish an approved successor that replaces `config.yaml` with a versioned, secret-free runtime-requirements artifact.
8. Re-run full active-manifest validation, dependency validation, regressions, and release-link validation.
9. Preserve the prior manifest and release record; never silently rewrite release history.
10. Require Unitalk Operations approval before promoting the successor active manifest.

## Prevention

- Apply secret redaction only to displayed output and logs, never to repository files, archives, or snapshots.
- Validate a snapshot immediately after creation and again before using it for recovery.
- Make release archives immutable or read-only.
- Exclude credentials and mutable profile configuration from immutable foundation manifests.
- Add Python compilation and schema parsing to promotion gates.
- Record the hashing rule explicitly as SHA-256 over exact raw file bytes.
