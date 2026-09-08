# Equinet A1 — ICP Scoring Model Summary

**Status:** Approved for production — subject to later Equinet review and calibration  
**Applies to:** A1 ICP Discovery  
**Related policies:** ICP Configuration 2.0.0, Evidence and Confidence Rules 1.2.0, Approved Source Register 2.0.0

## Purpose

The ICP score measures how closely a documented Farrier or professional/commercial Horse Owner matches Equinet's commercial target. It does not measure evidence reliability; confidence is calculated and displayed separately.

## Common rules

- Only confirmed criteria with traceable evidence receive points.
- Confirmed criteria receive their full configured weight in V1.
- Unknown, not-confirmed or contradicted criteria receive zero points.
- Missing information is never guessed.
- The numeric score is the sum of awarded criterion points.
- Special pathways may limit the final band and review outcome without altering the numeric points earned.
- Confirmed exclusions override every score.
- Every A1 V1 candidate remains subject to human review.
- Related criteria do not double-count a generic fact. Farrier professional product usage and explicit buying influence both receive points only when the evidence establishes distinct usage and decision-influence facts.

## Score bands

| Band | Score | Meaning |
|---|---:|---|
| High | 75–100 | High-priority ICP candidate |
| Medium | 50–74 | Qualified candidate |
| Low | 25–49 | Lower-priority or evidence-limited pathway |
| Unqualified | 0–24 | Does not currently meet the qualification threshold |

The proposed qualification threshold is `50`.

## Farrier weights

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

### Farrier pathways

- Professional activity is required for standard qualification.
- Unknown professional activity limits the final band to Low and requires review.
- Active apprentices are future potential, limited to Low and always human-reviewed.
- Inactive or hobby-only candidates are limited to Unqualified.
- Confirmed absence of professional activity excludes the candidate.

## Horse Owner weights

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

### Horse Owner pathways

- Commercial operation and more than three horses are required for standard qualification.
- Unknown commercial orientation limits the candidate to Unqualified and requires review.
- Unknown horse count plus at least two strong commercial signals limits the final band to Medium and requires human review.
- Horse count at or below three plus at least two strong commercial signals follows the exception pathway, limited to Low and requiring human review.
- Missing/below-threshold horse count without two strong signals is Unqualified.
- A confirmed single-horse recreational profile is Unqualified.
- Confirmed absence of commercial orientation excludes the candidate.

Strong commercial signals are purchasing influence, product fit, performance discipline, breeding activity, professional network, or recent buying/expansion activity.

## Score and confidence are displayed together

```text
ICP score: commercial fit
Confidence score: reliability of evidence
```

A high ICP score with low confidence is not presented as a validated priority prospect. Confidence does not change the numeric ICP score; it changes how safely the result can be interpreted.

## Human review and integrations

The score never authorises outreach, CRM creation, HubSpot updates, A2 handoff or automatic approval. CRM exclusions and previously lost opportunities are handled by the review workflow rather than by changing the commercial-fit score.

## Production calibration

The weights and thresholds remain versioned operating values. During production review, Equinet and Unitalk may compare accepted and rejected candidates, false positives, missing prospects and segment conversion. Any approved adjustment will be documented, tested and published as a new version rather than applied silently.
