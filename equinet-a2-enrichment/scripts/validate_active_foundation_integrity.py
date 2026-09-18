#!/usr/bin/env python3
"""Validate the active A2 foundation using SHA-256 over exact raw bytes."""
from __future__ import annotations
import argparse,hashlib,json,py_compile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json'
def sha(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def main()->int:
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=Path,default=DEFAULT);ap.add_argument('--output',type=Path);a=ap.parse_args();m=json.loads(a.manifest.read_text(encoding='utf-8'));errors=[];compiled=[]
 rows=m.get('active_files',[])
 if m.get('active_file_count')!=len(rows):errors.append('active_file_count mismatch')
 seen=set()
 for item in rows:
  rel=item.get('path')
  if rel in seen:errors.append(f'duplicate active path: {rel}');continue
  seen.add(rel);p=ROOT/rel
  if not p.is_file():errors.append(f'missing: {rel}');continue
  if p.stat().st_size!=item.get('bytes'):errors.append(f'byte-size mismatch: {rel}')
  if sha(p)!=item.get('sha256'):errors.append(f'hash mismatch: {rel}')
  if p.suffix=='.py':
   try:py_compile.compile(str(p),doraise=True);compiled.append(rel)
   except Exception as e:errors.append(f'python syntax error: {rel}: {e}')
 runtime=m.get('runtime_policy') or {};rp=ROOT/runtime.get('path','')
 if not rp.is_file() or sha(rp)!=runtime.get('sha256'):errors.append('runtime_policy reference mismatch')
 req=m.get('profile_runtime_requirements') or {};rq=ROOT/req.get('path','')
 if not rq.is_file() or sha(rq)!=req.get('sha256'):errors.append('profile_runtime_requirements reference mismatch')
 if 'config.yaml' in seen:errors.append('mutable config.yaml must not be in active immutable hash set')
 integration=m.get('integration_validation') or {};step=integration.get('step10_manifest') or {}
 if step:
  sp=ROOT/step.get('path','')
  if not sp.is_file() or sha(sp)!=step.get('sha256'):errors.append('Step 10 implementation manifest reference mismatch')
  else:
   nested=json.loads(sp.read_text(encoding='utf-8'))
   for item in nested.get('artifacts',[]):
    np=ROOT/item.get('path','')
    if not np.is_file():errors.append(f"missing Step 10 artifact: {item.get('path')}")
    elif sha(np)!=item.get('sha256'):errors.append(f"Step 10 artifact hash mismatch: {item.get('path')}")
 result={'record_type':'a2_active_foundation_integrity_validation','manifest_version':m.get('version'),'status':'pass' if not errors else 'fail','active_file_count':len(rows),'python_files_compiled':len(compiled),'hash_algorithm':'sha256_raw_file_bytes','errors':errors,'external_actions':0}
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(result,indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
