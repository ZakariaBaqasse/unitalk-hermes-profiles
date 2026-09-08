# Twenty URL trailing-slash reconciliation observation

## Observed live behavior

In the 2026-09-01 Company staging slice, Twenty accepted URLs ending in `/` for `domainName.primaryLinkUrl` and `sourceUrl.primaryLinkUrl`, then returned the same URLs without the terminal slash on `find_one_company` read-back.

This occurred for both `http` and `https` URLs and for source-only records as well as records with `domainName`.

## Required handling

1. Preserve the immutable emitted plan plus raw `find_one_company` and normalized read-back responses.
2. Use the deterministic helper’s tested URL equivalence: accept only HTTP(S) link values that differ solely by terminal `/`; scheme, host, path, query and fragment must remain identical.
3. Cover both an accepted trailing-slash case and a rejected changed-path case in the helper tests before treating an earlier mismatch as staged.
4. Re-run reconciliation against the already persisted read-back; never issue a second create because of this compatibility difference.
5. If any difference remains after the narrow equivalence rule, retain `sync_failed` with literal expected and returned values.

## Cron audit requirement

Persist raw Twenty preflight responses before deciding or writing. If none exist, classify the result as a concrete preflight/capability failure—not a payload-safety failure—and do not claim an API rejection.

- `https://horseprofinder.com/.../diego-almeida-cjf/` → returned without `/`
- `http://www.breedersfarriersupply.com/` → returned without `/` (domain and source)
- `https://soundhorse.com/` → returned without `/` (domain and source)

This is a compatibility note, not authorization to manually alter a plan payload or waive reconciliation.