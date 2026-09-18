#!/usr/bin/env python3
"""Promote Step 7 synthetic end-to-end acceptance."""
from __future__ import annotations
import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evaluations/step7';TECH=E/'technical-validation.json';REVIEW=E/'A2-STEP-7-REVIEW.md';DRAFT=E/'step7-draft-package-manifest.json';DET=E/'deterministic-acceptance.json';PROFILE=E/'profile-behavioural-result.json';FINAL=ROOT/'foundations/contracts/runtime/a2-step7-synthetic-acceptance-manifest-0.1.0.json';ACTIVE=ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json';SOUL=ROOT/'SOUL.md';ROADMAP=ROOT/'deliverables/A2-DELIVERY-STATUS-AND-ROADMAP.md';ACC=E/'acceptance-record.json';PROMO=E/'step7-promotion-manifest.json';AT='2026-08-29T21:31:10Z'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rep(t,o,n):
 if o not in t:raise RuntimeError(f'expected text not found: {o}')
 return t.replace(o,n,1)
def main():
 t=load(TECH);m=load(DRAFT);d=load(DET);p=load(PROFILE)
 if not t.get('pass') or t.get('status')!='ready_for_severine_review_not_approved' or not t.get('profile_invocation',{}).get('passed'):raise RuntimeError('Step 7 validation not ready')
 if not d.get('pass') or d.get('passed')!=6 or d.get('scenario_count')!=6:raise RuntimeError('Step 7 deterministic suite not ready')
 if m.get('status')!='ready_for_severine_review_not_approved':raise RuntimeError('Step 7 package status mismatch')
 for x in m['files']:
  q=ROOT/x['path']
  if not q.exists() or sha(q)!=x['sha256'] or q.stat().st_size!=x['bytes']:raise RuntimeError(f"draft hash mismatch: {x['path']}")
 snap=E/'pre-promotion'
 for q in [TECH,REVIEW,DET,PROFILE,SOUL,ROADMAP]:
  z=snap/q.relative_to(ROOT);z.parent.mkdir(parents=True,exist_ok=True)
  if not z.exists():shutil.copy2(q,z)
 t['status']='approved_synthetic_acceptance';t['approval_required']=False;t['promotion_performed']=True;t['next_gate_after_approval']='Step 8 — Bounded Real No-Integration Pilot Readiness';TECH.write_text(json.dumps(t,indent=2,ensure_ascii=False)+'\n')
 review=REVIEW.read_text();review=rep(review,'**Status:** `READY_FOR_SEVERINE_REVIEW_NOT_APPROVED`',f'**Status:** `APPROVED SYNTHETIC ACCEPTANCE`  \n**Approved by:** Séverine, Unitalk Operations  \n**Approved at:** `{AT}`');REVIEW.write_text(review)
 manifest={'manifest_id':'equinet-a2-step7-synthetic-acceptance','version':'0.1.0','status':'approved_synthetic_acceptance','approved_at':AT,'approved_by':{'name':'Séverine','role':'Unitalk Operations'},'approved_decisions':[f'S7-{n}' for n in range(1,11)],'deterministic_acceptance':{'path':str(DET.relative_to(ROOT)),'sha256':sha(DET),'scenarios':'6/6 pass'},'profile_invocation':{'path':str(PROFILE.relative_to(ROOT)),'sha256':sha(PROFILE),'status':'pass'},'operator_coverage':'14/14','exports':{'markdown':2,'csv':12,'xlsx':2},'external_calls':0,'external_actions':0,'real_data_authorized':False,'profile_status':'FOUNDATION CONFIGURED — NOT PILOT-READY','next_gate':'Step 8 — Bounded Real No-Integration Pilot Readiness'};FINAL.parent.mkdir(parents=True,exist_ok=True);FINAL.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
 soul=SOUL.read_text();anchor='- A2 Runtime Policy `0.1.0`, approved for synthetic local testing; upstream telemetry, fallback and real-data gates pending.'
 if 'Step 7 Synthetic Acceptance Manifest `0.1.0`' not in soul:soul=rep(soul,anchor,anchor+'\n- Step 7 Synthetic Acceptance Manifest `0.1.0`, approved; real-data pilot not authorised.')
 soul=rep(soul,'Step 6 model, tool, permission and quota configuration is approved for synthetic local testing only. The next delivery gate is Step 7 — Synthetic End-to-End Acceptance. Upstream telemetry, fallback verification, provider region/retention and real-data approval remain blocked. The profile remains **FOUNDATION CONFIGURED — NOT PILOT-READY**.','Step 7 synthetic end-to-end acceptance is approved. The next delivery gate is Step 8 — Bounded Real No-Integration Pilot Readiness. Upstream telemetry, fallback verification or disablement, provider region/retention, DPA evidence and named reviewers remain mandatory before real data. The profile remains **FOUNDATION CONFIGURED — NOT PILOT-READY**.');SOUL.write_text(soul)
 road=ROADMAP.read_text();road=rep(road,'**Version:** `1.2.9`','**Version:** `1.3.0`');road=rep(road,'**Next delivery gate:** `Step 7 — synthetic acceptance review and approval`','**Next delivery gate:** `Step 8 — Bounded Real No-Integration Pilot Readiness`');road=rep(road,'### Step 7 — Synthetic End-to-End Acceptance — READY FOR SÉVERINE REVIEW / NOT APPROVED','### Step 7 — Synthetic End-to-End Acceptance — COMPLETED / APPROVED');road=rep(road,'Review and approve or amend decisions **S7-1 through S7-10**. Step 8 remains blocked until its separate real-data, reviewer and provider-governance gates are satisfied.','Resolve and approve the Step 8 real-data activation gates before selecting or processing any Mustad/Equinet pilot records.');ROADMAP.write_text(road)
 subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/build_active_foundation_manifest.py')],cwd=ROOT,check=True)
 decisions=[f'S7-{n}' for n in range(1,11)];acc={'record_type':'step7_synthetic_acceptance','profile':'equinet-a2-enrichment','step':'7','decision':'approved_synthetic_acceptance','approver':{'name':'Séverine','role':'Unitalk Operations'},'approved_at':AT,'approved_decisions':decisions,'synthetic_acceptance_manifest':str(FINAL.relative_to(ROOT)),'synthetic_acceptance_manifest_sha256':sha(FINAL),'technical_validation':str(TECH.relative_to(ROOT)),'technical_validation_sha256':sha(TECH),'profile_invocation':str(PROFILE.relative_to(ROOT)),'profile_invocation_sha256':sha(PROFILE),'active_foundation_manifest':str(ACTIVE.relative_to(ROOT)),'active_foundation_manifest_sha256':sha(ACTIVE),'scenario_count':6,'operator_coverage':'14/14','external_actions':0,'real_data_authorized':False,'profile_status':'FOUNDATION CONFIGURED — NOT PILOT-READY','next_gate':'Step 8 — Bounded Real No-Integration Pilot Readiness'};ACC.write_text(json.dumps(acc,indent=2,ensure_ascii=False)+'\n')
 post=E/'post-promotion'
 for q,name in [(SOUL,'SOUL.md'),(ROADMAP,'A2-DELIVERY-STATUS-AND-ROADMAP.md')]:z=post/name;z.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(q,z)
 immutable=[FINAL,TECH,REVIEW,DET,PROFILE,ACC,post/'SOUL.md',post/'A2-DELIVERY-STATUS-AND-ROADMAP.md'];promo={'manifest_id':'equinet-a2-step7-promotion','version':'0.1.0','status':'approved_synthetic_acceptance','approved_decisions':decisions,'files':[{'path':str(q.relative_to(ROOT)),'bytes':q.stat().st_size,'sha256':sha(q)} for q in immutable],'active_foundation_manifest':{'path':str(ACTIVE.relative_to(ROOT)),'sha256':sha(ACTIVE)},'real_data_authorized':False,'external_actions':0};PROMO.write_text(json.dumps(promo,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'pass':True,'decision':acc['decision'],'scenarios':'6/6','operators':'14/14','real_data_authorized':False,'active_files':len(load(ACTIVE)['active_files']),'next_gate':acc['next_gate']},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
