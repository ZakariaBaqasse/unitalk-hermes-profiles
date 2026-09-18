#!/usr/bin/env python3
"""Shared strict JSON and active-foundation helpers for A2 Wave 3."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
from typing import Any
ROOT=Path(__file__).resolve().parents[1]
ACTIVE=ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json'
class ContractError(ValueError): pass
def _pairs(pairs):
 out={}
 for k,v in pairs:
  if k in out: raise ContractError(f'duplicate JSON key: {k}')
  out[k]=v
 return out
def _constant(v): raise ContractError(f'non-finite JSON number is not allowed: {v}')
def load(path:Path)->dict[str,Any]:
 try:v=json.loads(path.read_text(encoding='utf-8'),object_pairs_hook=_pairs,parse_constant=_constant)
 except (OSError,UnicodeError,json.JSONDecodeError) as e: raise ContractError(f'cannot read valid JSON from {path}: {e}') from e
 if not isinstance(v,dict): raise ContractError('JSON root must be an object')
 return v
def sha_file(path:Path)->str:return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical_bytes(v:Any)->bytes:return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def canonical_hash(v:Any)->str:return hashlib.sha256(canonical_bytes(v)).hexdigest()
def load_active(rel:str)->dict[str,Any]:
 m=load(ACTIVE);idx={x['path']:x for x in m.get('active_files',[])};e=idx.get(rel);p=ROOT/rel
 if not e: raise ContractError(f'dependency is not active: {rel}')
 if not p.is_file() or sha_file(p)!=e['sha256']: raise ContractError(f'active dependency hash mismatch: {rel}')
 return load(p)
