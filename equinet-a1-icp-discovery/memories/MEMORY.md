Twenty REST staging must JSON-quote exact filter values (commas parse as separators). Soft-deleted Companies with exact fingerprint/domain matches are held as possible_match — no automatic restore/update/recreate.
§
A1 post-n8n routing: every named lead stages a Company; non-empty `name` adds one linked Person after Company verification. Phone/email go to Person when expected, else Company. No-site/terminal enrichment failures stage unscored; website candidates are verified/enriched/scored first.
§
Equinet Twenty `sourceUrl` is acquisition provenance only: use the directory/source URL from the immutable n8n lead, label it with the normalized hostname, and never replace it with the verified official website. The official website belongs only in `domainName`.
§
Hermes default-profile gateway multiplexes named profiles; credential changes need a multiplexer restart.
§
Twenty Company live `email` field (EMAILS, nullable, max 10): stage as `{primaryEmail, additionalEmails: []}`, omit invalid/masked values.
§
A1 field contract: n8n `name`/`person_name` = explicitly identified person only. Organisation-only Google Maps records use `business_name` with empty person fields → Company only.
§
Equinet Google Maps cursor semantics: `dataset_exhausted` means one bounded Apify dataset is consumed; it must not imply durable `source_exhausted`. Google Maps remains cross-run `refreshable`, while same-run/provider completion stays separately recorded.
§
Equinet n8n MCP execute_workflow requires `workflowId` (not `id`) plus `executionMode:"production"`; the response returns only `executionId`/`status`, never the run ID.
§
Equinet poll_ticket.py init rejects an empty --application-run-id; when n8n is started without an explicit run_id, use a deterministic substitute such as exec-<execution-id>.
§
Facebook enrichment inside Equinet n8n needs no Facebook-specific runtime-policy change; source-specific controls belong in n8n source/evidence configuration.