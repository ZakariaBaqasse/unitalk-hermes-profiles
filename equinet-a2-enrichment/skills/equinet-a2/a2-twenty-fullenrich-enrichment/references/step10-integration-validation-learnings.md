# Step 10 Integration Validation Learnings

## Company selection

Translate natural-language scope into allowlisted Twenty filters. Apply them server-side and verify them again locally before claiming. `latest` means `createdAt[DescNullsLast]` unless the user requests recently updated records. Prefer immutable Company ID; reject ambiguous exact names. Reprocessing terminal records requires explicit intent.

## Existing linked People

Lookup a supported existing Person before Search. A retained target must have verified identity, confirmed Company match, `CURRENT_AT_COMPANY`, and `PRIMARY` priority. Selected existing targets proceed to Contact Enrichment for work email and phone; non-primary or non-current People remain linked, receive A2 classification fields, and do not receive contact enrichment.

`a2RoleStatus` is a target-Company relationship, not role priority:

- `CURRENT_AT_COMPANY`
- `NOT_CURRENT_AT_COMPANY`
- `UNVERIFIED`

## Provider controls

FullEnrich requests use work email and `contact.phones`; A2 retains a mobile/direct candidate by preferring `most_probable_phone`, rejecting inactive or ownership-mismatch values, and accepting mobile or otherwise unclassified active values. Normalize URL-form Company domains to hostnames before provider calls.

Credit caps are 50 per run, 100 per UTC day, and 250 for the controlled pilot. Reserve estimated maximum credits atomically before paid calls, settle provider-reported actual credits afterward, and block duplicate paid requests.

## No-target branch

One bounded role-specific follow-up Search is allowed after an approved-title Search returns no suitable Person. If it also returns no result, skip Contact Enrichment and write `COMPLETED_NO_TARGET` plus `target_role_not_found`, then reconcile the exact Twenty read-back.

## Reconciliation

Compare ISO timestamps semantically, not as literal strings: Twenty may return `.000Z` for an equivalent second-precision value. Company status must be the final operation and successful HTTP writes do not count until read-back matches.

## Status boundary

The deployment status is `INTEGRATION_VALIDATION_IN_PROGRESS`, not production acceptance. Twenty Company filtering/claim/status write and FullEnrich account/Search are live-validated; positive Lookup, Contact Enrichment, pricing, and Person create/association reconciliation remain pending.
