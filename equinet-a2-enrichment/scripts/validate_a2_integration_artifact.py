#!/usr/bin/env python3
"""Validate an A2 integration artifact against a JSON Schema."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from jsonschema import Draft202012Validator
from a2_twenty_fullenrich_common import load_json,write_json_atomic
def main():
 ap=argparse.ArgumentParser();ap.add_argument('schema',type=Path);ap.add_argument('artifact',type=Path);ap.add_argument('--output',type=Path);a=ap.parse_args();schema=load_json(a.schema);artifact=load_json(a.artifact);errors=[{'path':'/'.join(str(x) for x in e.absolute_path),'message':e.message} for e in Draft202012Validator(schema).iter_errors(artifact)];result={'status':'valid' if not errors else 'invalid','schema_id':schema.get('$id'),'artifact':str(a.artifact),'errors':errors}
 if a.output:write_json_atomic(a.output,result)
 print(json.dumps(result,indent=2));return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
