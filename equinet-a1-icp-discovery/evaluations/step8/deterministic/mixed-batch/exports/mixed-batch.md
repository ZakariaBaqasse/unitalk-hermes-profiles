# Equinet A1 Prospect Review — A1-RP-STEP8-MIXED

**Generated:** `2026-08-15T17:46:29Z`  
**Candidates:** `3` — Accept `1`, Needs Research `1`, Reject `1`  
**Integrations:** HubSpot unavailable; Twenty unavailable; A2 not triggered.  
**Human decision:** Pending for every candidate.

## Review queue

| Rank | Candidate | Segment | ICP | Confidence | Recommendation | Human decision |
|---:|---|---|---|---|---|---|
| 1 | Alex Morgan / Bluegrass Performance Farriery | farrier | 86 / high | 84 / high | Accept | Pending |
| 2 | Synthetic Horse Farm / Jane Doe | horse_owner | 80 / medium | 92 / high | Needs Research | Pending |
| 3 | Synthetic Unverified Farrier | farrier | Blocked | 90 / high | Reject | Pending |

## 1. Alex Morgan / Bluegrass Performance Farriery

- **Candidate ID:** `A1-SYN-FARRIER-HIGH`
- **Type:** `farrier` / `farrier_independent`
- **Location:** Lexington, Kentucky
- **Full address:** 100 Synthetic Lane, Lexington, KY 40502
- **Primary named contact:** Alex Morgan
- **Primary contact role:** Farrier
- **Recommendation:** `Accept` — Accept recommendation for human review: final band high with high evidence confidence and no unresolved review gate.
- **Scoring outcome:** `high_priority_farrier`
- **ICP:** `86` / `high`
- **Confidence:** `84` / `high`
- **Batch duplicate:** `no_match`
- **HubSpot/Twenty:** `unavailable` / `unavailable`
- **A2:** `not authorised`

### Confirmed criteria

- `farrier.professional_activity`
- `farrier.product_usage_or_influence`
- `farrier.regular_business_activity`
- `farrier.high_value_service_area`
- `farrier.advanced_specialisation`
- `farrier.certified_or_experienced`
- `farrier.sport_horse_focus`
- `farrier.buying_influence`
- `farrier.product_fit`
- `farrier.engagement_signal`

### Limitations

- Synthetic candidate created only for Step 8 validation.
- Exact client-base size is not published.

### Sources

- https://bluegrass-farriery.example.test
- https://bluegrass-farriery.example.test/services
- https://bluegrass-farriery.example.test/service-area
- https://bluegrass-farriery.example.test/contact

### Public contacts

- **Synthetic business email**: alex.morgan@example.com
- **Synthetic business phone**: +1-555-010-8000

### Evidence

