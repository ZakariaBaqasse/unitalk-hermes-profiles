# Step 11 Website-First Runbook

All live actions require the Step 11 runtime gate. Until then, use `--fixture` paths only.

## Per-Company sequence

1. Build and validate the website preflight request.
2. Build `site-plan.json` from the Twenty Company and approved official URL.
3. Run `firecrawl_official_site_fetch.py`; never substitute free-form `web_extract` for prospect runtime.
4. Extract observations, build the LLM packet, produce decisions and validate them.
5. Build a Company merge plan from Company-attributed contacts and social links.
6. If Company email or phone remains missing and validated website evidence contains Facebook, run the one-call/no-retry Apify path.
7. Merge accepted Facebook Company candidates into the same composite plan.
8. Build website Person contact batch. People with both channels skip FullEnrich; People missing either channel request exactly work email and phone.
9. Continue existing linked-Person Lookup and staged Search only when unresolved contact/target gaps remain and the two-Person limit permits it.
10. Build the consolidated Twenty plan, dry-run, apply only under the run-specific write gate, and reconcile read-back.

## Commands

```bash
python scripts/preflight_step11_source_action.py website-preflight.json --output preflight.json
python scripts/build_official_site_plan.py website-request.json --output site-plan.json
python scripts/firecrawl_official_site_fetch.py site-plan.json --output site-fetch.json
python scripts/extract_official_site_observations.py site-fetch.json --output site-observations.json
python scripts/build_website_decision_packet.py site-observations.json --output website-packet-preliminary.json
# Agent writes person-proposals.json after reviewing every bounded person_evidence_block.
python scripts/validate_website_person_observation_proposals.py website-packet-preliminary.json person-proposals.json --output website-packet.json
python scripts/validate_website_decisions.py website-packet.json website-decisions.json --output website-validation.json
python scripts/build_company_contact_merge_plan.py company-merge-request.json --output company-merge-plan.json
python scripts/build_website_people_contact_batch.py website-packet.json website-validation.json --run-id <RUN_ID> --output website-selected-people.json
python scripts/fullenrich_contact_enrichment.py website-selected-people.json --output website-contact-results.json
```

Conditional Facebook path:

```bash
python scripts/build_apify_facebook_requests.py facebook-input.json --output apify-requests.json
python scripts/apify_facebook_page_contact.py apify-requests.json --output apify-raw-results.json
python scripts/validate_apify_facebook_results.py apify-raw-results.json --output apify-results.json
```

## Hard controls

- five website pages maximum;
- same-domain pages only;
- Firecrawl key in environment only;
- Firecrawl Markdown/HTML/links with `onlyMainContent=false`;
- no agent `web_extract` for prospects;
- one official-Facebook Actor run per Company and no retry;
- Company contacts never populate Person fields;
- two retained People maximum;
- final Company status last;
- every live write requires read-back.
