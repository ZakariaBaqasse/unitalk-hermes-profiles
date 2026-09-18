# Redaction-Corruption Recovery Pattern

## Diagnostic signature

A release manifest passed when published, but later reports small byte-size reductions and SHA-256 mismatches. Source files contain malformed tokens such as:

```text
idempotency_key=object...ey"]
field_key=*** "value"
TRACKING_KEYS=*** "value"}
```

Policy or configuration scalars may become:

```yaml
credentials_logged: ***
model_max_output_tokens_per_call: ***
```

This indicates a secret-redaction transform was applied to stored files rather than only to displayed output.

## Confirming the cause

1. Calculate SHA-256 over exact bytes.
2. Compile affected source files.
3. Validate every alleged snapshot against its own snapshot manifest.
4. Locate a trusted release archive containing at least one expected digest.
5. Reconstruct missing tokens in memory or a staging tree.
6. Accept the diagnosis only when reconstructed files reproduce both expected byte counts and expected digests.

A successful exact reconstruction distinguishes corruption from line-ending or canonicalisation differences.

## Recovery pattern

- Preserve the corrupted state before repair.
- Restore files only from candidates that match their published digests exactly.
- Re-run syntax and behavioural tests.
- Preserve the predecessor manifest unchanged.
- If a mutable configuration changed legitimately, do not roll it back solely for checksum parity. Publish a successor manifest excluding it and add a versioned requirements artifact instead.
- Record that integration permissions did not change unless separately approved.

## Prevention

- Redact only tool output, logs, and chat displays.
- Never send source trees or release archives through a mutating redaction pipeline.
- Validate snapshots immediately after copying.
- Make published artifacts read-only when practical.
- Keep mutable runtime configuration, secrets, caches, and generated state outside immutable manifests.
