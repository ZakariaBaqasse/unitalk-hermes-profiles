#!/usr/bin/env python3
"""Validate the Step 10 implementation manifest and activation gates."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];M=ROOT/'foundations/contracts/runtime/a2-step10-implementation-manifest-0.1.0.json'
def main():
 m=json.loads(M.read_text());errors=[]
 for item in m.get('artifacts',[]):
  p=ROOT/item['path']
  if not p.is_file():errors.append(f"missing: {item['path']}");continue
  if hashlib.sha256(p.read_bytes()).hexdigest()!=item['sha256']:errors.append(f"hash mismatch: {item['path']}")
 implementation_valid=not errors and m.get('acceptance',{}).get('status')=='pass_with_live_fullenrich_pending'
 activation_ready=implementation_valid and not m.get('remaining_gates') and not m.get('active_manifest_hash_drift')
 result={'implementation_valid':implementation_valid,'activation_ready':activation_ready,'artifact_count':m.get('artifact_count'),'errors':errors,'activation_blocks':m.get('remaining_gates',[])+([f"active manifest drift: {len(m.get('active_manifest_hash_drift',[]))} files"] if m.get('active_manifest_hash_drift') else [])}
 print(json.dumps(result,indent=2));return 0 if implementation_valid else 1
if __name__=='__main__':raise SystemExit(main())
