# Equinet HubSpot Metadata Intake Audit for A2 Enrichment

**Audit version:** `0.1.0`  
**Recorded at:** `2026-08-25T09:51:49Z`  
**Status:** `PARTIAL METADATA SNAPSHOT RECEIVED — NO LIVE HUBSPOT CONNECTION`  
**Profile:** `equinet-a2-enrichment`

## 1. Executive conclusion

The supplied HubSpot data-model image and property-definition export materially improve A2 delivery readiness.

They now allow Unitalk to:

- identify real HubSpot objects, property internal names, data types, enum options and read-only status for the six exported objects;
- draft a Contact/Company/Deal mapping for A2;
- map candidate protected, consent, customer, sequence, owner, territory, data-quality and enrichment fields;
- avoid proposing duplicate fields that already exist;
- use real HubSpot metadata when designing Step 2B and the later integration specification.

They do **not** provide live HubSpot access and do not prove live values, fill rates, permissions, association labels, workflow dependencies or write behaviour. A2 cannot yet perform authoritative CRM checks or any HubSpot action.

The approved A1-to-A2 handoff and canonical A2 design remain structurally valid. No redesign is required. Only integration-readiness status and the HubSpot intake register need updating.

## 2. Inputs and integrity

| Input | Result |
|---|---|
| Data-model image | Read through tiled OCR; image size 2116 × 1248 |
| Image SHA-256 | `1aac099ce0158752e336e813dfe56728a8b7a66f28448a8d098193072bcfce39` |
| Property-definition CSV | Parsed successfully: 950 rows × 14 columns |
| CSV SHA-256 | `3303992627bad953e28913eaf3b19cdc998fc0c6f3f6f29ef455d788e8c9b952` |
| Duplicate internal names within an object | 0 |
| Duplicate property labels within an object | 3 |
| Authored-artifact language | English |

## 3. Data-model image findings

The image shows a wider HubSpot model than the property-definition export.

### CRM objects visible

Appointments, Campaigns, Carts, Companies, Contacts, Courses, Listings, Marketing events, Orders, Projects, Services, Tickets and Users.

### Sales objects visible

Contracts, Credit memos, Deals, Invoices, Leads, Line items, Payments, Quotes and Subscriptions.

### Activity objects visible

Calls, Communications, Emails, Meetings, Notes, Postal Mail and Tasks.

### Custom objects visible

- Complaints
- Sample Requests

The image confirms the object landscape but is not a reliable association-label or cardinality export. Exact associations still require a dedicated metadata export or read-only API verification.

## 4. Property-export findings

| Object | Type ID | Properties | Writable | Read only |
|---|---:|---:|---:|---:|
| Company | `0-2` | 227 | 111 | 116 |
| Contact | `0-1` | 431 | 256 | 175 |
| Deal | `0-3` | 145 | 30 | 115 |
| Ticket | `0-5` | 78 | 20 | 58 |
| Complaints | `2-251550468` | 28 | 14 | 14 |
| Sample Requests | `2-204687032` | 41 | 25 | 16 |

The export contains definitions for six objects only. It does not include property definitions for most objects visible in the image.

All 950 rows have blank `Field type`, `Group`, `Description` and data-entry guidance in this export. Business meaning therefore cannot be inferred solely from labels and internal names where ambiguity exists.

## 5. Existing fields that materially help A2

### Identity and matching

Existing fields include:

- Contact: `firstname`, `lastname`, `email`, `secondary_email`, `work_email`, `phone`, `mobilephone`, `secondary_phone_number`, `jobtitle`, `contact_type`, address fields, website and public-profile URLs;
- Company: `name`, `trade_name`, `domain`, `website`, `company_email`, `phone`, address fields, `company_type` and `business_type`;
- HubSpot record IDs and merged-object IDs;
- Contact email is marked as a unique lookup property.

This supports a much more concrete identity and duplicate-matching specification. Company domain is not marked unique, so it cannot be the sole Company duplicate key.

### Farrier and Horse Owner enrichment

Existing Contact properties include:

- `farrier_active_flag`;
- `farrier_certifications`;
- `disciplines_worked_with`;
- `farrier_primary_discipline`;
- `farrier_horses_served`;
- `years_experience`;
- `farrier_school`;
- `owner_horse_count`;
- `horse_count_range`;
- `owner_primary_discipline`;
- `owner_breeds`;
- `owner_stable_name`;
- `stable_type`;
- `horse_relationship`;
- `association_member`.

This means A2 can reuse many existing properties rather than proposing a new property for every enrichment value.

### Data quality and enrichment

Existing fields include:

- Contact `contact_verified`;
- Contact and Company `data_quality` with Complete, Partial and Needs Review;
- Contact and Company `hs_is_enriched` as read-only HubSpot fields;
- Contact `hs_contact_enrichment_opt_out` and timestamp as read-only fields;
- Company `mailing_verified`.

These fields are mapping candidates, not yet approved A2 semantics. `contact_verified` and `data_quality` must not be treated as equivalent to the future A2 evidence/confidence policy until Equinet approves their business meaning.

### Customer, consent and suppression controls

The export exposes concrete fields for:

