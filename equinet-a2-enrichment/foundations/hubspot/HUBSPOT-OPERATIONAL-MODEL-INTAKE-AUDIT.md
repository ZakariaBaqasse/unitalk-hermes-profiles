# Equinet HubSpot Operational Metadata Intake Audit for A2 Enrichment

**Audit version:** `0.1.0`  
**Recorded at:** `2026-08-25T09:51:49Z`  
**Status:** `OPERATIONAL METADATA SNAPSHOT RECEIVED — NO LIVE HUBSPOT CONNECTION`  
**Profile:** `equinet-a2-enrichment`

## 1. Executive conclusion

The three additional files materially improve A2 design readiness. Unitalk now has a documented snapshot of:

- Contact and Company lifecycle stages;
- the Deal pipeline;
- custom-object pipelines and approval states;
- lead, account and ticket statuses;
- active/inactive HubSpot users, teams, owner model and territories;
- selected Sales and Marketing workflows, lists and review-related assets.

This information enables more precise Step 2B states and a safer draft A2-to-HubSpot mapping. It also reveals important blockers and side-effect risks that were not visible from the property export alone.

The files do not create a HubSpot connection. They do not verify live record values, OAuth scopes, per-user permissions or complete workflow trigger/action definitions.

## 2. Inputs and integrity

| Input | Source statement | SHA-256 |
|---|---|---|
| HubSpot Status Model Overview | Generated August 18, 2026 from live HubSpot portal data | `fa96082eeb69fca75caa3b5ec61723d572e5e8513377802498b109120df754b3` |
| HubSpot Users, Teams & Ownership Model | Generated August 18, 2026 from live HubSpot portal data, account 145840940 | `401f48738283c8e1e0ac013be025575893fbf6bc236b3c7c74352fabfbbdacb2` |
| Sales and Marketing Process Inventory | 68 inventory rows | `8212df536e1a5560861b70882fd3031c89758b41b635cf5b97ee802724536bdb` |

## 3. Confirmed status models

### Contact and Company lifecycle

The shared `lifecyclestage` model has seven ordered values:

```text
Subscriber
→ Lead
→ Marketing Qualified Lead
→ Sales Qualified Lead
→ Opportunity
→ Customer
→ Evangelist
```

A2 can now reference these exact external values. It must not change lifecycle stage during the no-integration pilot or infer that enrichment approval authorises a lifecycle change.

### Deal pipeline

One Deal pipeline is documented:

```text
Sales Pipeline [default]
Appointment Scheduled
→ Qualified To Buy
→ Presentation Scheduled
→ Decision Maker Bought-In
→ Contract Sent
→ Closed Won | Closed Lost
```

This enables a draft authoritative Deal-status gate for A2. Live Deal associations and stages remain unavailable without a connection.

### Lead Status

The shared Contact/Company `hs_lead_status` values are:

```text
NEW
OPEN
IN_PROGRESS
OPEN_DEAL
UNQUALIFIED
ATTEMPTED_TO_CONTACT
CONNECTED
BAD_TIMING
```

Lead Status is separate from Lifecycle Stage and must remain a separate baseline field in the canonical mapping.

### Company Account Status

`account_status` contains:

```text
Active
Block
Ship
```

The business meaning of `Block` and `Ship` is not sufficiently documented. A2 must treat these values as authoritative external states but must not derive eligibility logic until Equinet confirms their meaning.

### Custom objects

- Complaints has no pipeline; records use `complaint_type` classification.
- Sample Requests has an eight-stage pipeline and a separate four-value approval status.
- The existing Sample Request approval workflow is specific to Sample Requests and cannot be treated as an A2 enrichment-review workflow.

### Ticket pipeline

The Support Pipeline has:

```text
New
Rename 1
Waiting on us
Closed
```

`Rename 1` appears to be an unfinished placeholder and must not be used as a durable business label until Equinet confirms its intended meaning.

## 4. Users, teams and ownership

The account snapshot contains:

- 21 active users;
- 9 inactive users retained in historical records;
- 6 members in `EQUINET Team`;
- 12 members in `Mustad USA Sales Team`;
- three placeholder/queue owners: `Mustad HubSpot`, `Sample Request Mustad USA` and `Cetrix Support`;
- available seat types: Core, Sales Pro, Partner and Developer.

This HubSpot user list is not proof of the ten-person Equinet AI Collaborator roster. It must not be used to assign personal profiles or specialist permissions automatically.

No HubSpot job titles or roles are configured. Any active user can technically be selected as record owner. The source documents provide:

- no owner-assignment rules;
- no reassignment rules;
- no backup-owner rules;
- no technical ownership restrictions by region, segment or role.

Territory and region fields are informational/reporting fields, not access controls.

### A2 consequence

A2 must not auto-assign an owner or territory from this snapshot. Until Equinet approves deterministic assignment and backup rules, A2 must preserve the current owner or return `needs_owner_review`.

Inactive owners must remain valid historical references but cannot receive new assignments.

## 5. Process inventory

The inventory contains:

