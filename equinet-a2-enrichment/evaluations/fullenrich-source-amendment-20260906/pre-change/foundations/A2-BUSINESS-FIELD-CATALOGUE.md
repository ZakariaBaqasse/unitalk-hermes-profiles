# Equinet A2 Business Field Catalogue

**Version:** `0.2.0`  
**Status:** `EQUINET-CONFIRMED BUSINESS CONFIGURATION — NO INTEGRATION ACTIVATION`  
**Canonical schema:** `1.0.0`

## Purpose

The machine-readable catalogue at `foundations/contracts/business/a2-business-field-catalogue-0.2.0.json` is authoritative. It defines 33 business fields, segment priorities, collection boundaries, mappings and the confirmed role/contact policies.

## Confirmed contact policy

- Retain one selected named contact by default.
- Retain at most two selected contacts when a large organisation or shared purchasing or operational responsibility is documented.
- Record the reason for the second contact.
- Do not invent a contact or use an unrelated role.
- If no suitable target-role person is found, preserve organisation information and label the record `Contact Needed / Needs Review`.
- Attempt both professional email and business phone; one verified channel satisfies the minimum when the other is unavailable.

## Confirmed Farrier roles

### Primary

- Independent Farrier / Self-Employed Farrier
- Farrier Business Owner / Owner
- Founder / Co-Founder of a Farrier Business
- Lead Farrier / Head Farrier
- Professional Farrier

### Secondary

- Associate Farrier / Staff Farrier
- Farrier at a Multi-Farrier Practice
- Business Manager / Office Manager / Practice Manager when commercial or purchasing responsibility is verified

### Review only

- Apprentice Farrier / Student Farrier

### Excluded when the stated condition is verified

- Farrier school instructor or educator with no current commercial/professional Farrier activity
- Retired or inactive Farrier with no current professional activity

An A2 exclusion finding creates a requalification signal for A1; A2 does not change the A1 score.

## Confirmed Horse Owner roles

### Primary

- Owner / Horse Owner
- Farm Owner / Farm Manager
- Stable Owner / Stable Manager
- Equestrian Centre Owner / Manager
- Breeding Farm Owner / Breeding Manager
- Managing Director / General Manager of an equine business
- Operations Manager when horse-care or purchasing responsibility is verified

### Secondary

- Head Trainer / Head Coach
- Trainer / Professional Rider
- Barn Manager / Yard Manager
- Equine Program Manager
- Purchasing Manager / Procurement Manager
- Assistant Manager / Operations Coordinator when purchasing responsibility is verified

## Horse Owner enrichment priorities

Required for enrichment completeness:

- current role;
- stable/farm type;
- exact horse count;
- at least one verified breed;
- organisation name;
- public business location with state and country;
- one verified professional email or business phone, after attempting both.

Attempt the complete address and retain address, city and postal code when available. Preserve verified `Mixed` or `Other` breed values explicitly.

## Horse-count policy

- Existing matched HubSpot record: `Contact.owner_horse_count` is authoritative.
- Net-new prospect or empty HubSpot value: explicit approved A1 evidence, authorised Equinet first-party data, recorded Equinet confirmation or the prospect-owned official website may support an exact count.
- Never infer horse count.
- Ignore `horse_count_range`.
- Do not create new `horse_count_band` values; preserve historical values only.
- Synchronisation to `owner_horse_count` requires final human review and a guarded HubSpot write with read-back reconciliation.

## Missing information

Missing required data creates a visible gap and an incomplete record. It never rejects the prospect or changes the A1 score. Research exhaustion triggers the consolidated human review. The reviewer may request more work, hold for a true dependency, reject for an explicit business reason, or approve collection of the missing information during sales discovery.
