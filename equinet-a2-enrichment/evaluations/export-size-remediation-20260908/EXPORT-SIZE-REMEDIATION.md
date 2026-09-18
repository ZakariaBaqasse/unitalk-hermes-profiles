# A2 Profile Export Size Remediation

**Profile:** `equinet-a2-enrichment`  
**Completed at:** `2026-09-08T12:53:13Z`  
**Status:** `COMPLETED — RUNTIME AND EXTRACTED EXPORT VERIFIED`

## Change summary

- Removed the OCR-only dependency stack from the active A2 Python environment.
- Rebuilt `.venv` with the eight pinned packages required by active A2 scripts.
- Moved `scripts/ocr_hubspot_data_model.py` to `evaluations/hubspot-intake/historical-tools/ocr_hubspot_data_model.py`.
- Preserved the historical OCR output and its source manifest.
- Updated `foundations/contracts/requirements-foundation.txt` to match the installed runtime exactly.

## Size result before export

| Measure | Before | After |
|---|---:|---:|
| Active profile apparent size | 401.84 MiB | 52.89 MiB |
| `.venv` apparent size | 374.15 MiB | 24.93 MiB |
| Installed distributions | 20 | 8 |

The removed OCR stack included RapidOCR, OpenCV, ONNX Runtime, NumPy, Pillow, Shapely, PyClipper and their OCR-only dependencies. No OCR package marker remains in the active `.venv`.

## Runtime verification

- Dependency compatibility: PASS (`uv pip check`; 8/8 installed distributions compatible).
- Current A2 amendment validation: PASS, 47/47 checks.
- Farrier review workflow: PASS, 14/14 operators, 0 external calls, 0 external actions.
- Horse-owner requalification workflow: PASS, 14/14 operators, 0 external calls, 0 external actions.
- Active foundation hashes: PASS.
- Review-package generation, including XLSX output: PASS in both workflows.

## Historical regression note

A rerun of the historical Step 9B suite produced 10/11 passing executions. The remaining execution passed all 59 behavioural cases but failed two historical hash assertions because `validate_a2_enrichment_record.py` was legitimately revised after that acceptance snapshot. The original accepted Step 9 evidence was restored unchanged from the pre-remediation profile export. It remains 10/10 controls PASS and the final Step 9 release remains 17/17 controls PASS.

## Scope and safety

- No CRM write, outreach, provider call or other external business action was performed.
- The active A2 profile remains `pilot_ready_no_integration`.
- OCR is not part of A2's active runtime and can only be rerun from the archived utility in a separate temporary environment.
- The pre-remediation OCR environment was retained outside the profile until archive verification completed, then removed.

## Export verification

- Clean profile export: `equinet-a2-enrichment-2026-09-08-clean.tar.gz`.
- Compressed size before final report refresh: 8.12 MiB.
- Unsafe archive paths: 0.
- Credential files (`.env`, `auth.json`): 0.
- OCR binary/package members: 0.
- Extracted runtime imports: PASS.
- Current A2 amendment validation from extracted archive: PASS.
- Farrier workflow from extracted archive: PASS.
