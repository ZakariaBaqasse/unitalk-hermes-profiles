# A1 Wave 1 Behavioural Evaluation Report

**Profile:** `equinet-a1-icp-discovery`  
**Model:** `deepseek-v4-flash` through Unitalk AI Gateway / LiteLLM  
**Web:** Exa search + Firecrawl extract  
**Evaluation outputs:** 17  
**Final status:** Technically passed after iterative corrections and business-approved by Séverine.

## Scope

Skills evaluated:

1. `public-prospect-research`
2. `prospect-segment-classification`
3. `equinet-icp-qualification`

The tests covered individual skill behaviour, source-policy enforcement, synthetic edge cases, controlled real-web research and one end-to-end Wave 1 handoff.

## Initial defects detected and corrected

### 1. Restricted directory evidence was retained

The first live research run retained Mad Barn, NewHorse and LinkedIn data as evidence.

**Correction:** added `validate_research_seed.py`, which checks every retained source against the Approved Source Register and rejects blocked, unavailable, unverified, directory-only, platform-only and search-only sources.

### 2. Unknown aggregator domains were accepted

A later run retained Voofla because the domain did not have a register entry.

**Correction:** an unregistered domain can now be retained only when it is verified as the prospect's official `public_business_website`. Unknown directories, aggregators, news and social sources require an approved register entry.

### 3. Research did not stop when sufficient evidence existed

A live run continued to 41 tool calls and was truncated after finding a suitable official website.

**Correction:** added a V1 budget of six searches per single-segment run, three page reads per candidate, ten total tool calls per candidate and no browser fallback by default. The skill must stop once identity, professional activity and geography are sufficiently established.

### 4. Direct website seeds used the wrong discovery method

A user-supplied official website was marked `human_directory_seed`.

**Correction:** added `human_website_seed` to the Research Seed contract.

### 5. Research-to-classification evidence references were not durable

Research used source URLs while downstream skills expected evidence IDs.

**Correction:** Research Seeds now require unique `evidence_id` values. Public contacts reference those IDs. Classification and Qualification reuse the same evidence IDs.

### 6. Hobby-only exclusion was misinterpreted

The initial qualification treated `no_professional_evidence` as “no evidence of any kind” rather than “no evidence of professional activity.”

**Correction:** direct evidence that a person is hobby-only and offers no professional service may confirm both `inactive_or_hobbyist` and `no_professional_evidence`, producing an exclusion.

### 7. Minimum review data was handled inconsistently

One synthetic qualification treated future scoring/confidence fields as already available.

**Correction:** the qualification skill must list every required full-candidate field absent from the provided context. Missing future-stage fields keep `minimum_data_status: fail` until the full candidate is assembled.

### 8. Evaluation sessions attempted package installation and wrote into skill folders

**Correction:** all three skills now require the existing runtime, prohibit package installation during execution and direct temporary output to `tmp/` or the evaluation workspace. Temporary evaluation artifacts were cleaned up.

## Final behavioural results

### Research

- Blocked EquineProFinder and Apify Google Maps requests were refused.
- A human directory seed was treated as discovery-only and uncertainty was preserved.
- Autonomous research found an official Farrier business website using Exa/Firecrawl.
- The final autonomous run used five searches, one page extraction and ten total tool calls.
- The final Research Seed retained only the official business website and passed source-permission validation.
- A controlled user-supplied website seed used `human_website_seed` and validated successfully.

### Segment classification

- Professional Farrier → confirmed `farrier` / `farrier_independent`.
- Commercial breeding farm → confirmed `horse_owner` / `breeding_farm`.
- Ambiguous same-name identity across two states → `needs_review`, no forced segment/type.
- Cross-segment prospect types were rejected.

### ICP qualification

- Farrier output contained all 15 configured criteria.
- Horse Owner output contained all 11 configured criteria.
- Unknown horse count remained `unknown`.
- Unsupported claims remained `unknown` or `not_confirmed`.
- Confirmed claims required evidence IDs.
- Hobby-only/non-professional Farrier evidence produced `exclusion_status: excluded` after correction.
- Missing full-candidate fields remained visible and produced `minimum_data_status: fail` until later stages.

## Final end-to-end result

The final controlled chain succeeded:

```text
Research Seed
→ validated
→ Classification Decision
→ validated
→ Qualification Object
→ validated against Prospect Candidate Schema
```

Preserved artifacts:

```text
evaluations/wave1/iteration-7/end-to-end/artifacts/research-seed.json
evaluations/wave1/iteration-7/end-to-end/artifacts/classification-decision.json
evaluations/wave1/iteration-7/end-to-end/artifacts/qualification-output.json
```

Final candidate classification:

- segment: `farrier`
- prospect type: `farrier_independent`
- classification status: `confirmed`
- qualification criteria: 15/15 represented
- exclusion status: `eligible`
- minimum data status: `fail` because Wave 2/3 fields were intentionally absent
- confidence and ICP score: not calculated, as required for Wave 1

## Deterministic regression status

```text
ALL WAVE 1 SKILL TESTS PASSED
```

The regression suite now protects:

- search/run budgets;
- blocked and directory-only source rejection;
- unregistered aggregator rejection;
- human website provenance;
- evidence-ID continuity;
- segment/type compatibility;
- ambiguity handling;
- all segment criteria;
- unknown horse count;
- exclusion semantics;
- confirmed-criterion evidence requirements;
- Candidate Schema compatibility.

## Business acceptance

Séverine confirmed:

- the real prospect is relevant;
- segment `farrier` is correct;
- prospect type `farrier_independent` is correct;
- confirmed criteria are reasonable;
- unknown criteria are appropriately cautious;
- public business address, phone and email should be retained by A1 with evidence;
- explanation length is acceptable;
- the official business website is an acceptable primary source.

The clearer identity value `person_and_organisation` replaces `linked_person_organisation`. It means the candidate includes both J.T. Holub as a person and James Holub Equine Services as the associated organisation.

Final accepted artifacts:

```text
evaluations/wave1/iteration-8/accepted-artifacts/search-plan.json
evaluations/wave1/iteration-8/accepted-artifacts/research-seed.json
evaluations/wave1/iteration-8/accepted-artifacts/classification-decision.json
evaluations/wave1/iteration-8/accepted-artifacts/qualification-output.json
evaluations/wave1/iteration-8/accepted-artifacts/business-acceptance.json
```

These artifacts passed the plan/run/timestamp check, source-permission validator, classification validator and Candidate qualification schema.

No further technical or business blocker remains for Wave 1. The profile is not yet pilot-ready because Wave 2/3 skills, quotas and full-candidate acceptance tests remain outstanding.
