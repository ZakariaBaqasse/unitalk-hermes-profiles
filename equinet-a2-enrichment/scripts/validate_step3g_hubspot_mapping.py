#!/usr/bin/env python3
"""Validate the Step 3G preliminary A2-to-HubSpot mapping."""
from __future__ import annotations
import copy,csv,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]; M=R/'foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.1.0-draft.1.json'; C=R/'foundations/contracts/mappings/a2-hubspot-preliminary-mapping-0.1.0-draft.1.csv'; F=R/'foundations/contracts/business/a2-business-field-catalogue-0.1.0-draft.1.json'; H=Path('/opt/data/profiles/equinet/attachments/Property_Definitions (1).csv'); E=R/'evaluations/step3g'; CONTRACT=R/'foundations/A2-PRELIMINARY-HUBSPOT-MAPPING.md'; REVIEW=E/'A2-PRELIMINARY-HUBSPOT-MAPPING-REVIEW.md'; OUT=E/'technical-validation.json'; MANIFEST=E/'step3g-draft-package-manifest.json'; LANGUAGE=R/'evaluations/foundation-clarifications/language-audit.json'; B=R/'scripts/build_step3g_hubspot_mapping.py'; V=Path(__file__).resolve()
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def metadata():
 with H.open(encoding='utf-8-sig',newline='') as f:return {(x['Object'].lower(),x['Internal name']) for x in csv.DictReader(f)}
def validate(m):
 e=[]
 if m.get('status')!='approved_by_unitalk_as_working_baseline_live_verification_pending':e.append('mapping status must be the approved Unitalk working baseline pending live verification')
 approval=m.get('unitalk_approval',{})
 if approval.get('approver')!='Séverine, Unitalk Operations' or approval.get('scope')!='decisions_3G_1_through_3G_10':e.append('Unitalk approval metadata is invalid')
 for d in m.get('dependencies',[]):
  p=Path(d['path']) if str(d['path']).startswith('/') else R/d['path']
  if not p.exists() or sha(p)!=d['sha256']:e.append(f"dependency hash mismatch: {d['path']}")
 cat={x['field_key'] for x in load(F)['fields']}; entries=m.get('mappings',[]); keys=[x.get('canonical_field') for x in entries]
 if set(keys)!=cat or len(keys)!=len(set(keys)):e.append('canonical field coverage or uniqueness mismatch')
 md=metadata()
 for x in entries:
  if x.get('write_authorized') is not False:e.append(f"write authority enabled: {x.get('canonical_field')}")
  for d in x.get('hubspot_destinations',[]):
   if (d['object'].lower(),d['property']) not in md or d.get('metadata_found') is not True:e.append(f"unknown HubSpot destination: {d['object']}.{d['property']}")
  if x.get('hubspot_destinations') and x.get('workflow_dependency_status')!='unverified':e.append(f"workflow dependency overstated: {x['canonical_field']}")
 if m.get('hubspot_connection')!='not_connected' or m.get('global_write_authorized') is not False or m.get('metadata_snapshot_only') is not True:e.append('connection or write readiness overstated')
 by={x['canonical_field']:x for x in entries}
 expected={'person.personal_email_candidate':'review_only_no_hubspot_mapping','organisation.horse_count_band':'mapping_blocked_taxonomy_conflict','organisation.stable_type':'mapping_blocked_enum_mismatch','person.professional_credential':'canonical_only_compatibility_field','organisation.disciplines':'proposed_segment_specific'}
 for k,v in expected.items():
  if by.get(k,{}).get('mapping_status')!=v:e.append(f"mapping status mismatch: {k}")
 if by['person.personal_email_candidate']['hubspot_destinations']:e.append('personal email candidate mapped to HubSpot')
 if m.get('approval_gate',{}).get('live_read_verification')!='pending' or m['approval_gate'].get('global_write_authorized') is not False:e.append('approval gate overstated')
 return e
def negatives(m):
 out=[]
 def run(n,x,fn):
  q=copy.deepcopy(m);fn(q);es=validate(q);out.append({'name':n,'expected_error':x,'errors':es,'passed':any(x in z for z in es)})
 def fld(q,k):return next(x for x in q['mappings'] if x['canonical_field']==k)
 run('dep_hash','dependency hash mismatch',lambda q:q['dependencies'][0].update(sha256='0'*64))
 run('drop_field','coverage or uniqueness mismatch',lambda q:q['mappings'].pop())
 run('duplicate_field','coverage or uniqueness mismatch',lambda q:q['mappings'].append(copy.deepcopy(q['mappings'][0])))
 run('enable_write','write authority enabled',lambda q:fld(q,'person.business_email').update(write_authorized=True))
 run('unknown_property','unknown HubSpot destination',lambda q:fld(q,'person.business_email')['hubspot_destinations'][0].update(property='invented'))
 run('workflow_verified_early','workflow dependency overstated',lambda q:fld(q,'person.business_email').update(workflow_dependency_status='verified'))
 run('connection_active','connection or write readiness overstated',lambda q:q.update(hubspot_connection='connected'))
 run('personal_email_mapped','personal email candidate mapped',lambda q:fld(q,'person.personal_email_candidate')['hubspot_destinations'].append({'object':'Contact','property':'email','metadata_found':True}))
 run('horse_band_enabled','mapping status mismatch',lambda q:fld(q,'organisation.horse_count_band').update(mapping_status='proposed_unverified'))
 run('approval_write','approval gate overstated',lambda q:q['approval_gate'].update(global_write_authorized=True))
 run('approval_removed','Unitalk approval metadata is invalid',lambda q:q['unitalk_approval'].update(scope='draft_only'))
 return out
