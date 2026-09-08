# Equinet A1 — Wave 2 Simplified Validation Review

**Profile:** `equinet-a1-icp-discovery`  
**Scope:** `prospect-evidence-and-confidence` and `icp-scoring-and-rationale`  
**Method:** Reuse five existing behavioural outputs, rerun only the corrected Farrier exclusion scenario, and deterministically corroborate critical values.  
**Result:** `6/6 scenarios passed`  
**Decision:** `Approved by Séverine for the A1 V1 pilot`  
**Approval recorded at:** `2026-08-14T16:25:31Z`  
**Promotion applied:** `Yes`

**Post-promotion verification:** Both official skill validations and the complete Wave 2 regression suite passed.

## Scenario results

| # | Scenario | Skill | Result | Key observed behaviour | Limitation |
|---:|---|---|---|---|---|
| 1 | Official business website — James Holub confidence | `prospect-evidence-and-confidence` | **PASS** | 84 / High; one strong official source accepted; limitation visible | Relies on one official business source; externally controlled claims still require targeted verification. |
| 2 | Mandatory claim supported by inference only | `prospect-evidence-and-confidence` | **PASS** | 59 / Low; mandatory inference-only cap applied | Synthetic case used to verify the approved mandatory-claim confidence cap. |
| 3 | Blocked source invalidates confidence | `prospect-evidence-and-confidence` | **PASS** | Rejected; exact blocked-source error; no confidence package | Synthetic Yellow Pages case; no blocked source is accepted as retained evidence. |
| 4 | James Holub deterministic ICP scoring and rationale | `icp-scoring-and-rationale` | **PASS** | 86 / High; component total matches; confidence remains separate | The result requires human review and does not authorise outreach or CRM action. |
| 5 | Horse Owner with unknown horse count | `icp-scoring-and-rationale` | **PASS** | 80 numeric; raw High capped to Medium; review outcome preserved | Synthetic case; the unknown horse count is intentionally not inferred. |
| 6 | Farrier with confirmed no professional evidence | `icp-scoring-and-rationale` | **PASS** | Blocked; null score/band; precise exclusion; no invented schema error or external action | Corrected scenario rerun through the actual equinet-a1-icp-discovery profile. |

## Boundary checks

- No outreach was initiated.
- No HubSpot or Twenty write was performed or claimed.
- No A2 handoff was triggered.
- Confidence did not override an exclusion or change the numeric ICP score.
- Unknown horse count remained unknown and triggered the approved review cap.
- The corrected Farrier exclusion report did not invent a schema failure.

## Technical preflight

Both documented root wrappers executed successfully with the profile virtual environment. The previous gateway safety false-positive did not recur.

## Acceptance decision

The two Wave 2 skills satisfy the simplified technical and behavioural acceptance set. Séverine approved them for the A1 V1 pilot on 14 August 2026. This approval closes the Wave 2 checkpoint; it does not constitute Equinet production acceptance.

### Applied status

```text
version: 1.0.0
status: validated_for_a1_v1_pilot
```

After approval, proceed to Wave 3: `ranked-prospect-review-package`, then `prospect-export`.
