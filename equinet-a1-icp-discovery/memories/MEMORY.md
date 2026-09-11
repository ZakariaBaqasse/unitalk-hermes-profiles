Equinet Twenty REST staging must JSON-quote exact filter values because Twenty parses commas as filter separators. Before writes, the worker scans soft-deleted Companies; exact soft-deleted fingerprint/domain matches are held as possible_match with no automatic restore, delete, update, or recreate, since soft-deleted rows can still reserve unique values.
§
Equinet A1 post-n8n routing is entity-aware: every named lead stages a Company; a non-empty `name` also requires one linked Person after Company verification. Phone/email route only to Person when expected, otherwise Company. No-site and terminal enrichment failures remain unscored; website candidates are verified/enriched/scored first.
§
Equinet Twenty `sourceUrl` is acquisition provenance only: use the directory/source URL from the immutable n8n lead, label it with the normalized hostname, and never replace it with the verified official website. The official website belongs only in `domainName`.
§
Hermes deployment uses the default-profile gateway as a multiplexing gateway; named-profile messaging credential changes require restarting the default multiplexer, not starting a second profile gateway.
§
Equinet Twenty Company now has live field `email` (label Email), type EMAILS, nullable/writable, max 10. A1 stages validated public professional email as `{primaryEmail, additionalEmails: []}` and omits invalid/masked values.
§
Equinet A1 field contract: n8n `name`/`person_name` represents only an explicitly identified person. Organisation-only Google Maps records use `business_name` and leave person-name fields empty, so Twenty stages only a Company.
§
Equinet Google Maps cursor semantics: `dataset_exhausted` means one bounded Apify dataset is consumed; it must not imply durable `source_exhausted`. Google Maps remains cross-run `refreshable`, while same-run/provider completion stays separately recorded.