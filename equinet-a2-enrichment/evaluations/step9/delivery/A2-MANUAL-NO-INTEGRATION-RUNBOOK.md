# Equinet A2 Manual No-Integration Runbook

**Release:** `equinet-a2-no-integration-1.0.0`  
**Status:** `PILOT_READY_NO_INTEGRATION`

## 1. Preflight

1. Work only in `/opt/data/profiles/equinet-a2-enrichment`.
2. Require an approved A1 handoff and valid candidate snapshot hash.
3. Confirm the candidate-specific processing approval, reviewer and scope.
4. Confirm that the Unitalk gateway route is available without printing credentials.
5. Confirm fallback is disabled and the prepaid balance is below no-stop risk thresholds.
6. Keep HubSpot, Twenty, n8n, Apify, outreach and downstream delivery disabled.
7. Keep Web disabled unless a separate bounded source plan is approved for that candidate.

## 2. Intake and planning

Use absolute commands:

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python   /opt/data/profiles/equinet-a2-enrichment/scripts/a2_intake.py <handoff.json> --output-dir <candidate-dir>

/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python   /opt/data/profiles/equinet-a2-enrichment/scripts/build_a2_gap_plan.py <request.json> --output <gap-plan.json>
```

Reuse approved A1 evidence first. Never recollect a verified current value without a named reason.

## 3. Conditional official-site research

Activate Web only for an approved candidate, allowed domain and named gap. Record the page/call/retry budget before access. Stop on terms or robots denial, login, paywall, CAPTCHA, HTTP 403/429, unexpected personal data or budget/scope limit. Search snippets are discovery-only. Do not open linked social profiles.

After collection, disable Web before classification, confidence, quality and review generation.

## 4. Verification and quality

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python   /opt/data/profiles/equinet-a2-enrichment/scripts/normalise_and_validate_a2_observations.py   <observations.json> --output <validated-observations.json>

/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python   /opt/data/profiles/equinet-a2-enrichment/scripts/evaluate_a2_evidence_confidence.py   <evidence-request.json> --output <evidence-result.json>

/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python   /opt/data/profiles/equinet-a2-enrichment/scripts/evaluate_a2_minimum_package.py   <field-state-snapshot.json> --output <minimum-package-result.json>
```

A selected named contact may map to `secondary`. A `primary` role does not satisfy named-contactability without a verified named email or phone. A High A1 score does not override an incomplete A2 package.

## 5. Canonical revision and review

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python   /opt/data/profiles/equinet-a2-enrichment/scripts/create_a2_revision.py   <previous.json> <proposed.json> --output <revision-result.json>

/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python   /opt/data/profiles/equinet-a2-enrichment/scripts/render_and_validate_a2_review_package.py   <record.json> --previous-record <previous.json> --output-dir <review-dir>
```

Present one consolidated final review containing field decisions, corrected values, the record decision, evidence, gaps, limitations and any exact future patch preview. Intermediate implementation checks are not runtime approval gates.

## 6. Decision outcomes

- `approved`: preserve the review receipt; no write follows without a separately approved guarded action.
- `held`: retain the record and named gaps; do not downgrade the A1 score.
- `needs_changes`: create a new immutable revision after authorised correction.
- `rejected`: record the reason without altering the A1 source snapshot.

## 7. Failures and recovery

- Never retry a full run automatically.
- Retry one failed source URL at most once when policy permits.
- Preserve the last validated artifact and resume from the first missing gate.
- Treat unavailable usage or cost as unknown, not zero.
- Use absolute paths in non-interactive sessions.
- If the gateway fails, save partial artifacts, stop and notify; fallback remains disabled.

## 8. Audit and closeout

Record actor, trigger, timestamp, source references, model/tool route, output, approval state, external actions, result, retries and usage. Verify zero unauthorised external actions and retain the authoritative canonical JSON plus validated review exports.
