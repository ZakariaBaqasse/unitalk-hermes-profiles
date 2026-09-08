# Equinet A1 — Wave 2 Skill Audit

**Audited at:** `2026-08-14T10:22:07Z`  
**Profile:** `equinet-a1-icp-discovery`  
**Technical readiness:** Passed after fixes  
**Behavioural acceptance:** Passed simplified validation; approved by Séverine for A1 V1 pilot on 14 August 2026  
**Production / Equinet acceptance:** Not assessed

## Scope

Wave 2 contains two installed skills:

1. `prospect-evidence-and-confidence`
2. `icp-scoring-and-rationale`

The profile reports six installed skills in total. Wave 2 depends on the Prospect Candidate Schema, ICP Configuration, Approved Source Register, Evidence and Confidence Rules, ICP Scoring Model and accepted Wave 1 artifacts.

## Findings and fixes

### Fixed — invalid SKILL.md frontmatter

Both Wave 2 skills stored `version` and `status` as unsupported top-level frontmatter keys. The official skill validator rejected both packages. These values were moved under the supported `metadata` key. Both packages now pass `quick_validate.py`.

### Confirmed — root and bundled wrappers are equivalent

The root wrappers referenced by the skills and the bundled skill scripts use the same implementation with path-resolution differences only. Smoke tests produced identical JSON outputs:

- confidence: `84 / high`;
- scoring: `86 / high / high_priority_farrier`.

### Fixed — specific exclusion outcome was lost

The scoring engine previously returned the generic outcome `excluded` whenever `qualification.exclusion_status` was already `excluded`, even when a confirmed segment exclusion criterion supplied a more precise outcome. Confirmed exclusion criteria are now evaluated first.

The Farrier exclusion path now returns:

```text
status: blocked
score: null
band: null
block_reason: Confirmed exclusion criterion: farrier.no_professional_evidence.
outcome: excluded_no_professional_evidence
```

### Fixed — blocked-score explanation

Blocked scoring no longer produces an interpretation such as `ICP band None`. It now states that evidence confidence cannot override the exclusion. The explanation also omits the misleading list of unearned weighted criteria because scoring did not occur.

### Fixed — unsupported behavioural claim

The first behavioural run for the missing Farrier-exclusion scenario claimed that the wrapper had a package-schema failure, but direct reproduction showed no such failure. The skill now instructs A1 to quote only the exact wrapper error and never invent or infer a schema failure.

The corrected deterministic artifact is stored at:

```text
evaluations/wave2/iteration-1/scoring-farrier-exclusion/artifacts/scoring-package.json
```

## Test results

All of the following pass:

- official package validation for both Wave 2 skills;
- Evidence and Confidence Rules validation;
- evidence/confidence regression suite;
- ICP Scoring Model validation;
- ICP scoring regression suite;
- Wave 2 integration suite;
- Python compilation checks;
- root-wrapper smoke tests;
- root-versus-bundled output equality checks.

Key covered cases:

- one official business website may produce High confidence;
- mandatory inference-only claim caps confidence at Low;
- blocked evidence source invalidates confidence;
- confidence-stage minimum mismatch is rejected;
- ideal and medium Farrier scores;
- apprentice and inactive pathways;
- ideal Horse Owner score;
- unknown and at/below-three horse-count pathways;
- missing evidence is rejected;
- Farrier and Horse Owner exclusions block scoring;
- specific exclusion outcomes are preserved;
- confidence cannot override an exclusion;
- scoring components sum to the numeric score;
- weight, version and approval-record drift are rejected.

## Behavioural evaluation inventory

Six of six intended scenario directories now exist:

- confidence — official business website;
- confidence — inference-only mandatory claim;
- confidence — blocked source;
- scoring — accepted James Holub candidate;
- scoring — Horse Owner unknown count;
- scoring — Farrier exclusion.

However, the behavioural evaluation lifecycle is not complete:

- no formal grading files exist;
- no benchmark exists;
- no Wave 2 review document exists;
- no human review/acceptance is recorded;
- the corrected Farrier exclusion instructions have not yet been rerun as a clean behavioural iteration.

## Readiness decision

The two Wave 2 skills are technically valid and passed the simplified behavioural validation. Séverine approved both for the A1 V1 pilot. This does not constitute Equinet production acceptance.

## Required next step

Proceed to Wave 3: create and validate `ranked-prospect-review-package`, then `prospect-export`. The completed simplified Wave 2 review is stored at `evaluations/wave2/validation-simplified/WAVE2-SIMPLIFIED-REVIEW.md`.
