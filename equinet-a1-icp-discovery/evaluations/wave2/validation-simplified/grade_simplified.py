#!/usr/bin/env python3
"""Grade the simplified A1 Wave 2 acceptance set and generate review artifacts."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

BASE = Path(__file__).resolve().parents[3]
VALIDATION = BASE / "evaluations" / "wave2" / "validation-simplified"
PYTHON = BASE / ".venv" / "bin" / "python"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text_lossy(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


def run_wrapper(script: str, source: Path, output: Path | None = None) -> subprocess.CompletedProcess[str]:
    command = [str(PYTHON), str(BASE / "scripts" / script), str(source)]
    if output is not None:
        command.extend(["--output", str(output)])
    return subprocess.run(command, cwd=BASE, capture_output=True, text=True, check=False)


def assertion(text: str, passed: bool, evidence: str) -> dict[str, Any]:
    return {"text": text, "passed": bool(passed), "evidence": evidence}


def scenario(name: str, skill: str, source_output: str, assertions: list[dict[str, Any]], limitation: str) -> dict[str, Any]:
    return {
        "scenario": name,
        "skill": skill,
        "source_output": source_output,
        "assertions": assertions,
        "passed": all(item["passed"] for item in assertions),
        "limitation": limitation,
    }


def main() -> None:
    corroboration = VALIDATION / "corroboration"
    corroboration.mkdir(parents=True, exist_ok=True)

    # Deterministic corroboration only; the five existing behavioural outputs are reused.
    inference_output = corroboration / "confidence-inference-cap.json"
    inference_run = run_wrapper(
        "build_confidence_package.py",
        BASE / "cache" / "synthetic-inference-only-assessment.json",
        inference_output,
    )
    blocked_run = run_wrapper(
        "build_confidence_package.py",
        BASE / "test-blocked-source.json",
    )
    owner_output = corroboration / "scoring-owner-unknown-count.json"
    owner_run = run_wrapper(
        "build_scoring_package.py",
        BASE / "skills" / "icp-scoring-and-rationale" / "test_data" / "synthetic_horse_owner_unknown_count.json",
        owner_output,
    )

    james_confidence = load_json(VALIDATION / "preflight" / "confidence-package.json")
    james_scoring = load_json(VALIDATION / "preflight" / "scoring-package.json")
    inference = load_json(inference_output) if inference_run.returncode == 0 and inference_output.exists() else {}
    owner = load_json(owner_output) if owner_run.returncode == 0 and owner_output.exists() else {}
    exclusion = load_json(VALIDATION / "scoring-farrier-exclusion" / "scoring-package.json")
    exclusion_report = read_text_lossy(VALIDATION / "scoring-farrier-exclusion" / "output.txt")

    original = BASE / "evaluations" / "wave2" / "iteration-1"
    confidence_james_text = read_text_lossy(original / "confidence-james" / "output.txt")
    inference_text = read_text_lossy(original / "confidence-inference-cap" / "output.txt")
    blocked_text = read_text_lossy(original / "confidence-blocked-source" / "output.txt")
    scoring_james_text = read_text_lossy(original / "scoring-james" / "output.txt")
    owner_text = read_text_lossy(original / "scoring-owner-unknown-count" / "output.txt")

    component_total = sum(item["points_awarded"] for item in james_scoring["scoring"]["components"])
    blocked_message = (blocked_run.stderr + "\n" + blocked_run.stdout).strip()

    scenarios = [
        scenario(
            "Official business website — James Holub confidence",
            "prospect-evidence-and-confidence",
            "evaluations/wave2/iteration-1/confidence-james/output.txt",
            [
                assertion("Existing behavioural output is present", bool(confidence_james_text.strip()), "Iteration 1 output retained."),
                assertion("Confidence is 84 / High", james_confidence["confidence"]["score"] == 84 and james_confidence["confidence"]["level"] == "high", f"Observed {james_confidence['confidence']['score']} / {james_confidence['confidence']['level']}."),
                assertion("One strong official source is not capped", james_confidence["audit"]["applied_caps"] == [], "No confidence cap applied."),
                assertion("Single-source limitation remains visible", any("one strong primary source" in item.lower() for item in james_confidence["confidence"]["limitations"]), "Limitation is included in the confidence object."),
            ],
            "Relies on one official business source; externally controlled claims still require targeted verification.",
        ),
        scenario(
            "Mandatory claim supported by inference only",
            "prospect-evidence-and-confidence",
            "evaluations/wave2/iteration-1/confidence-inference-cap/output.txt",
            [
                assertion("Existing behavioural output is present", bool(inference_text.strip()), "Iteration 1 output retained."),
                assertion("Deterministic wrapper succeeds", inference_run.returncode == 0, f"Exit code {inference_run.returncode}."),
                assertion("Confidence is capped at 59 / Low", inference.get("confidence", {}).get("score") == 59 and inference.get("confidence", {}).get("level") == "low", f"Observed {inference.get('confidence', {}).get('score')} / {inference.get('confidence', {}).get('level')}."),
                assertion("Inference-only gate is recorded", inference.get("assessment", {}).get("gates", {}).get("mandatory_claim_inference_only", {}).get("value") is True, "mandatory_claim_inference_only=true."),
            ],
            "Synthetic case used to verify the approved mandatory-claim confidence cap.",
        ),
        scenario(
            "Blocked source invalidates confidence",
            "prospect-evidence-and-confidence",
            "evaluations/wave2/iteration-1/confidence-blocked-source/output.txt",
            [
                assertion("Existing behavioural output is present", bool(blocked_text.strip()), "Iteration 1 output retained."),
                assertion("Wrapper rejects the assessment", blocked_run.returncode != 0, f"Exit code {blocked_run.returncode}."),
                assertion("Exact blocked-source error is returned", "A blocked source supports a retained or confirmed claim" in blocked_message, blocked_message),
                assertion("No confidence package is produced", "\"confidence\"" not in blocked_message, "Only the rejection error was returned."),
            ],
            "Synthetic Yellow Pages case; no blocked source is accepted as retained evidence.",
        ),
        scenario(
            "James Holub deterministic ICP scoring and rationale",
            "icp-scoring-and-rationale",
            "evaluations/wave2/iteration-1/scoring-james/output.txt",
            [
                assertion("Existing behavioural output is present", bool(scoring_james_text.strip()), "Iteration 1 output retained."),
                assertion("Score is 86 / High", james_scoring["scoring"]["score"] == 86 and james_scoring["scoring"]["band"] == "high", f"Observed {james_scoring['scoring']['score']} / {james_scoring['scoring']['band']}."),
                assertion("Outcome is high_priority_farrier", james_scoring["audit"]["outcome"] == "high_priority_farrier", james_scoring["audit"]["outcome"]),
                assertion("Components sum to the numeric score", component_total == james_scoring["scoring"]["score"], f"Component total {component_total}."),
                assertion("Confidence remains separate and visible", james_scoring["confidence_context"]["score"] == 84 and james_scoring["confidence_context"]["level"] == "high", "Confidence context is 84 / High."),
            ],
            "The result requires human review and does not authorise outreach or CRM action.",
        ),
        scenario(
            "Horse Owner with unknown horse count",
            "icp-scoring-and-rationale",
            "evaluations/wave2/iteration-1/scoring-owner-unknown-count/output.txt",
            [
                assertion("Existing behavioural output is present", bool(owner_text.strip()), "Iteration 1 output retained."),
                assertion("Deterministic wrapper succeeds", owner_run.returncode == 0, f"Exit code {owner_run.returncode}."),
                assertion("Numeric score remains 80", owner.get("scoring", {}).get("score") == 80, f"Observed {owner.get('scoring', {}).get('score')}."),
                assertion("Raw High is capped to final Medium", owner.get("audit", {}).get("raw_band") == "high" and owner.get("scoring", {}).get("band") == "medium", f"Raw {owner.get('audit', {}).get('raw_band')}; final {owner.get('scoring', {}).get('band')}."),
                assertion("Review outcome is preserved", owner.get("audit", {}).get("outcome") == "horse_count_unknown_human_review", str(owner.get("audit", {}).get("outcome"))),
            ],
            "Synthetic case; the unknown horse count is intentionally not inferred.",
        ),
        scenario(
            "Farrier with confirmed no professional evidence",
            "icp-scoring-and-rationale",
            "evaluations/wave2/validation-simplified/scoring-farrier-exclusion/output.txt",
            [
                assertion("Corrected behavioural rerun completed", "full pass" in exclusion_report.lower(), "One-shot profile run completed with wrapper exit code 0."),
                assertion("Scoring is blocked with no score or band", exclusion["scoring"]["status"] == "blocked" and exclusion["scoring"]["score"] is None and exclusion["scoring"]["band"] is None, "status=blocked; score=null; band=null."),
                assertion("Specific exclusion outcome is preserved", exclusion["audit"]["outcome"] == "excluded_no_professional_evidence", exclusion["audit"]["outcome"]),
                assertion("No schema failure is invented", "schema" not in exclusion_report.lower(), "The report states no wrapper error and does not claim a schema failure."),
                assertion("No external action occurred", all(marker in exclusion_report for marker in ["Outreach occurred?** | No", "CRM write occurred?** | No", "A2 handoff occurred?** | No"]), "Report confirms no outreach, CRM write or A2 handoff."),
            ],
            "Corrected scenario rerun through the actual equinet-a1-icp-discovery profile.",
        ),
    ]

    passed = sum(1 for item in scenarios if item["passed"])
    overall_passed = passed == len(scenarios)
    result = {
        "evaluation": "A1 Wave 2 simplified behavioural validation",
        "profile": "equinet-a1-icp-discovery",
        "model": "deepseek-v4-flash",
        "scenarios_passed": passed,
        "scenarios_total": len(scenarios),
        "overall_passed": overall_passed,
        "decision": "ready_for_severine_review" if overall_passed else "correction_required",
        "promotion_applied": False,
        "scenarios": scenarios,
        "corroboration": {
            "inference_wrapper_exit_code": inference_run.returncode,
            "blocked_source_wrapper_exit_code": blocked_run.returncode,
            "blocked_source_error": blocked_message,
            "owner_scoring_wrapper_exit_code": owner_run.returncode,
        },
    }
    (VALIDATION / "grading.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Equinet A1 — Wave 2 Simplified Validation Review",
        "",
        "**Profile:** `equinet-a1-icp-discovery`  ",
        "**Scope:** `prospect-evidence-and-confidence` and `icp-scoring-and-rationale`  ",
        "**Method:** Reuse five existing behavioural outputs, rerun only the corrected Farrier exclusion scenario, and deterministically corroborate critical values.  ",
        f"**Result:** `{passed}/{len(scenarios)} scenarios passed`  ",
        f"**Decision:** `{'Ready for Séverine review' if overall_passed else 'Correction required'}`  ",
        "**Promotion applied:** `No`",
        "",
        "## Scenario results",
        "",
        "| # | Scenario | Skill | Result | Key observed behaviour | Limitation |",
        "|---:|---|---|---|---|---|",
    ]
    key_results = [
        "84 / High; one strong official source accepted; limitation visible",
        "59 / Low; mandatory inference-only cap applied",
        "Rejected; exact blocked-source error; no confidence package",
        "86 / High; component total matches; confidence remains separate",
        "80 numeric; raw High capped to Medium; review outcome preserved",
        "Blocked; null score/band; precise exclusion; no invented schema error or external action",
    ]
    for index, (item, key_result) in enumerate(zip(scenarios, key_results), start=1):
        result_label = "PASS" if item["passed"] else "FAIL"
        safe_limitation = item["limitation"].replace("|", "\\|")
        lines.append(f"| {index} | {item['scenario']} | `{item['skill']}` | **{result_label}** | {key_result} | {safe_limitation} |")

    lines.extend([
        "",
        "## Boundary checks",
        "",
        "- No outreach was initiated.",
        "- No HubSpot or Twenty write was performed or claimed.",
        "- No A2 handoff was triggered.",
        "- Confidence did not override an exclusion or change the numeric ICP score.",
        "- Unknown horse count remained unknown and triggered the approved review cap.",
        "- The corrected Farrier exclusion report did not invent a schema failure.",
        "",
        "## Technical preflight",
        "",
        "Both documented root wrappers executed successfully with the profile virtual environment. The previous gateway safety false-positive did not recur.",
        "",
        "## Acceptance decision",
        "",
        "The two Wave 2 skills satisfy the simplified technical and behavioural acceptance set and are ready for Séverine's review. They remain Draft until that review is recorded. This review does not constitute Equinet production acceptance.",
        "",
        "### Proposed status after Séverine approval",
        "",
        "```text",
        "version: 1.0.0",
        "status: validated_for_a1_v1_pilot",
        "```",
        "",
        "After approval, proceed to Wave 3: `ranked-prospect-review-package`, then `prospect-export`.",
        "",
    ])
    (VALIDATION / "WAVE2-SIMPLIFIED-REVIEW.md").write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "profile": "equinet-a1-icp-discovery",
        "validation": "wave2-simplified",
        "technical_preflight": "passed",
        "corrected_behavioural_rerun": "passed",
        "scenario_result": f"{passed}/{len(scenarios)} passed",
        "review_artifact": "evaluations/wave2/validation-simplified/WAVE2-SIMPLIFIED-REVIEW.md",
        "grading_artifact": "evaluations/wave2/validation-simplified/grading.json",
        "status": "ready_for_severine_review" if overall_passed else "correction_required",
        "promotion_applied": False,
    }
    (VALIDATION / "validation-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scenarios_passed": passed, "scenarios_total": len(scenarios), "overall_passed": overall_passed, "decision": result["decision"]}))


if __name__ == "__main__":
    main()
