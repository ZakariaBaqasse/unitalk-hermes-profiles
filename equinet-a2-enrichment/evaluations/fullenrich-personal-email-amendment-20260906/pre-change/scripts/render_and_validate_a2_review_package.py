#!/usr/bin/env python3
"""Render and independently validate one lossless A2 review package."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_wave3_contracts import ROOT,load
from render_a2_review_views import DEFAULT_SPEC,render_bundle
from validate_step2h_review_views import validate_sample

def build(record:Path,output:Path,previous:Path|None,spec_path:Path)->dict:
 manifest=render_bundle(record,output,previous,spec_path);spec=load(spec_path);sample={'name':'wave3-runtime','record':record,'previous':previous,'output':output};validation=validate_sample(sample,spec)
 return {'command':'a2-render-review-package','version':'0.1.0-draft.1','valid':validation['passed'],'output_dir':str(output),'canonical_record_sha256':manifest['canonical_record_sha256'],'row_counts':manifest['row_counts'],'manifest_path':str(output/'manifest.json'),'review_validation':validation,'read_only':True,'external_actions':0,'errors':validation['errors']}
def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('record',type=Path);p.add_argument('--previous-record',type=Path);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--spec',type=Path,default=DEFAULT_SPEC);p.add_argument('--result',type=Path);a=p.parse_args()
 try:r=build(a.record,a.output_dir,a.previous_record,a.spec)
 except Exception as e:r={'command':'a2-render-review-package','version':'0.1.0-draft.1','valid':False,'output_dir':str(a.output_dir),'read_only':True,'external_actions':0,'errors':[str(e)]}
 text=json.dumps(r,indent=2,ensure_ascii=False)+'\n'
 if a.result:a.result.parent.mkdir(parents=True,exist_ok=True);a.result.write_text(text,encoding='utf-8')
 print(text,end='');return 0 if r['valid'] else 1
if __name__=='__main__':raise SystemExit(main())
