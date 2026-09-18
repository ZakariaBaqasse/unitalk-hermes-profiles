#!/usr/bin/env python3
"""Repair Step 5E promoted validation evidence after an approved-state replay."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evaluations/step5e';TECH=E/'technical-validation.json';REVIEW=E/'A2-STEP-5-CLOSURE-REVIEW.md';ACC=E/'acceptance-record.json';PROMO=E/'step5e-promotion-manifest.json';AT='2026-08-29T17:26:25Z'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 t=load(TECH)
 if not t.get('pass') or t.get('deterministic_replay')!={'passed':58,'total':58} or t.get('behavioural_replay')!={'passed':10,'total':10}:raise RuntimeError('current Step 5E validation is not truthful')
 t['status']='approved_and_promoted';t['approval_required']=False;t['promotion_performed']=True;t['next_gate_after_approval']='Step 6 — Model, Tools, Permissions and Quotas';TECH.write_text(json.dumps(t,indent=2,ensure_ascii=False)+'\n')
 text=REVIEW.read_text()
 if 'READY FOR SÉVERINE REVIEW — NOT APPROVED' in text:text=text.replace('**Status:** `READY FOR SÉVERINE REVIEW — NOT APPROVED`',f'**Status:** `APPROVED AND PROMOTED`  \n**Approved by:** Séverine, Unitalk Operations  \n**Approved at:** `{AT}`',1)
 text=text.replace('Approval closes Step 5 and authorises Step 6 configuration. It does not make the profile pilot-ready or enable integrations.','Step 5 is approved and closed. Step 6 configuration is authorised. This does not make the profile pilot-ready or enable integrations.')
 REVIEW.write_text(text)
 a=load(ACC);a['technical_validation_sha256']=sha(TECH);ACC.write_text(json.dumps(a,indent=2,ensure_ascii=False)+'\n')
 p=load(PROMO)
 for x in p['files']:
  path=ROOT/x['path'];x['bytes']=path.stat().st_size;x['sha256']=sha(path)
 PROMO.write_text(json.dumps(p,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'pass':True,'technical':sha(TECH),'review':sha(REVIEW),'acceptance':sha(ACC),'promotion':sha(PROMO)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
