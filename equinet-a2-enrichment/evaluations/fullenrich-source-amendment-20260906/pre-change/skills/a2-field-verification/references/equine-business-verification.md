# Equine-Business Verification

- Accept stable/farm type, disciplines, breeds, service area and explicit operating facts only when the source states them directly or an authorised Equinet representative confirms them.
- Preserve the exact source claim and evidence reference.
- For a Horse Owner record, require at least one verified breed value for enrichment completeness. Preserve `Mixed` or `Other` exactly when verified; never use either as a guessed fallback.
- For an existing matched HubSpot record, `Contact.owner_horse_count` is authoritative. For a net-new prospect, or when that property is empty, accept an exact horse count only from approved A1 evidence, authorised Equinet first-party data, recorded Equinet confirmation or the prospect-owned official website.
- Never infer horse count from acreage, stall capacity, photos, events, staff size or marketing language.
- Ignore `horse_count_range` and do not create new `horse_count_band` values.
- A verified public business location requires `state_region` and `country_code`. Retain the complete public address, city and postal code when available.
- Keep uncorroborated or ambiguous claims `present_unverified` for Wave 3 evidence assessment rather than presenting them as verified.
- Missing required business information creates a visible gap and remains eligible for the consolidated human review; it never rejects the prospect or changes the A1 score.
