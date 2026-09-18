#!/usr/bin/env python3
"""Run the approved A2 workflow locally with synthetic fixtures and no integrations."""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PY=ROOT/'.venv/bin/python'
W1=ROOT/'evaluations/step5b/fixtures/wave1-cases.json';W2=ROOT/'evaluations/step5c/fixtures/wave2-cases.json';W3=ROOT/'evaluations/step5d/fixtures/wave3-cases.json'
OPERATORS=['a2-intake','a2-normalise-resolve-entities','a2-duplicate-eligibility','a2-build-gap-plan','a2-evaluate-minimum-package','a2-source-preflight','a2-social-link-classifier','a2-normalise-validate-observations','a2-evaluate-evidence-confidence','a2-evaluate-protected-field-action','a2-create-revision','a2-render-review-package','a2-twenty-review','a2-governed-handoff']
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--scenario',choices=['farrier_review','horse_owner_requalification'],default='farrier_review');ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True);f1=load(W1);f2=load(W2);f3=load(W3);steps=[];coverage=[]
 def write(name,obj):p=a.output_dir/f'{name}.input.json';p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n');return p
 def run(name,args,expected=(0,),output_file=None):
  p=subprocess.run([str(PY),*args],cwd=ROOT,capture_output=True,text=True);data=None
  if output_file and output_file.exists():data=load(output_file)
  else:
   try:data=json.loads(p.stdout)
   except Exception:data={'stdout':p.stdout,'stderr':p.stderr}
  ok=p.returncode in expected;steps.append({'operator':name,'return_code':p.returncode,'passed':ok,'output_reference':str(output_file or '')});coverage.append(name);return data,ok
 handoff=ROOT/('evaluations/step2g/fixtures/inputs/horse-owner-handoff.json' if a.scenario=='horse_owner_requalification' else 'evaluations/step2g/fixtures/inputs/farrier-handoff.json');intake_out=a.output_dir/'initial-record.json';ledger=a.output_dir/'intake-ledger.json';_,_=run('a2-intake',['scripts/a2_intake.py',str(handoff),'--output',str(intake_out),'--ledger',str(ledger)])
 entity_case=f1['entity_resolution_cases'][0];p=write('entity',entity_case['request']);entity_out=a.output_dir/'entity.json';run('a2-normalise-resolve-entities',['scripts/normalise_and_resolve_a2_entities.py',str(p),'--output',str(entity_out)])
 elig_case=next(x for x in f1['eligibility_cases'] if x['name']=='synthetic-hubspot-unavailable-can-continue');p=write('eligibility',elig_case['request']);elig_out=a.output_dir/'eligibility.json';run('a2-duplicate-eligibility',['scripts/evaluate_a2_duplicate_eligibility.py',str(p),'--output',str(elig_out)])
 gap_case=next(x for x in f2['gap_cases'] if x['name']==('horse-owner-required-gap' if a.scenario=='horse_owner_requalification' else 'complete-farrier-no-research'));gap_request=dict(gap_case['request']);
 if gap_request.get('contact_path')=='general_organisation_fallback':gap_request['contact_path']='contact_needed'
 p=write('gap',gap_request);gap_out=a.output_dir/'gap-plan.json';run('a2-build-gap-plan',['scripts/build_a2_gap_plan.py',str(p),'--output',str(gap_out)])
 snapshot=gap_request;p=write('minimum-package',snapshot);min_out=a.output_dir/'minimum-package.json';run('a2-evaluate-minimum-package',['scripts/evaluate_a2_minimum_package.py',str(p),'--packages','foundations/contracts/business/a2-minimum-data-packages-0.3.1.json','--output',str(min_out)])
 source_case=f2['source_cases'][0];preq=dict(source_case['request']);preq.update({'actor_profile':'equinet-a2-enrichment','trigger':'Step 5E synthetic workflow','requested_at':'2026-08-28T10:00:00Z','run_id':f'STEP5E-{a.scenario}'});p=write('source-preflight',preq);pre_out=a.output_dir/'source-preflight.json';receipt,_=run('a2-source-preflight',['scripts/preflight_a2_source_action.py',str(p),'--output',str(pre_out)],output_file=pre_out)
 social={'source':'prospect_official_website','explicitly_linked':True,'url':'https://www.linkedin.com/company/example-farrier-services/','page_context':'organisation','named_role_gap':True};p=write('social-link',social);social_out=a.output_dir/'social-link.json';run('a2-social-link-classifier',['scripts/classify_official_site_social_link.py',str(p)])
 obs_case=f2['observation_cases'][0];obs=load(write('obs-copy',obs_case['request']));
 for index,item in enumerate(obs['observations'],1):
  oreq=dict(preq);oreq['field_key']=item['field_key'];oreq['named_need']=f"Verify {item['field_key']}";op=write(f'observation-preflight-{index}',oreq);oo=a.output_dir/f'observation-preflight-{index}.json';oreceipt,_=run('a2-source-preflight',['scripts/preflight_a2_source_action.py',str(op),'--output',str(oo)],output_file=oo);item['source_preflight']=oreceipt
 p=write('observations',obs);obs_out=a.output_dir/'observations.json';run('a2-normalise-validate-observations',['scripts/normalise_and_validate_a2_observations.py',str(p),'--output',str(obs_out)])
 ev=dict(f3['evidence_cases'][0]['request']);ev['source_preflight']=receipt;p=write('evidence',ev);ev_out=a.output_dir/'evidence.json';run('a2-evaluate-evidence-confidence',['scripts/evaluate_a2_evidence_confidence.py',str(p),'--output',str(ev_out)])
 prot=f3['protected_cases'][0]['request'];p=write('protected',prot);prot_out=a.output_dir/'protected.json';run('a2-evaluate-protected-field-action',['scripts/evaluate_a2_protected_field_action.py',str(p),'--output',str(prot_out)])
 rec=f3['records'];rev_prev=ROOT/rec['review_previous'];rev_current=ROOT/rec['review_current'];prev=rev_prev;current=rev_current
 if a.scenario=='horse_owner_requalification':prev=ROOT/rec['requalification_previous'];current=ROOT/rec['requalification_current']
 rev_out=a.output_dir/'revision.json';run('a2-create-revision',['scripts/create_a2_revision.py',str(rev_prev),str(rev_current),'--output',str(rev_out)])
 review_dir=a.output_dir/'review-package';review_result=a.output_dir/'review-result.json';run('a2-render-review-package',['scripts/render_and_validate_a2_review_package.py',str(current),'--previous-record',str(prev),'--output-dir',str(review_dir),'--result',str(review_result)],output_file=review_result)
 twenty_out=a.output_dir/'twenty-preparation.json';run('a2-twenty-review',['scripts/build_and_validate_a2_twenty_review.py','prepare',str(current),'--output',str(twenty_out)],output_file=twenty_out)
 dest='a1_requalification' if a.scenario=='horse_owner_requalification' else 'hubspot_proposed_patch';handoff_out=a.output_dir/'governed-handoff.json';handoff_result,_=run('a2-governed-handoff',['scripts/build_and_validate_a2_handoff.py',str(current),'--previous-record',str(prev),'--destination',dest,'--output',str(handoff_out)],expected=(0,1),output_file=handoff_out)
 semantic={'all_operators_covered':sorted(set(coverage))==sorted(OPERATORS),'external_actions_zero':all((load(a.output_dir/p.name).get('external_actions',0)==0) for p in a.output_dir.glob('*.json') if p.name not in {'workflow-result.json'}),'review_package_valid':load(review_result).get('valid') is True,'handoff_not_delivered':handoff_result.get('delivered') is False,'expected_handoff_state':handoff_result.get('status')==('prepared_not_delivered' if dest=='a1_requalification' else 'blocked_contract_pending')};passed=all(x['passed'] for x in steps) and all(semantic.values());result={'workflow':'equinet-a2-no-integration','version':'1.2.1','scenario':a.scenario,'status':'pass' if passed else 'fail','operator_coverage':sorted(set(coverage)),'operator_count':len(set(coverage)),'steps':steps,'semantic_checks':semantic,'external_calls':0,'external_actions':0};out=a.output_dir/'workflow-result.json';out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps(result,indent=2,ensure_ascii=False));return 0 if passed else 1
if __name__=='__main__':raise SystemExit(main())