- `do_not_contact`;
- `gdpr_consent`;
- `hs_legal_basis`;
- marketing-email, SMS, WhatsApp, direct-mail and app communication opt-ins;
- global and subscription-specific email opt-outs;
- `hs_marketable_status`;
- `hs_current_customer`;
- `lifecyclestage`;
- `hs_lead_status`;
- current sequence and prospecting-agent enrolment;
- associated and open Deal counts;
- Deal stages.

A2 can now draft exact authoritative-read gates for CRM-connected operation. These fields remain unavailable at runtime until HubSpot read access exists.

### Ownership and data boundary

The export includes:

- Contact and Company owner fields;
- assigned Equinet/Mustad rep fields;
- territory;
- team and shared-user fields;
- business-unit/brand values for `EQUINET App` and `Mustad USA`.

These values confirm that Equinet and broader Mustad data coexist in the portal. The mapping must enforce Equinet-approved business-unit, team and record-access boundaries; the export does not grant cross-entity access.

## 6. Important data-quality and governance findings

1. **Horse-count ranges overlap.** `horse_count_range` contains both `5 - 20 horses` and `11 - 25 horses`. This must not drive deterministic qualification until Equinet resolves the taxonomy or Unitalk defines a non-ambiguous mapping rule.
2. **Duplicate opt-out labels exist.** Contact has two properties labelled `Opted out of email: Marketing Information` with different internal names. Internal names and business-unit/subscription meaning must be used; labels alone are unsafe.
3. **Three duplicate labels exist overall.** Two are `Cumulative conversion`; one is the marketing-information opt-out label.
4. **Descriptions and groups are absent.** Every exported property lacks a description and group in this file, so ambiguous properties require client confirmation or live usage inspection.
5. **HubSpot enrichment fields are not A2 workflow fields.** Read-only `hs_is_enriched` and HubSpot enrichment-opt-out fields cannot serve as proof that the Unitalk A2 workflow completed or was approved.
6. **Existing score fields are not the A1 score.** `hs_ideal_customer_profile`, predictive-contact score, contact priority and Deal score must not replace the approved A1 score-revision model.
7. **Sensitive fields exist but are outside A2 scope.** Date of birth, gender, marital status, military status and similar fields must not be enriched by A2.
8. **Writable does not mean authorised.** A property marked writable in the export still requires mapping approval, user scope, conflict handling and recorded human approval.

## 7. Work newly unlocked without a live connection

Unitalk can now create:

1. a draft A2-to-HubSpot mapping for Contact, Company and Deal;
2. exact candidate field types and enum values for Step 2B;
3. a protected-field candidate register using real internal names;
4. draft duplicate matching using Contact email, record IDs, merged IDs, Company domain plus additional identity fields;
5. a draft consent/customer/Deal/sequence eligibility matrix;
6. a draft owner, team, business-unit and territory read mapping;
7. deterministic validators that reject unknown internal names, wrong types, invalid enum values and attempted writes to read-only properties;
8. a gap analysis identifying fields that require Unitalk staging rather than HubSpot properties.

## 8. Work still blocked

Without live read-only access and the remaining operational configuration, Unitalk cannot yet:

- confirm that the export matches the current portal state;
- inspect record values or fill rates;
- verify Contact–Company–Deal and custom-object associations and labels;
- identify workflows, lists or forms that read or overwrite properties;
- test duplicate searches or customer/consent checks;
- verify business-unit, team and individual user scopes;
- prove that a property is manually maintained or safe to update;
- read, create, merge or update a HubSpot record;
- validate retries, idempotency, reconciliation or rollback;
- approve production integration.

## 9. Impact on the existing A2 profile

### No structural redesign required

The following remain valid:

- A2 Implementation Contract mission and approval boundary;
- A1-to-A2 handoff and immutable A1 snapshot;
- generic canonical `field_assessments[]` design;
- nullable external references;
- protected-field conflict model;
- A1-owned scoring and A2-triggered requalification;
- no-integration state ceiling and prohibition on CRM writes.

### Required factual updates

The profile should now state:

- HubSpot data-model image received;
- property-definition export received for Company, Contact, Deal, Ticket, Complaints and Sample Requests;
- direct HubSpot access remains unavailable;
- association labels, operational usage, permissions and live verification remain pending;
- a proposed mapping may now be drafted but is not approved or tested.

### Configuration work to add later

A separate versioned mapping must define for every selected property:

- canonical A2 field key;
- HubSpot object and internal name;
- read/propose/approved-write direction;
- authoritative source;
- protected status;
- enum/type conversion;
- conflict and missing-value behaviour;
- approval requirement;
- connector scope;
- failure and reconciliation behaviour.

This mapping must remain outside the canonical A2 schema.

## 10. Recommended next path

1. Continue with Step 2B Field Dictionary and State Model using the received HubSpot metadata as a mapping reference.
2. Build a preliminary Contact/Company/Deal mapping after the canonical field keys are stable.
3. Request the remaining HubSpot intake package:
   - association labels/cardinalities;
   - relevant workflow, list and form inventory;
   - representative anonymised records;
   - property fill-rate/usage information if available;
   - read-only OAuth/API verification;
   - confirmed business-unit/team access boundary.
4. Do not enable HubSpot reads or writes until scopes, live metadata and approval are verified.

## 11. Readiness statement

```text
HubSpot metadata snapshot: received and parsed
A2 mapping draft: now possible
Live HubSpot read: unavailable
Live HubSpot write: unavailable and unauthorised
Production integration: blocked
```
