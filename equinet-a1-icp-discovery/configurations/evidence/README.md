# Equinet A1 — Evidence and Confidence Rules V1

**Version:** `1.0.0`  
**Status:** Approved by Séverine for Unitalk A1 V1  
**Applies to:** `equinet-a1-icp-discovery`  
**Candidate contract:** `1.0.0`  
**ICP configuration:** `1.0.0`  
**Source register:** `1.0.0`

## Purpose

These rules define what A1 may treat as evidence and how A1 measures confidence in the resulting candidate. Confidence measures evidence reliability, identity certainty, corroboration, freshness and completeness. It does not measure commercial attractiveness; that belongs to the separate ICP score.

## Evidence states

| State | Meaning | May confirm a mandatory criterion? |
|---|---|---:|
| Direct fact | Explicitly stated or visibly presented by the cited source | Yes |
| Reasonable inference | Plausible conclusion not directly stated | No |
| Contradictory evidence | Material source conflict | No — human review |
| Unknown | Available evidence does not establish the claim | No |

## Source hierarchy

1. Authoritative CRM or official governing-body record.
2. Official registry, certification or association directory.
3. Prospect's own public business website.
4. Dated event, competition or sale record.
5. Permitted sector directory used as a human seed.
6. Reputable editorial or trade source.
7. Permitted public professional social profile.
8. Search, Maps or directory seed used only for discovery.
9. Blocked or unverified source — unusable.

Two pages are not independent merely because they have different URLs. Pages from the same business domain, copied directory descriptions and syndicated versions of one release count as one source.

## Authority of the prospect's business website

The current official website of the Farrier, farm, stable or equine business is authoritative for facts that the business controls and explicitly publishes. No second source is required for:

- business identity and organisation name;
- public business location and service area;
- publicly displayed professional contact details;
- stated services and specialisations;
- current team roles and job titles;
- business type and explicit operation details;
- an explicitly stated horse count, team size or facility scale when current and unambiguous.

A second authoritative source is still required for external claims such as current certification or membership validity, third-party awards, official competition results and CRM status. Marketing superlatives or vague claims are not converted into quantitative facts.

## Important claim rules

### Identity

Require a name plus a distinguishing identifier such as domain, public business phone, public address, organisation association or official record. Identity cannot be inferred.

### Public professional contact

The exact email or phone must be visibly published for professional use and linked to the source page. A1 never guesses contact details.

### Professional activity

Require current services, a current professional listing or dated recent professional activity. An old certification alone does not prove that the person is currently active.

### Horse count

Require an explicit current number or reliable record. Never infer horse count from photos, acreage, stable size, follower count or event participation.

### Client-base size

Require an explicit statement or direct quantitative evidence. Review counts, followers, service area and years in business do not establish client-base size.

### Purchasing influence

A current decision-role title from a reliable source may be sufficient to establish likely purchasing influence. Strong examples include Owner, Founder, CEO, General Manager, Farm Manager, Stable Manager, Barn Manager, Purchasing Manager, Head Trainer, Owner/Operator and Farrier Business Owner.

Titles such as Trainer, Professional Rider, Facility Manager or Professional Farrier indicate possible influence. Apprentice, Assistant, Groom, Rider, Student, Volunteer or Office Assistant are insufficient alone.

A1 must say `likely purchasing influence based on the current role`; it must not claim proven budget authority unless the source explicitly states it. Social following or association membership alone remains insufficient.

### CRM status and exclusions

Only a live authoritative CRM or approved exclusion source may establish customer, opportunity, partner, distributor, opt-out or duplicate status. Until HubSpot is connected, the correct value is `unavailable`.

## Freshness treatment

A current official business website does not need a visible publication date for facts that the business explicitly publishes and controls. When the page is available and there is no stale or contradictory signal, A1 treats those facts as current.

The same treatment applies to an official registry or association record that presents an active or current status.

