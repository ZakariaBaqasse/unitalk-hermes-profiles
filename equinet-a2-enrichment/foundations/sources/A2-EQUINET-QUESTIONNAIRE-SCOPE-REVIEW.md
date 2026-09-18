# A2 Equinet Questionnaire Scope Review

> **Historical questionnaire-design artifact.** The active SOC-1 through SOC-8 clarification now permits URL-only capture of explicit professional social links from an approved official website and separates person from organisation URLs. Broad social signals and automated social-profile extraction remain disabled.

**Version:** `1.0.1`  
**Status:** `UNITALK RECOMMENDATION`  
**Conclusion:** Do not send the original 28-row technical working matrix to Equinet as-is. Use the slim client decision template instead.

## 1. Main conclusion

The original template contains useful delivery questions, but several rows are:

- internal Unitalk design decisions;
- already answerable from the HubSpot metadata;
- safe defaults that Unitalk can propose for approval;
- later integration or go-live decisions;
- optional fields that should not be presented as required.

The most important missing Equinet decision is the **target job-role model by segment**:

- which Farrier roles A2 should identify;
- which Horse Owner organisation roles A2 should identify;
- their priority order;
- functional equivalents;
- roles to exclude;
- what A2 should do when no target role is found.

This decision determines who A2 researches, which profiles are relevant and when a record is complete enough for review.

## 2. Questions to keep as direct Equinet decisions

| Decision | Why Equinet must decide |
|---|---|
| Target Farrier roles and priority | Core business targeting decision |
| Target Horse Owner roles and priority | Core business targeting decision |
| Maximum named contacts and fallback | Controls scope, privacy and review volume |
| Minimum contactability | Determines review readiness |
| Personal email/mobile policy | Privacy and risk decision |
| Required versus optional Farrier fields | Business value and cost decision |
| Required versus optional Horse Owner fields | Business value and cost decision |
| Manual LinkedIn/social policy | Source and privacy boundary |
| A2 reviewer and backup | Approval accountability |
| Paid-provider types, budget and approver | Commercial and data-route decision |
| Owner/territory assignment | Go-live business rule |

The first four targeting/contact decisions plus the separate horse-count range correction are needed before finalising the business field catalogue. The others can be collected before pilot, paid testing or go-live as labelled.

## 3. Original rows to merge

### Contact fields

Merge:

- professional email;
- business phone;
- mobile phone;
- secondary email.

Use two client decisions:

1. minimum contactability;
2. personal/mobile data policy.

Unitalk can default secondary email to optional and no-credit lookup.

### Role fields

Merge:

- current role title;
- Buying Role.

Ask Equinet for target business roles and priority by segment. Unitalk then maps:

- source job title;
- normalised target role;
- optional Buying Role recommendation;
- human review requirement.

Equinet should not be asked to design the HubSpot mapping.

### Horse Owner fields

Merge:

- exact horse count;
- horse-count range;
- discipline;
- stable type;
- breeds.

Ask Equinet to classify the fields as Required, Optional or Do Not Collect. Keep the range overlap as a separate, explicit data-quality decision row. For the pilot, Unitalk recommends an A2-only derived review band while leaving the existing HubSpot field unchanged. A later impact review may propose correcting the options of the existing HubSpot field; no new HubSpot field is proposed by default.

### Farrier fields

Merge:

- professional status;
- certifications;
- discipline;
- service area;
- horses served per month;
- client-base summary.

Use one prioritisation row with Unitalk defaults.

### Social fields

Merge:

- public profile URLs;
- social signals;
- mutual connections.

Recommend storing role-relevant public URLs, permitting human manual LinkedIn role verification and keeping social signals/mutual connections disabled until separately approved.

## 4. Original rows Unitalk can decide or propose

Do not ask Equinet to design these from scratch:

| Original topic | Unitalk action |
|---|---|
| Authoritative organisation name | Map verified Company association as authoritative; preserve Contact baseline |
| Company-domain duplicate logic | Use domain as one signal, not a unique key |
| Location structure | Propose country/state minimum and preserve missing fields as gaps |
| Secondary email | Default optional; no paid lookup |
| Evidence for Contact Verified | Unitalk proposes deterministic evidence rules for approval |
| Record Data Quality states | Unitalk proposes definitions for Complete, Partial and Needs Review |
| Outreach eligibility property/list combination | Unitalk maps the confirmed HubSpot fields and lists; Equinet reviews the business effect |
| Technical source access and API method | Unitalk proposes after rights review |
| Confidence, freshness and conflict calculation | Unitalk designs; Equinet approves the business consequence |

## 5. Items to move outside the field questionnaire

- A2 reviewer and backup → approval matrix, referenced from the slim template;
- owner/territory rules → go-live ownership configuration;
- paid provider and budget → integration/provider approval register;
- outreach eligibility → shared consent and CRM-controls foundation;
- source access rights → A2 Source Register;
- detailed HubSpot mapping → Unitalk implementation artifact.

They remain required, but should not make the initial role/field workshop unnecessarily long.

## 6. Recommended client interaction

Use a short guided review rather than asking Equinet to complete a 28-row spreadsheet alone.

Suggested sequence:

1. confirm target job roles by segment;
2. confirm maximum contacts and fallback;
3. confirm minimum contactability;
4. approve or correct the proposed Required/Optional field defaults;
5. collect privacy, reviewer and budget decisions before the applicable pilot gate.

## 7. Delivery artifact

Use:

`A2-EQUINET-CLIENT-DECISION-TEMPLATE-SLIM.csv`

Keep the original 28-row template as an internal Unitalk working matrix for detailed design and traceability.
