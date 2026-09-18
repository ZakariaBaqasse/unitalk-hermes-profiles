# A2 FullEnrich Incidental Personal-Email Correction Review

**Profile:** `equinet-a2-enrichment`  
**Decision:** `A2-FULLENRICH-INCIDENTAL-PERSONAL-EMAIL-20260906`  
**Status:** `APPROVED BUSINESS CONFIGURATION — RUNTIME INTEGRATION PENDING`  
**Approved by:** Séverine, Unitalk Operations  
**Approved at:** `2026-09-06T13:38:10Z`

## Applied correction

- Personal email remains excluded from the default FullEnrich request.
- If FullEnrich returns a personal email incidentally, it is retained as `person.personal_email_candidate` with provider provenance, verification status and `incidental_provider_return` collection mode.
- It remains separate from professional email.
- It does not satisfy professional contactability by itself.
- It grants no consent, outreach authority or automatic HubSpot-write authority.
- The existing FullEnrich Search, Lookup, mobile and contact-count rules are unchanged.

## Verification completed

- Personal-email amendment deterministic validation: **47/47 passed**.
- Existing no-integration Farrier workflow: **14/14 operators passed**.
- Existing no-integration Horse Owner workflow: **14/14 operators passed**.
- Language audit: **1,651 files checked, zero findings**.
- Final manifest, dependency and release-integrity verification: **17/17 passed**.
- External provider calls: **0**.
- External business actions: **0**.

## Runtime limitations

FullEnrich and n8n remain disconnected. No API key is installed, no live provider call was executed, and no CRM or outreach action is authorised.
