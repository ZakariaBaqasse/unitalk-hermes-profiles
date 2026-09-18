# Manifest Redaction Repair Pattern

## Symptom

A manifest created from exact raw-byte hashes later reports small byte-count differences. Source files contain fragments such as `***`, truncated identifiers or `...`, and may no longer compile. Snapshot manifests can show the same mismatch because the redactor touched both active and backup copies after their hashes were recorded.

## Diagnosis

1. Recalculate SHA-256 over raw bytes.
2. Compare expected and actual byte sizes.
3. Search source and policies for redaction markers.
4. Compile mismatched Python files.
5. Check a separately packaged archive for intact earlier lines.
6. Reconstruct each candidate in staging only.
7. Accept reconstruction only if both expected size and SHA-256 match exactly.

A successful exact-hash reconstruction proves the hash algorithm is not the fault and identifies the mutation precisely.

## Repair split

- **Immutable source/policy:** restore exact published bytes.
- **Mutable runtime config:** preserve the working current configuration; remove it from the next immutable manifest and replace it with a versioned requirements contract.
- **Historical manifest:** archive unchanged.
- **Successor manifest:** record the repair, predecessor hash, excluded mutable path, replacement policy and unchanged permissions.

## Required verification

- zero missing/hash/byte mismatches;
- every active Python file compiles;
- predecessor manifest hash still matches its historical release;
- every release-reference hash resolves;
- runtime configuration remained unchanged if intentionally preserved;
- relevant business and integration regressions pass;
- no integration permission was accidentally enabled.

## Pitfall

Do not blindly regenerate expected hashes from corrupted files. That blesses the corruption and destroys the evidence needed to recover the intended release.
