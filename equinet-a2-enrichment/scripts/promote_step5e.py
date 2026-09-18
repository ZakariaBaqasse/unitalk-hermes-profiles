#!/usr/bin/env python3
"""Promote approved Step 5E consolidated A2 runtime."""
from __future__ import annotations
import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evaluations/step5e';TECH=E/'technical-validation.json';REVIEW=E/'A2-STEP-5-CLOSURE-REVIEW.md';DRAFT=E/'step5e-draft-package-manifest.json';DRAFT_RUNTIME=ROOT/'foundations/contracts/skills/a2-step5-runtime-manifest-0.1.0-draft.1.json';FINAL_RUNTIME=ROOT/'foundations/contracts/skills/a2-step5-runtime-manifest-0.1.0.json';ORCH=ROOT/'scripts/run_a2_no_integration_workflow.py';ACTIVE=ROOT/'foundations/contracts/A2-ACTIVE-FOUNDATION-MANIFEST.json';SOUL=ROOT/'SOUL.md';ROADMAP=ROOT/'deliverables/A2-DELIVERY-STATUS-AND-ROADMAP.md';ACC=E/'acceptance-record.json';PROMO=E/'step5e-promotion-manifest.json';AT='2026-08-29T17:26:25Z'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rep(t,o,n):
 if o not in t:raise RuntimeError(f'expected text not found: {o}')
 return t.replace(o,n,1)
