# Equinet A2 Preliminary HubSpot Mapping

**Version:** `0.3.1`  
**Status:** `EQUINET-CONFIRMED BUSINESS SEMANTICS — LIVE VERIFICATION PENDING`  
**HubSpot connection:** not connected  
**Global write authorisation:** false

## Operating boundary

HubSpot remains Equinet's final CRM system of record. The machine-readable mapping at `foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.3.1.json` is authoritative. All mappings remain read-and-propose only until live metadata, permissions, workflow dependencies and guarded-write controls are verified.

## Confirmed horse-count mapping

- Existing matched record: `Contact.owner_horse_count` is authoritative.
- Net-new prospect or empty HubSpot value: A2 may propose an exact count from explicit approved evidence.
- The proposed value may be synchronised to `owner_horse_count` only after the final human review, guarded write authorisation, idempotency checks and read-back reconciliation.
- `horse_count_range` is ignored.
- `organisation.horse_count_band` is deprecated for new revisions and has no active HubSpot destination.
- A difference from an existing `owner_horse_count` preserves HubSpot and requires human conflict review.

## Other confirmed priorities

- Current role maps provisionally to `Contact.jobtitle`.
- Breeds map provisionally to `Contact.owner_breeds`; live enum/multivalue behaviour must be verified.
- Stable/farm type mapping remains blocked until the enum conversion is verified.
- Public business location maps provisionally to Company address, city, state, postal code and country fields.
- Professional email and phone remain subject to protected-field, consent, workflow and human-review controls.

No CRM write, list enrolment, workflow trigger or outreach action is authorised by this mapping.

## FullEnrich mobile clarification

`person.mobile_phone` is now a permitted proposal field for selected contacts and maps provisionally to `Contact.mobilephone`. Existing manual values remain protected. No HubSpot write is authorised.