def render(m,results):
 summary={s:sum(x['mapping_status']==s for x in m['mappings']) for s in sorted({x['mapping_status'] for x in m['mappings']})}; rows='\n'.join(f"| `{x['canonical_field']}` | `{x['mapping_status']}` | {', '.join(d['object']+'.'+d['property'] for d in x['hubspot_destinations']) or 'None'} | `{x['conversion']}` |" for x in m['mappings'])
 CONTRACT.write_text(f"""# Equinet A2 Preliminary HubSpot Mapping

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED UNITALK WORKING BASELINE — LIVE READ VERIFICATION PENDING`  
**Decision timestamp:** `2026-08-27T09:09:39Z`  
**Step:** `3G — Preliminary A2-to-HubSpot Mapping`

## Boundary

This mapping is based on supplied metadata only. HubSpot is not connected. It proves candidate property names and metadata types, not live values, associations, permissions, workflow safety or write readiness. Every write remains blocked.

## Mapping table

| Canonical field | Status | HubSpot candidate(s) | Conversion |
|---|---|---|---|
{rows}

## Known blocks

- `horse_count_range` has overlapping options and cannot receive deterministic A2 bands.
- `stable_type` lacks the complete proposed A2 taxonomy.
- Full-name splitting requires human review.
- Farrier credential/certification representation needs one approved model.
- Personal-email candidates remain canonical review-only with no HubSpot mapping.
- Workflow and list dependencies remain unverified.

## Object routing

Person fields target Contact. Organisation fields prefer Company, but several existing Horse Owner/Farrier fields exist only on Contact and are marked for scope review. Relationship mappings and exact associations remain pending live read-only verification.

## Current result

Mapping status counts: `{json.dumps(summary,sort_keys=True)}`. Global write authority is false.
""",encoding='utf-8')
 REVIEW.write_text("""# Decision Review — Step 3G Preliminary HubSpot Mapping

**Version:** `0.1.0-draft.1`  
**Status:** `APPROVED AS UNITALK WORKING BASELINE — LIVE VERIFICATION PENDING`  
**Decision timestamp:** `2026-08-27T09:09:39Z`

| ID | Proposed decision |
|---|---|
| 3G-1 | Use the supplied HubSpot property export as the preliminary metadata authority. |
| 3G-2 | Keep all directions read-and-propose only; approve no writes. |
| 3G-3 | Preserve populated manual CRM values and apply Step 3E conflict rules. |
| 3G-4 | Prefer `work_email` for professional email and treat primary `email` as a reviewed fallback. |
| 3G-5 | Keep personal-email candidates canonical review-only with no HubSpot mapping. |
| 3G-6 | Block `horse_count_range` mapping until overlapping options are resolved. |
| 3G-7 | Block `stable_type` mapping until the enum mismatch is resolved. |
| 3G-8 | Use segment-specific discipline candidates and require explicit enum conversion. |
| 3G-9 | Keep every mapped field at `workflow_dependency_unverified`. |
| 3G-10 | Require live read-only verification of values, associations, permissions and fill rates before final mapping approval. |

This approval establishes the Unitalk working baseline and authorises preparation of the final specialist SOUL in draft form. It does not connect HubSpot or authorise a write.
""",encoding='utf-8')
def main():
 m=load(M);errs=validate(m);neg=negatives(m)
 if any(not x['passed'] for x in neg):errs.append('negative regression failed')
 with C.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
 csvok=len(rows)==len(m['mappings']) and [x['canonical_field'] for x in rows]==[x['canonical_field'] for x in m['mappings']]
 if not csvok:errs.append('CSV fidelity failed')
 E.mkdir(parents=True,exist_ok=True);render(m,neg);lang=load(LANGUAGE)
 if not lang.get('pass'):errs.append('language audit failed')
 result={'step':'3G','version':m['version'],'approval_state':'approved_unitalk_working_baseline_live_verification_pending','mapping':{'path':str(M.relative_to(R)),'sha256':sha(M)},'field_count':len(m['mappings']),'mapped_field_count':sum(bool(x['hubspot_destinations']) for x in m['mappings']),'status_counts':{s:sum(x['mapping_status']==s for x in m['mappings']) for s in sorted({x['mapping_status'] for x in m['mappings']})},'validation':{'errors':validate(m),'passed':not validate(m)},'csv_fidelity':csvok,'negative_regressions':{'total':len(neg),'passed':sum(x['passed'] for x in neg),'cases':neg},'language_audit':{'files_checked':lang.get('files_checked'),'findings':len(lang.get('findings',[])),'passed':lang.get('pass') is True},'hubspot_connection':False,'hubspot_write_authorized':False,'external_actions':0,'failures':errs,'pass':not errs}
 OUT.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');paths=[M,C,B,V,CONTRACT,REVIEW,OUT];manifest={'manifest_id':'equinet-a2-step3g-draft-package','version':m['version'],'status':'approved_unitalk_working_baseline_live_verification_pending','files':[{'path':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths],'file_count':len(paths),'external_actions':0};MANIFEST.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
 print(json.dumps({'pass':result['pass'],'fields':result['field_count'],'mapped':result['mapped_field_count'],'negative':f"{result['negative_regressions']['passed']}/{result['negative_regressions']['total']}",'review':str(REVIEW),'failures':errs},indent=2));return 0 if not errs else 1
if __name__=='__main__':raise SystemExit(main())
