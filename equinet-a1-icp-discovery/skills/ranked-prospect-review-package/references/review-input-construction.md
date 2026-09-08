# Review-Input Construction Reference

When building the `review-input.json` for `build_review_package.py`, the
deterministic script expects a specific directory layout and file-naming
convention. Getting these wrong causes `FileNotFoundError` or validation
failures.

## Directory layout

After scoring completes, a staged live run produces files in TWO locations
under the run directory:

```
evaluations/live-runs/{LIVE-RUN-ID}/
├── research/                              ← Research seeds live here
│   ├── seed-{name}.json
│   └── ...
├── candidates/{candidate-directory}/      ← Everything else per candidate
│   ├── classification-decision.json
│   ├── qualification-package.json         ← (not qualification-assessment.json)
│   ├── confidence-package.json
│   └── scoring-package.json
└── review-input.json                      ← Input to build_review_package.py
```

## Candidate-to-directory mapping

The `review-input.json` must reference the research seed from `research/`
and the remaining files from `candidates/{name}/`. The candidate directory
name is **separate** from the `candidate_id` field in the review input.

| candidate_id example | Directory name | Research seed |
|---|---|---|
| `A1-JTHOLUB-LEX-001` | `jt-holub` | `research/seed-jt-holub.json` |
| `A1-BOBBY-MENKER-002` | `bobby-menker` | `research/seed-bobby-menker.json` |
| `A1-KY-LEGEND-003` | `kentucky-legend` | `research/seed-kentucky-legend.json` |

**Pitfall:** The directory names use lowercased hyphens (e.g. `jt-holub`),
not the uppercase-ID convention (`JTHOLUB`). Use a mapping table — never
construct the directory path programmatically from the candidate ID.

## Required bundle fields

Every entry in `review_input.candidates[]` requires exactly these fields:

```json
{
  "candidate_id": "A1-{TYPE}-{CITY}-{NNN}",
  "record_kind": "production",
  "research_seed": { ... },
  "classification_decision": { ... },
  "qualification_package": { ... },
  "confidence_package": { ... },
  "scoring_package": { ... },
  "source_policy_status": "approved",
  "access_method": "approved_search_tool",
  "model": "deepseek-v4-flash",
  "tools_used": ["web_search", "web_extract", "terminal", "execute_code", ...],
  "hubspot_check": {
    "status": "no_match",
    "checked_at": "2026-08-28T15:00:00Z",
    "method_version": "n8n-hubspot-dedup-1.0.0",
    "matches": [],
    "notes": "n8n completed the live HubSpot duplicate check."
  }
}
```

`hubspot_check` is optional for backward compatibility. When n8n supplies it,
the builder validates and copies it unchanged to
`prospect_candidate.duplicate_check.hubspot`; otherwise the legacy
`unavailable` result is generated. The input accepts both the review package's
legacy names (`possible_match`, `confirmed_duplicate`, `error`) and n8n's
canonical names (`not_checked_no_domain`, `possible_duplicate`,
`hubspot_duplicate`, `hubspot_check_failed`). Possible/confirmed duplicates and
check failures remain human-review gates and never authorise outreach, A2
handoff, or a CRM write.

Key rules:
- `qualification_package` must contain `{"qualification": {..., "criteria": [...], ...}}` — the full output of `build_qualification.py`, not the assessment input.
- `confidence_package` must contain `{"confidence": {"level": "...", "score": N, ...}}` — the output of `build_confidence_package.py`.
- `scoring_package` must contain both `{"scoring": {...}, "audit": {...}}` — the output of `build_scoring_package.py`.
- `source_policy_status` controls the `reliability_level` field on every evidence record.
- `access_method` and `tools_used` populate the `provenance` section.

## What the builder assembles

`build_review_package.py` performs this sequence:

1. Validates the review input against `references/review-input.schema.json`.
2. For each bundle, calls `assemble_candidate()` which:
   - Copies `qualification`, `confidence`, and `scoring` from their packages.
   - Resolves `minimum_data_status` (fields resolvable at review stage vs. truly missing).
   - Builds `identity` from `research_seed.identity_hint` + `classification_decision`.
   - Builds `location` from `research_seed.location_hint` + geography rule.
   - Builds `source_evidence[]` by mapping evidence_ids from qualification criteria and contacts back to `research_seed.source_candidates[]`.
3. Runs batch duplicate checks across all candidates using domain/email/phone/identity+location keys.
4. Derives `recommended_review_status` (accept / needs_research / reject) from score, confidence, and data-quality state.
5. Sorts and ranks candidates.
6. Validates every assembled Prospect Candidate against the canonical schema.
7. Validates the final review package against its own schema.

## JSON loading path pitfall

The research seed is at `research/seed-{name}.json`, **not** at
`candidates/{name}/seed-{name}.json`. Using a path like
`candidates/{name}/../research/seed-{name}.json` also fails because
`../../research/` resolves incorrectly when the seed path uses a
subdirectory above.

**Always use `{run_dir}/research/seed-{name}.json` directly.**

## Package ID convention

```
A1-RP-{RUN-TIMESTAMP}-{SHORT-HEX}
```

Example: `A1-RP-LIVE-20260823-469CA5`

The `package_id` pattern in the schema is `^A1-RP-[A-Z0-9_-]{4,80}$`.
Use the LIVE run short suffix for uniqueness.