def main():
 tech=load(TECH);draft=load(DRAFT)
 if not tech.get('pass') or tech.get('deterministic_replay')!={'passed':58,'total':58} or tech.get('behavioural_replay')!={'passed':10,'total':10}:raise RuntimeError('Step 5E validation not ready')
 if not all(x.get('passed') for x in tech.get('workflow_scenarios',[])) or len(tech.get('workflow_scenarios',[]))!=2:raise RuntimeError('workflow scenarios not ready')
 if draft.get('status')!='ready_for_severine_review_not_approved' or draft.get('promotion_performed') is not False:raise RuntimeError('draft state invalid')
 for x in draft['files']:
  p=ROOT/x['path']
  if not p.exists() or sha(p)!=x['sha256'] or p.stat().st_size!=x['bytes']:raise RuntimeError(f"draft integrity mismatch: {x['path']}")
 snap=E/'pre-promotion'
 for p in [DRAFT_RUNTIME,ORCH,SOUL,ROADMAP,REVIEW]:
  d=snap/p.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True)
  if not d.exists():shutil.copy2(p,d)
 text=ORCH.read_text();text=rep(text,"'version':'0.1.0-draft.1'","'version':'0.1.0'");ORCH.write_text(text)
 runtime=load(DRAFT_RUNTIME);runtime['version']='0.1.0';runtime['status']='approved_local_no_integration';runtime['approved_at']=AT;runtime['approved_by']={'name':'Séverine','role':'Unitalk Operations'};runtime['approved_decisions']=[f'5E-{n}' for n in range(1,11)];runtime['orchestrator']['sha256']=sha(ORCH);runtime['orchestrator']['status']='active_local_no_integration';runtime['next_gate']='Step 6 — Model, Tools, Permissions and Quotas';FINAL_RUNTIME.write_text(json.dumps(runtime,indent=2,ensure_ascii=False)+'\n')
 review=REVIEW.read_text();review=rep(review,'**Status:** `READY FOR SÉVERINE REVIEW — NOT APPROVED`',f'**Status:** `APPROVED AND PROMOTED`  \n**Approved by:** Séverine, Unitalk Operations  \n**Approved at:** `{AT}`');REVIEW.write_text(review)
 soul=SOUL.read_text();anchor='- Wave 3 Runtime Manifest `0.1.0`, approved for local no-integration use.'
 if 'Consolidated Step 5 Runtime Manifest `0.1.0`' not in soul:soul=rep(soul,anchor,anchor+'\n- Consolidated Step 5 Runtime Manifest `0.1.0`, approved for local no-integration use.')
 soul=rep(soul,'Waves 1, 2 and 3 are approved for local no-integration use. The next delivery gate is Step 5E — Full Operational Skills Regression and No-Integration Workflow. Until runtime controls, synthetic end-to-end acceptance and a bounded pilot are completed, remain **FOUNDATION CONFIGURED — NOT PILOT-READY**.','Step 5 operational skills and the local no-integration workflow are approved. The next delivery gate is Step 6 — Model, Tools, Permissions and Quotas. Until runtime controls, synthetic end-to-end acceptance and a bounded pilot are completed, remain **FOUNDATION CONFIGURED — NOT PILOT-READY**.');SOUL.write_text(soul)
 road=ROADMAP.read_text();road=rep(road,'**Version:** `1.2.4`','**Version:** `1.2.5`');road=rep(road,'**Next delivery gate:** `Step 5E — Step 5 closure review and approval`','**Next delivery gate:** `Step 6 — Model, Tools, Permissions and Quotas`');road=rep(road,'### Step 5E — Full Operational Skills Regression and No-Integration Workflow — READY FOR SÉVERINE REVIEW / NOT APPROVED','### Step 5E — Full Operational Skills Regression and No-Integration Workflow — COMPLETED / APPROVED');road=rep(road,"- Step 5 closure is pending Séverine's explicit approval of 5E-1 through 5E-10.",f'- Séverine approved 5E-1 through 5E-10 on `{AT}`; Step 5 is closed and Step 6 is authorised.');road=rep(road,'Review and approve or amend decisions **5E-1 through 5E-10**. After approval, freeze the consolidated Step 5 runtime, activate the no-integration orchestrator and open **Step 6 — Model, Tools, Permissions and Quotas**.','Build and validate **Step 6 — Model, Tools, Permissions and Quotas**, then present the Step 6 review for approval.');ROADMAP.write_text(road)
 subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/build_active_foundation_manifest.py')],cwd=ROOT,check=True)
 acc={'record_type':'step5_closure_acceptance','profile':'equinet-a2-enrichment','step':'5E','decision':'approved_and_promoted','approver':{'name':'Séverine','role':'Unitalk Operations'},'approved_at':AT,'approved_decisions':[f'5E-{n}' for n in range(1,11)],'runtime_manifest':str(FINAL_RUNTIME.relative_to(ROOT)),'runtime_manifest_sha256':sha(FINAL_RUNTIME),'technical_validation':str(TECH.relative_to(ROOT)),'technical_validation_sha256':sha(TECH),'active_foundation_manifest':str(ACTIVE.relative_to(ROOT)),'active_foundation_manifest_sha256':sha(ACTIVE),'skills':10,'operators':14,'deterministic_replay':'58/58 pass','behavioural_replay':'10/10 pass','workflow_scenarios':'2/2 pass','external_calls':0,'external_actions':0,'profile_status':'FOUNDATION CONFIGURED — NOT PILOT-READY','next_gate':'Step 6 — Model, Tools, Permissions and Quotas'};ACC.write_text(json.dumps(acc,indent=2,ensure_ascii=False)+'\n')
 post=E/'post-promotion'
 for p,name in [(SOUL,'SOUL.md'),(ROADMAP,'A2-DELIVERY-STATUS-AND-ROADMAP.md')]:d=post/name;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
 immutable=[FINAL_RUNTIME,ORCH,TECH,REVIEW,ACC,post/'SOUL.md',post/'A2-DELIVERY-STATUS-AND-ROADMAP.md'];promo={'manifest_id':'equinet-a2-step5e-promotion','version':'0.1.0','status':'approved_and_promoted','approved_decisions':[f'5E-{n}' for n in range(1,11)],'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in immutable],'active_foundation_manifest':{'path':str(ACTIVE.relative_to(ROOT)),'sha256':sha(ACTIVE)},'external_actions':0};PROMO.write_text(json.dumps(promo,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'pass':True,'decision':'approved_and_promoted','skills':10,'operators':14,'active_files':len(load(ACTIVE)['active_files']),'next_gate':acc['next_gate'],'external_actions':0},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
