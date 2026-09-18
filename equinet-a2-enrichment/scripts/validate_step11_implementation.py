#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,py_compile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'foundations/contracts/runtime/a2-step11-implementation-manifest-0.1.0.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d=json.loads(P.read_text());errors=[]
 for x in d.get('artifacts',[]):
  p=ROOT/x['path']
  if not p.is_file():errors.append(f'missing: {x["path"]}')
  elif sha(p)!=x['sha256']:errors.append(f'hash mismatch: {x["path"]}')
 if d.get('missing'):errors.extend(f'manifest missing: {x}' for x in d['missing'])
 if d.get('compile_errors'):errors.extend(d['compile_errors'])
 if (d.get('acceptance') or {}).get('status')!='pass':errors.append('Step 11 acceptance did not pass')
 out={'implementation_valid':not errors,'activation_ready':False,'artifact_count':d.get('artifact_count'),'errors':errors,'activation_blocks':d.get('activation_blocks') or []};print(json.dumps(out,indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
