#!/usr/bin/env python3
"""Resolve A2 field proposals under the active protected-field policy."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_wave3_contracts import ROOT,canonical_hash,load,load_active
POLICY_REL='foundations/contracts/governance/a2-protected-fields-and-conflict-policy-0.3.0.json';DEFAULT_POLICY=ROOT/POLICY_REL

def evaluate(item:dict,policy:dict)->dict:
 protection=item.get('protection_class');errors=[]
 if item.get('hubspot_object') and item.get('hubspot_property'):
  matches=[x for x in policy.get('hubspot_protected_fields',[]) if x.get('object')==item['hubspot_object'] and x.get('property')==item['hubspot_property']]
  if not matches:errors.append('unknown protected HubSpot property')
  else:
   derived=matches[0]['class']
   if protection and protection!=derived:errors.append('caller protection class conflicts with policy')
   protection=derived
 baseline=item.get('baseline_state');proposal=item.get('proposal_state');confidence=item.get('confidence');conflict=item.get('conflict');review=item.get('review_decision');workflow=item.get('workflow_dependency_status');crm=item.get('crm_write_authorized') is True
 if protection not in policy['protection_classes']:errors.append('unknown protection class');action='invalid'
 elif protection=='prohibited_personal_or_sensitive':action='reject_collection'
 elif protection=='review_only_personal_data':action='hold_for_privacy_review'
 elif protection in {'authoritative_control','system_read_only'}:
  action='no_change' if proposal=='same' else 'preserve_authoritative_and_block' if protection=='authoritative_control' else 'read_only_preserve'
 elif protection=='owner_and_routing':action='no_change' if proposal=='same' else 'preserve_or_needs_owner_review'
 elif proposal=='same':action='no_change'
 elif conflict=='material' or protection=='manual_business_value':action='preserve_and_hold'
 elif confidence!='high':action='reject_proposal'
 elif item.get('a1_requalification_required') is True:action='create_requalification_signal'
 elif baseline=='empty':action='propose_add'
 else:action='preserve_and_hold'
 if action=='propose_add' and review=='approved' and crm and workflow not in {'verified_no_side_effect','verified_managed_side_effect'}:action='approved_proposal_write_blocked'
 write_allowed=action in {'propose_add','propose_update'} and review=='approved' and crm and workflow in {'verified_no_side_effect','verified_managed_side_effect'} and policy['global_rules']['current_hubspot_write_authorized'] is True
 proposal_id='A2-PROP-'+canonical_hash({'field':item.get('field_key'),'target':item.get('target_id'),'baseline':item.get('baseline_value'),'proposal':item.get('proposed_value'),'evidence':item.get('evidence_ids',[])})[:16].upper()
 canonical_action={'no_change':'no_change','propose_add':'add','propose_update':'update','read_only_preserve':'retain','preserve_authoritative_and_block':'hold','preserve_or_needs_owner_review':'hold','preserve_and_hold':'hold','reject_proposal':'retain','hold_for_privacy_review':'hold','reject_collection':'retain','create_requalification_signal':'retain','approved_proposal_write_blocked':'hold'}.get(action)
 return {'command':'a2-evaluate-protected-field-action','version':'0.1.0-draft.1','proposal_id':proposal_id,'field_key':item.get('field_key'),'target_id':item.get('target_id'),'protection_class':protection,'policy_action':action,'canonical_proposal_action':canonical_action,'recommended_action':action,'baseline_value':item.get('baseline_value'),'proposed_value':item.get('proposed_value'),'baseline_preserved':action not in {'propose_add','propose_update'},'evidence_ids':item.get('evidence_ids',[]),'human_review_required':action not in {'no_change','read_only_preserve','reject_collection'},'workflow_dependency_status':workflow,'external_write_allowed':write_allowed,'crm_patch_prepared':False,'a1_score_changed':False,'canonical_record_mutated':False,'external_actions':0,'errors':errors}

def main()->int:
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('case',type=Path);p.add_argument('--policy',type=Path,default=DEFAULT_POLICY);p.add_argument('--output',type=Path);a=p.parse_args();policy=load_active(POLICY_REL) if a.policy==DEFAULT_POLICY else load(a.policy);r=evaluate(load(a.case),policy);text=json.dumps(r,indent=2,ensure_ascii=False)+'\n'
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(text,encoding='utf-8')
 print(text,end='');return 1 if r['errors'] else 0
if __name__=='__main__':raise SystemExit(main())
