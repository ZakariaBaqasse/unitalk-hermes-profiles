# Two-lane post-n8n processing runbook

## Boundary

Start only from the persisted compact `a1.discovery-result.v1` artifact. Never rerun n8n discovery, source acquisition, deduplication, or HubSpot checks during processing.

## 1. Determine the durable next action

```text
python3 skills/post-n8n-public-website-enrichment/scripts/route_and_overlay.py next-action \
  --input <discovery-result.json> --work-dir <two-lane-v1>
```

Always follow the returned action. Do not infer phase completion from chat history.

## 2. Route

```text
python3 skills/post-n8n-public-website-enrichment/scripts/route_and_overlay.py route \
  --input <discovery-result.json> --output-dir <two-lane-v1>
```

The router writes `routing-index.json`, two lane subsets, and no-website overlays. Empty lane subsets are valid artifacts but must not be passed to the stager.

## 3. Stage the no-website lane

When its count is non-zero, the worker stages the Company first and verifies its UUID. If the immutable lead has `name`, it then stages one linked Person using that UUID as `companyId`; otherwise phone/email remain on Company.

```text
python3 skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_rest.py \
  --input <two-lane-v1>/no-website-discovery-result.json \
  --overlays <two-lane-v1>/no-website-overlays.json \
  --output-dir <two-lane-v1>/staging-no-website
```

The overlay writes `qualificationStatus=NOT_CHECKED` and `icpScoreStatus=NOT_SCORED`; numeric score/band/confidence fields remain absent/null. Never reuse a non-empty incomplete output directory.

## 4. Initialise website enrichment

When the website-candidate count is non-zero:

```text
.venv/bin/python skills/post-n8n-public-website-enrichment/scripts/manage_enrichment.py init \
  <two-lane-v1>/website-candidate-discovery-result.json \
  --state <two-lane-v1>/enrichment-state.json --max-retries 2
```

Use `summary` and stable `next --batch-size 5` calls. Research only the returned batch. A candidate URL is not evidence until an official destination page is retrieved and accepted.

## 5. Score ready records

Submit cited enrichment with evidence-linked classification, qualification and confidence assessments, then checkpoint with `accept`. Execute deterministic wrappers one lead at a time:

```text
.venv/bin/python skills/post-n8n-public-website-enrichment/scripts/manage_enrichment.py run-ready \
  --state <two-lane-v1>/enrichment-state.json \
  --output-dir <two-lane-v1>/enrichment-artifacts \
  --lead-id <lead-fingerprint>
```

Item-level source/access failures use `fail` with bounded retries. A deterministic wrapper, schema or configuration failure after accepted official-site verification produces a verified-unscored terminal overlay: retain the official URL, keep all assessment values null, and record the fallback reason. A failure before official-site verification still requires operator repair and must not be relabelled as verified or no-site evidence.

Run classification, qualification, confidence and scoring validators with the profile-local `.venv/bin/python`. Provision that environment before a discovery run from `configurations/operations/a1-python-runtime-requirements.txt`; never install packages during a run.

## 6. Build and stage website overlays

After the enrichment summary returns `build_overlays`:

```text
python3 skills/post-n8n-public-website-enrichment/scripts/route_and_overlay.py build-website-overlays \
  --input <two-lane-v1>/website-candidate-discovery-result.json \
  --state <two-lane-v1>/enrichment-state.json \
  --output <two-lane-v1>/website-overlays.json

python3 skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_rest.py \
  --input <two-lane-v1>/website-candidate-discovery-result.json \
  --overlays <two-lane-v1>/website-overlays.json \
  --output-dir <two-lane-v1>/staging-website
```

Scored overlays populate the verified dedicated Twenty fields. Verified-unscored overlays populate `domainName` while leaving qualification, score, band, outcome and confidence null. Failed or none-found items remain unscored without `domainName`. Existing scored Companies are not downgraded by weaker unscored rediscovery.

## 7. Merge and consume

```text
python3 skills/post-n8n-public-website-enrichment/scripts/route_and_overlay.py merge-indexes \
  --input <discovery-result.json> \
  --no-website-index <two-lane-v1>/staging-no-website/staging-index.json \
  --website-index <two-lane-v1>/staging-website/staging-index.json \
  --output <two-lane-v1>/final-staging-index.json
```

Omit a lane-index argument only when the routing count for that lane is zero. The merger produces `a1.twenty-entity-staging-index.v3`. Mark the polling ticket consumed only with this complete final index; `mark-consumed` revalidates the discovery file hash, run ID, exact ordered fingerprint coverage, lane membership, aggregate counts, Company IDs, expected Person IDs and verified relation artifacts.

## Person staging and partial-failure recovery

- `business_name + name`: Company uses `business_name`; Person uses unsplit `name`; phone/email go only to Person.
- `name` only: both Company and Person use `name`; phone/email go only to Person.
- `business_name` only: no Person is created; phone/email remain on Company.
- neither: `blocked_missing_company_name` with no write.
- The Company must be fully reconciled before Person preflight or write.
- Person duplicate precedence is Company plus exact email, exact phone, then normalized full name; soft-deleted matches and ambiguities are held.
- Never retry an uncertain Person write. Preserve `company_staged_person_sync_failed` and use a separately reviewed recovery based on persisted artifacts.
- `company_staged_person_possible_match` and `company_staged_person_sync_failed` are complete terminal partial states; they preserve the verified Company while requiring human/operator action for Person.

## Safety

- Company plus at most one linked Person; no other Twenty object writes.
- Preserve reviewer-controlled `discoveryStatus`.
- Never retry an uncertain write.
- Hold active ambiguous and soft-deleted exact matches.
- No HubSpot writes, Opportunities, tasks, messages, campaigns, A2 invocation, or outreach.