| Asset type | Count |
|---|---:|
| Workflows | 33 |
| Enabled workflows | 28 |
| Disabled workflows | 5 |
| Lists | 32 |
| Dynamic lists | 19 |
| Static lists | 13 |
| Audit findings | 3 |

### Existing prospect-review assets

The portal includes:

- enabled EQUINET telesales workflows that create call tasks from list membership;
- Kentucky and Lexington lists requiring known email and phone data;
- an EQUINET non-app-user lead list;
- several disabled Mustad owner-specific follow-up workflows.

These assets are not A2 enrichment-review queues.

### No current enrichment-review asset

The inventory explicitly reports:

```text
No matching enrichment review asset identified
```

This confirms that A2 requires either:

- Twenty or another Unitalk review layer;
- a new approved HubSpot review design;
- or a controlled file/manual review during the no-integration pilot.

A2 must not reuse an outreach list or Sample Request approval pipeline as an enrichment-review queue without explicit approval.

### Existing outreach and side-effect risk

Enabled workflows already:

- send app-download and referral emails;
- resend lifecycle/retention emails;
- create call and follow-up tasks;
- change subscription or engagement status;
- create Sample Request records and notes;
- move Sample Requests through approval and shipment stages.

This creates a significant integration risk: a future A2 property update or list-membership change could trigger customer-facing communication or task creation.

Before any HubSpot write, Unitalk must verify the exact workflow enrolment criteria and actions for every mapped property and list. Until that dependency audit passes, all A2 HubSpot writes remain blocked.

### Consent and exclusion assets

The portal has relevant lists and workflows for:

- contacts unsubscribed from all email;
- contacts not opted in to marketing emails;
- hard-bounced users;
- ignored users in the US and AU/NZ;
- internal accounts and internal users;
- SMS opt-in.

These assets improve the future eligibility design but are not currently readable by A2. Their exact list membership logic and business precedence still require live verification.

### Sequence inventory

No sequence resources were returned. This means no sequence asset was identified in this check. It does **not** mean there is no outbound automation: several enabled workflows send emails or create outreach tasks.

A2 remains prohibited from sequence enrolment and external communication.

### Deal and approval gaps

No Deal approval workflow was identified. Sample Request approval workflows exist but apply only to the Sample Requests custom object.

A2 Deal or CRM-change approval cannot rely on an existing Deal approval process from this inventory.

## 6. Work newly unlocked

Unitalk can now:

1. use exact Lifecycle Stage, Lead Status, Deal Stage, Sample Request and Ticket state values in Step 2B external-state references;
2. distinguish lifecycle, lead, customer, subscription, retention and Deal states instead of treating them as one status;
3. draft owner/team/territory mappings with an explicit `needs_owner_review` fallback;
4. treat inactive owners and placeholder/queue owners correctly;
5. document existing exclusion and consent assets as future authoritative checks;
6. design workflow-side-effect protection before HubSpot write-back;
7. confirm that a new A2 enrichment-review layer or workflow is required;
8. draft a more complete HubSpot integration specification without direct access.

## 7. Work still blocked

Unitalk still cannot:

- query lifecycle, Deal, consent, list or owner state for a real record;
- verify user-specific seats, permissions or OAuth scopes;
- confirm exact Contact–Company–Deal/custom-object associations;
- inspect full workflow criteria, branches and actions;
- prove which property change would trigger a workflow;
- assign A2 reviewers or backup owners;
- auto-assign owners or territories;
- create an enrichment-review queue in HubSpot;
- perform or test HubSpot writes;
- verify production idempotency, rollback or reconciliation.

## 8. Impact on the approved A2 foundations

### No structural redesign required

The following remain valid:

- A1-to-A2 handoff and immutable A1 input;
- canonical record structure and generic `field_assessments[]`;
- separate baseline, observations, proposal, decision and application states;
- nullable external-system references;
- human review requirements;
- A1-owned scoring and score revision;
- no-integration CRM-write and outreach prohibitions.

### Factual and safety updates required

The profile must now record that:

- status, user/team/owner and process snapshots have been received;
- no live HubSpot connection exists;
- no existing enrichment-review asset was found;
- no owner-assignment or backup-owner rules are available;
- enabled workflows can send messages, create tasks, update statuses and create records;
- any future A2 HubSpot write requires a workflow-dependency audit first.

## 9. Recommended next path

Continue with Step 2B Field Dictionary and State Model. Step 2B can now define:

- canonical A2 states independently of HubSpot;
- exact external HubSpot state references;
- protected external baseline fields;
- `needs_owner_review` and `workflow_dependency_unverified` states;
- consent, suppression, customer, Deal and sequence checks as unavailable until connection;
- a hard block on write actions until workflow dependencies are verified.

After canonical field keys are stable, create a separate A2-to-HubSpot mapping and workflow-dependency register.

## 10. Readiness statement

```text
HubSpot object/property snapshot: received
Lifecycle and pipeline snapshot: received
Users/teams/owner snapshot: received
Relevant process inventory: received
Existing enrichment-review asset: not found
Owner/backup assignment rules: not available
Live HubSpot read: unavailable
Live HubSpot write: unavailable and unauthorised
Production integration: blocked
```
