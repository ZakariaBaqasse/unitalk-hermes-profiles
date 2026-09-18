# A2 Active Foundation Integrity Repair

**Decision:** `A2-ACTIVE-MANIFEST-INTEGRITY-REPAIR-20260915`  
**Recorded:** `2026-09-15T10:24:25Z`  
**Status:** `APPROVED FOR IMPLEMENTATION BY USER INSTRUCTION`

Manifest 1.3.1 was published correctly, then an output-secret-redaction transform altered ordinary source tokens and runtime-policy scalar values. The mutable Hermes `config.yaml` also changed later. Seven immutable artifacts are restored byte-for-byte to their published hashes. The live configuration is preserved and removed from the immutable hash set. A versioned, secret-free runtime-requirements artifact replaces it.

This repair changes no integration permission and grants no production, provider, CRM-write or outreach authority.
