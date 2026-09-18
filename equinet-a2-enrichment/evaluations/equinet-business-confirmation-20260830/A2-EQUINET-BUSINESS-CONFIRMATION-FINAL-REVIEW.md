# A2 Equinet Business Confirmation — Final Review

**Configuration version:** `0.2.0`  
**Runtime overlay:** `1.1.0`  
**Active foundation manifest:** `1.2.0`  
**Decision:** `APPROVED AND IMPLEMENTED BY UNITALK OPERATIONS — NO INTEGRATION ACTIVATION`  
**Decision timestamp:** `2026-08-30T17:05:11Z`

## Implemented decisions

- Exact Equinet-confirmed Farrier and Horse Owner role groups and conditional responsibility rules.
- One selected named contact by default; two maximum with a documented large-organisation or shared-responsibility reason.
- `Contact Needed / Needs Review` when no suitable target-role person is found; unrelated roles and general organisation contacts do not satisfy the target-contact need.
- Horse Owner completeness requires current role, stable/farm type, exact horse count, at least one verified breed, organisation name and public business location.
- Attempt both professional email and business phone; one verified channel satisfies the minimum when the other is unavailable.
- Attempt complete address; state and country are the minimum verified location components.
- Preserve verified `Mixed` or `Other` breed values.
- Existing matched HubSpot `Contact.owner_horse_count` is authoritative. Net-new prospects or empty HubSpot values may use explicit approved evidence. Horse-count inference is prohibited.
- `horse_count_range` is ignored and new `horse_count_band` values are disabled.
- Missing business data remains reviewable. Research exhaustion produces the consolidated human review; `held` is reserved for a true blocking dependency and `approved_collect_during_discovery` is available as a governed human disposition.
- HubSpot synchronisation remains conditional on final human review, active guarded integration and read-back reconciliation.

## Verified results

- Business configuration and dependency-closure checks: `32/32 PASS`.
- Confirmed role aliases exercised: `55`.
- Contact-selection cases: one accepted, justified two accepted, three rejected, no-contact routed to `Contact Needed` review.
- Horse Owner complete-with-email-only case: review-ready; missing phone remains a preferred visible gap.
- Missing horse count after exhausted research: incomplete but routed to human review.
- No suitable contact after exhausted research: incomplete and routed to `Contact Needed / Needs Review`.
- Location validation: state and country accepted as minimum; missing country rejected.
- `Mixed` breed preserved.
- New horse-count-band value rejected.
- CSV fidelity: 33 catalogue rows, 12 source rows and 33 mapping rows.
- Full no-integration Farrier workflow: pass across 14 operators.
- Full no-integration Horse Owner/requalification workflow: pass across 14 operators.
- External calls and external business actions: zero.

## Preserved boundaries

- A1 owns ICP scoring and score revisions.
- Missing A2 information does not reject or downgrade a prospect.
- No public information creates consent.
- HubSpot, Twenty, n8n and HarvestAPI remain unconnected or inactive.
- No CRM write, outreach or durable delivery was performed.
- The canonical schema remains `1.0.0`; business rules remain external versioned configuration.

## Remaining integration work

- Attach the named Equinet approver and original source-message reference to the decision record when supplied.
- Verify live HubSpot property types, associations, values, permissions and workflows.
- Implement guarded read/propose/write and read-back for `owner_horse_count` and the other approved fields.
- Confirm the destination application/workspace mapping when the HubSpot/Twenty integration is built.
