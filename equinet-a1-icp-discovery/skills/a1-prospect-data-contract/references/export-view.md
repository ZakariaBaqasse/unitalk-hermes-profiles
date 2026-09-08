# Prospect Candidate V1 — Human-Review Export View

**Contract version:** `1.1.0`  
**Status:** Approved by Unitalk for A1 pilot configuration

## Principle

The canonical, lossless record is the JSON object validated by `prospect-candidate.schema.json`. Markdown, CSV and Excel are human-review views derived from that JSON. They must never become a second, competing data model.

## Required review columns

| Column | Canonical source |
|---|---|
| `candidate_id` | `candidate_id` |
| `run_id` | `run_id` |
| `discovered_at` | `discovered_at` |
| `segment` | `segment` |
| `prospect_type` | `prospect_type` |
| `display_name` | `identity.display_name` |
| `person_name` | `identity.person.full_name` |
| `role_title` | `identity.person.role_title` |
| `organisation_name` | `identity.organisation.name` |
| `website` | `identity.organisation.website` |
| `domain` | `identity.organisation.domain` |
| `country_code` | `location.country_code` |
| `state_region` | `location.state_region` |
| `city` | `location.city` |
| `postal_code` | `location.postal_code` |
| `full_address` | `location.public_address` |
| `geography_status` | `location.geography_status` |
| `public_emails` | Filter `public_contacts` where `contact_type=email` |
| `public_phones` | Filter `public_contacts` where `contact_type=phone` |
| `public_profiles` | Other values from `public_contacts` |
| `public_contact_details` | JSON array of contact type, value, label and evidence IDs from `public_contacts` |
| `icp_score` | `scoring.score` |
| `score_band` | `scoring.band` |
| `score_model_version` | `scoring.model_version` |
| `score_rationale` | `scoring.rationale` |
| `confirmed_criteria` | Confirmed items from `qualification.criteria` |
| `confidence_level` | `confidence.level` |
| `confidence_score` | `confidence.score` |
| `confidence_limitations` | `confidence.limitations` |
| `minimum_data_status` | `qualification.minimum_data_status` |
| `missing_minimum_fields` | `qualification.missing_minimum_fields` |
| `exclusion_status` | `qualification.exclusion_status` |
| `batch_duplicate_status` | `duplicate_check.batch.status` |
| `twenty_duplicate_status` | `duplicate_check.twenty.status` |
| `hubspot_duplicate_status` | `duplicate_check.hubspot.status` |
| `source_urls` | URLs from `source_evidence` |
| `evidence_summary` | Source name + excerpt + supported claims |
| `next_action` | `recommendation.next_action` |
| `priority_rank` | `recommendation.priority_rank` |
| `suggested_territory` | `recommendation.suggested_territory` |
| `workflow_stage` | `workflow.stage` |
| `review_decision` | `workflow.review_decision` |
| `twenty_company_id` | `system_references.twenty_company_id` |
| `twenty_person_id` | `system_references.twenty_person_id` |
| `twenty_person_relation_status` | `system_references.twenty_person_relation_status` |
| `schema_version` | `schema_version` |

## Serialisation rules

- CSV encoding: UTF-8 with a header row.
- Excel: one `Prospects` worksheet and, when useful, separate `Evidence` and `Score Components` worksheets keyed by `candidate_id`.
- Markdown: one compact row per candidate; put long evidence and rationale below the table or in linked detail sections.
- Lists in a single CSV cell use JSON-array syntax, not an ambiguous comma-separated string.
- Null values are empty in human-review tables but remain explicit `null` in canonical JSON.
- Dates use ISO 8601 UTC.
- Do not truncate URLs, evidence excerpts or rationales in the canonical JSON.
- Every exported row must be traceable back to `candidate_id`, `run_id` and `schema_version`.

## Integration rule

Twenty, A2 and HubSpot mappings will be generated from the canonical JSON fields. They must not read inferred values from the visual Markdown or spreadsheet formatting.
