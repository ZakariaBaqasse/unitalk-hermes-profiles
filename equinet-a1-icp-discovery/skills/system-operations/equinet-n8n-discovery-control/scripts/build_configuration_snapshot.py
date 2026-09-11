#!/usr/bin/env python3
"""Build an immutable, non-secret configuration snapshot for one A1 run."""
from __future__ import annotations
import argparse, hashlib, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

PROFILE = Path(__file__).resolve().parents[4]
FILES = [
    "configurations/icp/equinet-icp-v1.yaml",
    "configurations/geography/location-resolution-v1.json",
    "configurations/evidence/public-website-enrichment-policy-v1.yaml",
    "configurations/evidence/evidence-confidence-rules-v1.yaml",
    "configurations/scoring/icp-scoring-model-v1.yaml",
    "configurations/operations/a1-runtime-policy-v1.yaml",
    "configurations/sources/approved-source-register-v1.yaml",
    "skills/a1-prospect-data-contract/references/prospect-candidate.schema.json",
    "skills/post-n8n-public-website-enrichment/references/enrichment-state-v2.schema.json",
    "skills/post-n8n-public-website-enrichment/references/enrichment-results.schema.json",
    "skills/post-n8n-public-website-enrichment/references/assessment-submissions-v2.schema.json",
    "skills/post-n8n-public-website-enrichment/references/explicit-fallback-v2.schema.json",
    "skills/post-n8n-public-website-enrichment/references/staging-overlays.schema.json",
    "skills/post-n8n-public-website-enrichment/scripts/manage_enrichment.py",
    "skills/post-n8n-public-website-enrichment/scripts/route_and_overlay.py",
    "skills/prospect-segment-classification/scripts/validate_classification.py",
    "skills/equinet-icp-qualification/scripts/build_qualification.py",
    "skills/prospect-evidence-and-confidence/scripts/build_confidence_package.py",
    "skills/icp-scoring-and-rationale/scripts/build_scoring_package.py",
    "skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_company.py",
    "skills/crm/evidence-aware-crm-staging/scripts/stage_twenty_rest.py"
]

def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def atomic_json(path: Path, value: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp=path.with_name(f".{path.name}.tmp.{os.getpid()}")
    with temp.open("w",encoding="utf-8") as handle:
        handle.write(json.dumps(value,indent=2,sort_keys=True)+"\n"); handle.flush(); os.fsync(handle.fileno())
    os.replace(temp,path)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",required=True,type=Path)
    parser.add_argument("--monitor-identity",required=True)
    parser.add_argument("--cron-model",default="gpt-5.6-terra")
    parser.add_argument("--cron-provider",default="openai-api")
    args=parser.parse_args()
    missing=[]; hashes={}
    for relative in FILES:
        path=PROFILE/relative
        if not path.is_file(): missing.append(relative); continue
        hashes[relative]=hashlib.sha256(path.read_bytes()).hexdigest()
    if missing:
        print(json.dumps({"status":"error","missing":missing,"lead_rows_emitted":False}),file=sys.stderr); return 1
    snapshot={"schema_version":"equinet.a1.configuration-snapshot.v1","created_at":utc_now(),"monitor_identity":args.monitor_identity,"cron_model":args.cron_model,"cron_provider":args.cron_provider,"files":hashes}
    atomic_json(args.output,snapshot)
    print(json.dumps({"status":"created","output":str(args.output),"file_count":len(hashes),"lead_rows_emitted":False},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
