# Equinet A1 — ICP Scoring Model V1

**Version:** `1.0.0`  
**Status:** Approved by Séverine for Unitalk A1 V1  
**Applies to:** `equinet-a1-icp-discovery`

## Purpose

The ICP score measures how closely a documented candidate matches Equinet's commercial target. It is separate from confidence:

```text
ICP score = commercial fit
Confidence score = reliability of the evidence
```

A candidate may have a high ICP score and low confidence when the available information is attractive but insufficiently proven.

## Common scoring rules

- Only confirmed criteria with traceable evidence receive points.
- Confirmed criteria receive the full configured weight; V1 does not use partial points.
- Unknown, not-confirmed or contradicted criteria receive zero points.
- Missing data does not create a penalty beyond the points not earned.
- The numeric score equals the sum of awarded criterion components.
- Special pathways cap the final band and business outcome, not the numeric score.
- Confirmed exclusions override every score.
- All V1 candidates remain human-reviewed.
- Related criteria do not double-count a generic fact: Farrier product usage and explicit buying influence both score only when the evidence establishes distinct usage and decision-influence facts.

## Bands

| Band | Score | Meaning |
|---|---:|---|
| High | 75–100 | High-priority ICP candidate |
| Medium | 50–74 | Qualified candidate |
| Low | 25–49 | Lower-priority or evidence-limited pathway |
| Unqualified | 0–24 | Does not currently meet the ICP threshold |

The proposed qualification threshold is `50`.

## Farrier model

| Criterion | Points |
|---|---:|
| Active professional Farrier activity | 20 |
| Professional product usage or influence | 15 |
| Product fit | 10 |
| Established or broad client base | 10 |
| Regular business activity | 10 |
| Advanced specialisation | 8 |
| High-value service area | 5 |
| Certified or experienced | 5 |
| Sport or competition-horse focus | 5 |
| Buying influence | 5 |
| Multi-Farrier business | 4 |
| Recent professional engagement | 3 |
| **Total** | **100** |

### Farrier gates and pathways

- `professional_activity` is required for standard qualification.
- If professional activity is unknown, the numeric score remains visible but the band is capped at Low and the candidate requires review.
- An active apprentice is future potential, capped at Low and always human-reviewed.
- An inactive or hobby-only candidate is capped at Unqualified.
- Confirmed `no_professional_evidence` blocks scoring and excludes the candidate.

## Horse Owner model

| Criterion | Points |
|---|---:|
| Professional or commercial operation | 25 |
| More than three horses | 20 |
| Purchasing influence | 15 |
| Product fit | 10 |
| Performance or competition discipline | 8 |
| Breeding activity | 7 |
| Professional equine network | 5 |
| High-equine-activity location | 5 |
| Recent buying or expansion signal | 5 |
| **Total** | **100** |

### Horse Owner gates and pathways

- `commercial_operation` and `more_than_three_horses` are required for standard qualification.
- If commercial orientation is unknown, the band is capped at Unqualified and human review is required.
- If horse count is unknown but at least two strong commercial signals are confirmed, the band is capped at Medium and the candidate goes to human review.
- If horse count is at or below three but at least two strong commercial signals are confirmed, the band is capped at Low and the candidate follows the approved exception review pathway.
- Without two strong commercial signals, missing or below-threshold horse count is capped at Unqualified.
- A confirmed single-horse recreational owner is capped at Unqualified.
- Confirmed `no_commercial_evidence` blocks scoring and excludes the candidate.

Strong commercial signals for the horse-count exception are:

- purchasing influence;
- product fit;
- performance discipline;
- breeding activity;
- professional network;
- recent buying or expansion signal.

## Score versus band cap

Example:

```text
Raw numeric score: 78
Horse count: unknown
Strong commercial signals: 3

Numeric score: 78
Raw band: High
Final band: Medium
Outcome: horse_count_unknown_human_review
```

This preserves the points actually earned while preventing automatic high-priority treatment when a required gate is unresolved.

## Exclusions and CRM status

Confirmed global or segment exclusions block the candidate regardless of score. HubSpot status does not change the ICP score itself:

- confirmed duplicate/customer/opportunity/partner/distributor/opt-out → workflow block;
- HubSpot unavailable → show `unavailable`, with no score penalty;
- previously lost opportunity → review, with no score change.

## Confidence interaction

Confidence never changes the numeric ICP score. Both values are shown together. A high ICP score with low confidence must not be presented as a validated high-priority prospect.

## Approval status

Séverine approved the Farrier and Horse Owner weights, score bands, qualification threshold, two-signal Horse Owner exception, horse-count band caps, apprentice/inactive pathways and full-weight confirmed-criterion rule. The model is approved for production under the versioned runtime and ICP scope. Production acceptance remains distinct from contractual acceptance.
