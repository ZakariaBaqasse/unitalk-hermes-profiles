#!/usr/bin/env python3
"""Validate the semantic result of a Twenty apply/read-back operation."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import load_json,write_json_atomic
def main():
 ap=argparse.ArgumentParser();ap.add_argument('result',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();r=load_json(a.result);errors=[]
 if r.get('status')!='reconciled':errors.append('push result is not reconciled')
 if r.get('mismatches'):errors.append('read-back mismatches are present')
 if not r.get('receipts') and r.get('external_writes',0):errors.append('external writes lack operation receipts')
 out={'status':'valid' if not errors else 'invalid','write_plan_sha256':r.get('write_plan_sha256'),'external_writes':r.get('external_writes',0),'errors':errors};write_json_atomic(a.output,out);print(json.dumps(out,indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
