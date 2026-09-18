# Step 8 Rood & Riddle — Behavioural Replay Instructions

**Profile:** `equinet-a2-enrichment`  
**Candidate:** `A1-RR-PODIATRY-001`  
**Purpose:** verify profile reasoning against the accepted deterministic Step 8 package  
**Mode:** read-only stored-page replay; no external access

## Read only

- `SOUL.md`
- `evaluations/step8/pilot/A1-RR-PODIATRY-001/STAGE1-INSTRUCTIONS.md`
- `evaluations/step8/handoffs/A1-RR-PODIATRY-001.handoff.json`
- `evaluations/step8/planning/A1-RR-PODIATRY-001.reuse-snapshot.json`
- `evaluations/step8/planning/A1-RR-PODIATRY-001.gap-plan.json`
- `evaluations/step8/collection/A1-RR-PODIATRY-001/page-01.md`
- `evaluations/step8/collection/A1-RR-PODIATRY-001/page-02.md`
- `evaluations/step8/collection/A1-RR-PODIATRY-001/page-03.md`
- `evaluations/step8/pilot/A1-RR-PODIATRY-001/canonical/revision-005-held.json`
- `evaluations/step8/pilot/A1-RR-PODIATRY-001/final-review-decision.json`

## Prohibited actions

- Do not call Web, Exa, Firecrawl, Apify, HubSpot, Twenty, n8n, email, messaging or any external service.
- Do not run or modify the canonical builder.
- Do not modify the accepted canonical record, decision, review package, contracts, skills, SOUL or configuration.
- Do not create or infer a named email, named phone, employment status, service area or purchasing authority.
- Do not treat `example@example.com` or form placeholders as contact data.
- Do not change the A1 score.

## Required output

Write exactly one JSON file:

`evaluations/step8/pilot/A1-RR-PODIATRY-001/behavioral-replay/result.json`

The JSON object must contain:

```json
{
  "record_type": "step8_rood_riddle_behavioral_replay",
  "candidate_id": "A1-RR-PODIATRY-001",
  "profile": "equinet-a2-enrichment",
  "model": "deepseek-v4-flash",
  "mode": "stored_page_read_only",
  "findings": {
    "person_role_title": "Co-Founder/Farrier",
    "person_professional_status": "not_found",
    "organisation_service_area": "not_found",
    "organisation_disciplines": ["all breeds and disciplines"],
    "person_business_email": "not_found",
    "person_business_phone": "not_found",
    "organisation_phone_available": true,
    "organisation_phone_is_named_contact_phone": false
  },
  "classifications": {
    "target_role_priority": "primary",
    "target_role_priority_is_sourced_fact": false,
    "purchasing_authority_established": false,
    "disciplines_scope": "organisation_level_not_podiatry_specific"
  },
  "minimum_package": {
    "status": "incomplete",
    "recommended_record_decision": "held"
  },
  "comparison_to_accepted_package": {
    "material_match": true,
    "differences": []
  },
  "boundaries": {
    "new_web_calls": 0,
    "external_actions": 0,
    "crm_writes": 0,
    "outreach_actions": 0,
    "a1_score_changed": false
  },
  "status": "pass"
}
```

If your evidence-based conclusion differs materially from the accepted package, set `material_match` and `status` to `false`/`failed`, list the differences, and do not change any accepted artifact.

Do not add keys. Do not include chain-of-thought. After writing the file, read it back and reply with only its path and `status`.
