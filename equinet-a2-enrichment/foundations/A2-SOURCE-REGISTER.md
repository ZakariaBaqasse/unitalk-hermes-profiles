# Equinet A2 Source Register

**Version:** `0.1.1-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — RUNTIME ACTIVATION PENDING`  
**Decision timestamp:** `2026-08-26T17:58:25Z`  
**Profile:** `equinet-a2-enrichment`  
**Step:** `3C — A2 Source Register`

## 1. Operating sequence

A2 reuses the approved A1 handoff first. It checks the prospect's official website when one exists. New external access is limited to a named gap, conflict, verification requirement or freshness issue. A2 is not a second discovery crawl.

## 2. Source status matrix

| Source ID | Business approval | Rights preflight | Runtime readiness | Register status |
|---|---|---|---|---|
| `a1_approved_handoff` | approved | approved_internal_contract | manual_fixture_ready_durable_integration_pending | approved |
| `hubspot_authoritative_records` | approved_system_of_record | oauth_and_source_permissions_required | integration_pending | conditional |
| `equinet_authorized_first_party_data` | conditional_per_asset | asset_owner_permission_required | manual_intake_available | conditional |
| `prospect_official_website` | approved_by_equinet | per_domain_terms_and_robots_preflight | runtime_policy_pending | conditional |
| `equinet_representative_confirmation` | approved_for_recorded_review | authorised_reviewer_required | manual_available | approved |
| `official_professional_registry` | not_in_scope_except_a1_handoff_reuse | not_applicable_until_scope_changes | not_configured | not_selected |
| `a1_directory_evidence_reuse` | approved_for_reuse_only | inherits_original_evidence_scope | available_through_handoff | approved |
| `apify_harvestapi_linkedin_profile_search` | approved_by_equinet_for_a2_business_purpose | blocked_pending_linkedin_rights_and_harvestapi_vendor_review | account_connector_budget_and_build_pending | conditional |
| `apify_harvestapi_email_search` | approved_by_equinet_for_a2_business_purpose | blocked_pending_linkedin_rights_email_data_rights_and_harvestapi_vendor_review | account_connector_budget_and_build_pending | conditional |
| `search_engine_discovery` | approved_by_equinet_for_official_site_discovery | standard_search_terms_apply | tool_available_not_profile_activated | conditional |
| `commercial_enrichment_provider` | not_selected | provider_dpa_and_data_rights_pending | not_connected | integration_pending |
| `other_social_platform_automation` | not_approved | platform_permission_required | not_connected | blocked |

## 3. Official website profile

For each retained Farrier or Horse Owner candidate, check the official site when it exists. Use at most five pages: primary page, About/Team, Services, Contact/Location and one relevant dated page when available. Capture explicit outbound LinkedIn, Facebook, Instagram, YouTube and other clearly professional social-profile URLs shown on those pages. Attribute a URL to a person or organisation only when the page context supports it; otherwise hold it as ambiguous. Retaining a URL does not authorise opening, crawling or extracting the linked social profile. Allow at most one targeted retry per failed URL. Stop on terms/robots denial, login/paywall, CAPTCHA, 403, 429, unexpected personal data or scope/budget limit.

## 4. Apify LinkedIn Profile Search profile

- Actor: `harvestapi/linkedin-profile-search`.
- Equinet business approval: recorded.
- Confirmed trigger: only for a named role/contact gap after the official-site check.
- Preferred input: exact LinkedIn company URL explicitly published on the official website; fallback: verified company name plus target role.
- An individual LinkedIn profile URL is retained for human review or a separately approved profile-scraper action; it is not routed to the profile-search Actor.
- Starting retained fields: name, current title, current company, location and profile URL; review the bounded test output before expanding the allowlist.
- Independent email-search mode: approved for professional-email search, subject to the separate rights, vendor, budget, retention and runtime gates.
- Full history, education, skills, posts, counts, photos and personal interests: prohibited.
- Proposed technical cap: one page, five returned profiles and three retained contacts per candidate; concurrency one; no automatic query segmentation.
- Spend cap: pending.

The Actor remains `blocked_pending_linkedin_rights_and_harvestapi_vendor_review`. Equinet business approval does not by itself establish LinkedIn automated-use rights, approve HarvestAPI as a data processor or activate the runtime connector.

## 5. Paid-provider boundary

Apollo, Clay and other commercial enrichment providers remain unselected and unconnected. No live Equinet data or spend is authorised.

## 6. Information still required before activation

1. Provide the authorised Apify workspace/account, credential route and pinned Actor build.
2. Approve an Apify cost/event cap and consumption owner.
3. Provide approved LinkedIn automated-use rights, API route or documented legal/commercial exception.
4. Complete HarvestAPI privacy, security, retention, deletion and subprocessor review.
5. Confirm raw Actor dataset retention/deletion handling.
6. Confirm whether a personal email returned by the independent search must always be discarded; the Unitalk default is discard.
7. Review a bounded Actor sample output before expanding the minimum profile field allowlist.

## 7. Current conclusion

The source register can be reviewed as a draft. Runtime activation is not approved. No source call, provider call, CRM action or outreach action is authorised by this document.