| Source situation | Treatment |
|---|---|
| Current official business website with explicit self-controlled fact | Current; no visible date required |
| Current official registry or association record | Current; no visible date required |
| Dated external source | Apply the relevant freshness window below |
| Undated external source | Secondary or historical context only for time-sensitive claims |
| Closed website, broken contact, archived content, retirement signal or conflicting current details | Needs review or lower confidence |

Freshness windows apply to dated external sources:

| Claim | Maximum age |
|---|---:|
| Public professional contact detail | 180 days |
| Location and business operation | 365 days |
| Current professional activity | 365 days |
| Certification or membership | 365 days, unless the official source confirms current validity |
| Horse count | 365 days |
| Client-base size | 365 days |
| Purchasing influence | 365 days |
| Recent activity | 365 days |
| Specialisation or discipline | 730 days |
| CRM status or exclusions | Live at the time of the run |

Older evidence may remain historical context, but it does not automatically establish a current claim.

## Future Google Business Profile integration

Google Maps remains discovery-only in A1 V1. A Google Business Profile may become a primary source only after an approved official Google Business Profile or GoogleLocations API integration can confirm owner-management, verification status or another approved equivalent signal.

If activated, it may support business-controlled facts such as business name, address, public phone, website, opening hours, category and explicitly displayed services. It will not alone establish horse count, client-base size, certification, CRM status or purchasing influence beyond an explicit approved role.

## Confidence score

The deterministic method uses six dimensions:

| Dimension | Maximum points |
|---|---:|
| Identity certainty | 20 |
| Source quality | 20 |
| Evidence directness | 20 |
| Corroboration | 20 |
| Freshness | 10 |
| Completeness | 10 |
| **Total** | **100** |

## Confidence bands

| Level | Score |
|---|---:|
| High | 80–100 |
| Medium | 60–79 |
| Low | 0–59 |

## Safety caps

A high raw total does not override evidence limitations.

| Condition | Maximum final score |
|---|---:|
| Mandatory claim supported only by inference | 59 |
| Unresolved identity conflict | 39 |
| Critical evidence conflict | 39 |
| Minimum evidence package for confidence assessment is incomplete | 39 |

A blocked source, missing evidence, or fabricated/untraceable evidence invalidates the assessment rather than merely lowering its score.

For Wave 2, the minimum evidence package includes identity, segment, permitted evidence, qualification criteria, exclusion status and visible conflicts/unknowns. It does not yet require scoring, recommendation, workflow, export or unavailable HubSpot/Twenty fields; those are produced later and must not artificially cap confidence.

## Examples

### High confidence

High confidence may be produced by:

- one current official business website that directly establishes the identity and all material self-controlled facts; or
- two independent permitted sources where external or ambiguous claims require corroboration.

The candidate must also have current information, no material conflict and a complete review package.

### Medium confidence

Typical Medium cases include:

- one permitted secondary source;
- a primary source with important noncritical gaps;
- mixed direct and inferred evidence;
- information that is partly stale but still usable.

A strong official business website is not automatically capped at Medium merely because it is the only source.

### Low confidence

- weak name/location match;
- key claims inferred rather than stated;
- stale or incomplete evidence;
- unresolved conflict or missing minimum data.

## Relationship with ICP score

```text
High ICP + High confidence
→ attractive candidate with strong evidence

High ICP + Low confidence
→ potentially attractive but insufficiently proven

Low ICP + High confidence
→ well-documented candidate that does not fit the target
```

Confidence never authorises outreach, CRM writes, sequence enrolment or removal of human review.

## Confirmed by Séverine

- A current official business website may stand alone for facts the business controls and explicitly publishes.
- A current decision-role title from a reliable source may establish likely purchasing influence.
- A single strong source is not automatically capped at Medium; the corroboration dimension already reflects the absence of a second source.
- A1 performs targeted research rather than checking every available source.

## Approval status

Séverine approved the V1 dimensions, confidence bands, safety caps, official-business-website authority, role-based purchasing influence, targeted corroboration, freshness treatment and the future Google Business Profile boundary. The evidence rules are approved for production under the versioned runtime and ICP scope. Production acceptance remains distinct from contractual acceptance.
