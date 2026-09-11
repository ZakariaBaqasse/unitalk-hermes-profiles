# No-site leads

No separate enrichment payload is required before Twenty staging.

For a named lead from `a1.discovery-result.v1`:

- omit `domainName` when no verified official website is available;
- create the Company with `discoveryStatus: DISCOVERED`;
- preserve the unchanged discovery fingerprint;
- leave score and confidence unavailable rather than inventing values;
- place it in the same Company review workflow as every other lead.

A missing website never blocks staging. A missing usable Company name (`business_name or name`) produces `blocked_missing_company_name`. When `name` is present, one linked Person is staged after the Company; no Opportunity, Task, campaign, message, A2 or outreach action is permitted.
