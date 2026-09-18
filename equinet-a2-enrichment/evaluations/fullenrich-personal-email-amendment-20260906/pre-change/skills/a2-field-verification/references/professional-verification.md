# Professional Verification

- Preserve the current source title exactly after whitespace normalisation.
- Require evidence that the role is current; otherwise hold the observation for review.
- Treat a title-to-target-role classification as a recommendation, not a sourced title. Use `scripts/classify_a2_target_role.py` and the Equinet-confirmed `0.2.0` role model.
- Require explicit evidence of commercial, purchasing, operational or horse-care responsibility for conditional manager roles.
- Classify an instructor/educator or retired/inactive Farrier as excluded only when the specified absence of current commercial or professional Farrier activity is verified; create a requalification signal for A1 rather than changing the A1 score.
- Do not infer a person-to-organisation relationship from name similarity alone.
- Keep credentials, certifications, service area and dated activity as separate fields with their own evidence.
- Retain explicit professional-profile URLs found on the official site without opening the destination platform.
- Keep person and organisation URLs in their respective canonical fields; ambiguous attribution requires review.
- Do not infer buying authority, consent or an A1 score change from a role or URL.