- **EV-SYN-PRO-001 — Synthetic Farrier Homepage**: Bluegrass Performance Farriery provides active professional hoof-care appointments throughout Lexington. (https://bluegrass-farriery.example.test)
- **EV-SYN-SERVICE-001 — Synthetic Farrier Services**: Services include performance shoeing, therapeutic applications and selection of professional horseshoes and hoof-care products. (https://bluegrass-farriery.example.test/services)
- **EV-SYN-AREA-001 — Synthetic Service Area**: The practice serves sport and competition horses in Lexington and the surrounding Kentucky equine community. (https://bluegrass-farriery.example.test/service-area)
- **EV-SYN-ROLE-001 — Synthetic Farrier Contact**: Alex Morgan, Farrier and owner, selects products for the practice. alex.morgan@example.com | +1-555-010-8000. (https://bluegrass-farriery.example.test/contact)

## 2. Synthetic Horse Farm / Jane Doe

- **Candidate ID:** `A1-OWNER-UNKNOWN-001`
- **Type:** `horse_owner` / `farm`
- **Location:** Lexington, KY
- **Full address:** Not published
- **Primary named contact:** Jane Doe
- **Primary contact role:** Farm Manager
- **Recommendation:** `Needs Research` — Needs Research recommendation: deterministic outcome `horse_count_unknown_human_review` or evidence/duplicate limitations require human follow-up.
- **Scoring outcome:** `horse_count_unknown_human_review`
- **ICP:** `80` / `medium`
- **Confidence:** `92` / `high`
- **Batch duplicate:** `no_match`
- **HubSpot/Twenty:** `unavailable` / `unavailable`
- **A2:** `not authorised`

### Confirmed criteria

- `horse_owner.commercial_operation`
- `horse_owner.purchasing_influence`
- `horse_owner.product_fit`
- `horse_owner.performance_discipline`
- `horse_owner.breeding_activity`
- `horse_owner.professional_network`
- `horse_owner.high_equine_activity_location`
- `horse_owner.buying_signal`

### Limitations

- Horse count remains unknown.
- Horse count is not published.

### Sources

- https://synthetic-horse-farm.example.test/about
- https://synthetic-horse-farm.example.test/team
- https://synthetic-horse-farm.example.test/services
- https://synthetic-horse-farm.example.test/competition
- https://synthetic-horse-farm.example.test/breeding
- https://synthetic-horse-farm.example.test/contact
- https://synthetic-horse-farm.example.test/news

### Public contacts

- No public contact published.

### Evidence

- **EV-OWNER-001 — Synthetic Horse Farm**: Professional equine farm operation serving the Lexington area (https://synthetic-horse-farm.example.test/about)
- **EV-OWNER-002 — Synthetic Horse Farm**: Jane Doe listed as Farm Manager with purchasing responsibilities (https://synthetic-horse-farm.example.test/team)
- **EV-OWNER-003 — Synthetic Horse Farm**: Operation manages multiple horses with professional hoof-care program (https://synthetic-horse-farm.example.test/services)
- **EV-OWNER-004 — Synthetic Horse Farm**: Actively competes in show jumping at regional level (https://synthetic-horse-farm.example.test/competition)
- **EV-OWNER-005 — Synthetic Horse Farm**: Active breeding program with multiple mares (https://synthetic-horse-farm.example.test/breeding)
- **EV-OWNER-006 — Synthetic Horse Farm**: Engages professional trainers, farriers and veterinary support (https://synthetic-horse-farm.example.test/team)
- **EV-OWNER-007 — Synthetic Horse Farm**: Farm located in Lexington, Kentucky — central equine industry hub (https://synthetic-horse-farm.example.test/contact)
- **EV-OWNER-008 — Synthetic Horse Farm**: Recent stable expansion and acquisition of new performance horses (https://synthetic-horse-farm.example.test/news)

## 3. Synthetic Unverified Farrier

- **Candidate ID:** `A1-FARRIER-REJECT-001`
- **Type:** `farrier` / `farrier_independent`
- **Location:** Lexington, KY
- **Full address:** Not published
- **Primary named contact:** Synthetic Unverified Farrier
- **Primary contact role:** Farrier
- **Recommendation:** `Reject` — Reject recommendation: Confirmed exclusion criterion: farrier.no_professional_evidence. Human review is still required before recording a final rejection.
- **Scoring outcome:** `excluded_no_professional_evidence`
- **ICP:** `None` / `None`
- **Confidence:** `90` / `high`
- **Batch duplicate:** `no_match`
- **HubSpot/Twenty:** `unavailable` / `unavailable`
- **A2:** `not authorised`

### Confirmed criteria

- `farrier.no_professional_evidence`

### Limitations

- Synthetic exclusion test candidate.
- No professional hoof-care activity is evidenced.

### Sources

- https://synthetic-unverified-farrier.example.test

### Public contacts

- No public contact published.

### Evidence

- **EV-NO-PRO-001 — Synthetic identity-only page**: A name and location are present, but no professional hoof-care activity is stated. (https://synthetic-unverified-farrier.example.test)
