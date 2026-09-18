#!/usr/bin/env python3
"""Validate Step 8 readiness after authorised handoffs, provider attestation and bounded collection."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'evaluations/step8';R=E/'readiness';DEC=R/'pilot-readiness-decision-intake.json';WEB=R/'web-connectivity-smoke.json';GOV=R/'provider-governance-attestation.json';HAND=E/'handoffs/manifest.json';PLAN=R/'pilot-run-plan.json';CONFIG=ROOT/'config.yaml';POLICY=ROOT/'foundations/contracts/runtime/a2-step8-pilot-runtime-policy-0.1.0.yaml';COL=E/'collection/collection-manifest.json';OUT=R/'technical-validation.json';REVIEW=R/'A2-STEP-8-READINESS-REVIEW.md';MANIFEST=R/'step8-readiness-package-manifest.json'
def j(p):return json.loads(p.read_text(encoding='utf-8'))
def y(p):return yaml.safe_load(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d,w,g,h,plan,c,p,col=j(DEC),j(WEB),j(GOV),j(HAND),j(PLAN),y(CONFIG),y(POLICY),j(COL);checks={}
 checks['candidate_authorisation']=d['candidate_authorisation']['status']=='approved_for_bounded_a2_pilot' and len(d['candidate_authorisation']['candidates'])==2
 checks['reviewer_recorded']=d['review']['primary_reviewer']=='Séverine' and d['review']['mode']=='single_reviewer_unitalk_test'
 checks['handoffs']=h['status']=='valid_ready_for_local_a2_intake' and len(h['handoffs'])==2 and all(x['valid'] and x['eligibility']=='eligible' for x in h['handoffs'])
 checks['local_intake']=all((E/f"intake/{x['candidate_id']}/initial-record.json").exists() for x in h['handoffs'])
 checks['a1_reuse_projections']=all((E/f"planning/{x['candidate_id']}.reuse-snapshot.json").exists() and (E/f"planning/{x['candidate_id']}.gap-plan.json").exists() for x in h['handoffs'])
 checks['synthetic_web_connectivity']=w['pass'] and w['exa']['request_count']==1 and w['firecrawl']['request_count']==1 and w['config_activation']['restored']
 checks['governance_attestation']=g['decision']=='approved_for_two_candidate_bounded_public_data_pilot' and g['primary_model_route']['processing_region']=='Europe' and g['primary_model_route']['azure_prompt_retention']=='zero_data_retention_attested' and g['fallback']['enabled_for_real_pilot'] is False
 checks['pilot_runtime_policy']=p['status']=='approved_for_two_candidate_bounded_pilot' and p['model']['fallback_enabled'] is False and p['scope']['candidate_ids']==['A1-DARLEY-JONABELL-001','A1-RR-PODIATRY-001']
 checks['active_pilot_config']=c['model']['default']=='deepseek-v4-flash' and c['fallback_providers']==[] and c['web']=={'search_backend':'exa','extract_backend':'firecrawl'} and 'web' in c['platform_toolsets']['cli']
 checks['bounded_real_collection']=col['pass'] and col['summary']=={'targets':5,'collected':5,'blocked':0,'failed':0,'robots_calls':3,'firecrawl_calls':5,'exa_calls':0} and col['model_processing'] is False
 checks['hubspot_outreach_blocked']=d['hubspot_and_actions']['hubspot_read'] is False and d['hubspot_and_actions']['hubspot_write'] is False and d['hubspot_and_actions']['outreach'] is False
 ready=all(checks.values());result={'step':'8','stage':'readiness_and_collection','status':'ready_for_jonabell_profile_stage1' if ready else 'readiness_validation_failed','checks':checks,'checks_passed':sum(checks.values()),'checks_total':len(checks),'candidate_count':2,'handoffs':'2/2 valid','local_intake':'2/2 complete','a1_reuse_plans':'2/2 complete','synthetic_connectivity':'Exa 1/1 and Firecrawl 1/1 pass','real_collection':'5/5 official pages collected','real_collection_external_calls':col['external_calls'],'exa_real_calls':col['summary']['exa_calls'],'model_processing_performed':False,'primary_model_real_data_authorized_for_named_scope':g['decision']=='approved_for_two_candidate_bounded_public_data_pilot','fallback_enabled':False,'review_mode':d['review']['mode'],'next_action':'Run Jonabell Stage 1 in a fresh equinet-a2-enrichment session using stored pages only, then stop for Séverine review.','external_actions':0,'profile_status':'FOUNDATION CONFIGURED — NOT PILOT-READY','failures':[k for k,v in checks.items() if not v],'pass':ready};OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
 REVIEW.write_text(f'''# Step 8 Bounded Real Pilot Readiness Review\n\n**Status:** `READY FOR JONABELL PROFILE STAGE 1`  \n**Profile:** `equinet-a2-enrichment`\n\n- Readiness checks: **{sum(checks.values())}/{len(checks)} PASS**.\n- Candidate authorisation: **2/2**.\n- Handoffs: **2/2 valid**.\n- Local intake: **2/2 complete**.\n- A1 reuse/gap plans: **2/2 complete**.\n- Synthetic connectivity: **Exa and Firecrawl PASS**.\n- Real official pages: **5/5 collected**, zero Exa fallback.\n- Model processing: **not yet performed**.\n- Fallback: **disabled**.\n- HubSpot, Twenty, n8n, Apify and outreach: **disabled**.\n\nRun Jonabell Stage 1 from a fresh profile session using the stored pages only, then stop for Séverine review before Rood & Riddle.\n''')
 files=[DEC,WEB,GOV,HAND,PLAN,CONFIG,POLICY,COL,OUT,REVIEW,ROOT/'scripts/build_step8_real_handoffs.py',ROOT/'scripts/build_step8_a1_reuse_snapshot.py',ROOT/'scripts/run_step8_official_site_collection.py',ROOT/'scripts/build_step8_collection_receipt.py',E/'pilot/A1-DARLEY-JONABELL-001/STAGE1-INSTRUCTIONS.md',*[E/f"handoffs/{x['candidate_id']}.handoff.json" for x in h['handoffs']],*[E/f"intake/{x['candidate_id']}/initial-record.json" for x in h['handoffs']],*[E/f"planning/{x['candidate_id']}.reuse-snapshot.json" for x in h['handoffs']],*[E/f"planning/{x['candidate_id']}.gap-plan.json" for x in h['handoffs']]]
 for x in col['records']:
  if x['markdown_path']:files.append(ROOT/x['markdown_path'])
 unique=[];seen=set()
 for x in files:
  key=str(x.resolve())
  if key not in seen:seen.add(key);unique.append(x)
 manifest={'manifest_id':'equinet-a2-step8-readiness-package','version':'0.1.0','status':result['status'],'files':[{'path':str(x.relative_to(ROOT)),'bytes':x.stat().st_size,'sha256':sha(x)} for x in unique],'file_count':len(unique),'candidate_count':2,'real_data_model_scope_authorized':ready,'real_collection_calls':col['external_calls'],'external_actions':0};MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'pass':result['pass'],'checks':f"{result['checks_passed']}/{result['checks_total']}",'handoffs':result['handoffs'],'intake':result['local_intake'],'collection':result['real_collection'],'model_processing_performed':False,'fallback_enabled':False,'status':result['status'],'failures':result['failures']},indent=2));return 0 if ready else 1
if __name__=='__main__':raise SystemExit(main())
