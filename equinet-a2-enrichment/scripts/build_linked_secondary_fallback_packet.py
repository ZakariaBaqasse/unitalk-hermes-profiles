#!/usr/bin/env python3
"""Build a candidate packet from verified A1-linked secondary People after Owner fallback fails."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import load_json,make_envelope,normalise_text,write_json_atomic
def main():
 ap=argparse.ArgumentParser();ap.add_argument('lookup_packet',type=Path);ap.add_argument('lookup_validation',type=Path);ap.add_argument('owner_validation',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();packet=load_json(a.lookup_packet);lookup=load_json(a.lookup_validation);owner=load_json(a.owner_validation)
 packets_by={x['company']['twenty_company_id']:x for x in packet.get('packets',[])};lookup_by={x.get('company_id'):x for x in lookup.get('validated_decisions',[])};owner_ids={x.get('company_id') for x in owner.get('validated_decisions',[]) if x.get('next_search_stage')=='linked_secondary'};out_packets=[]
 for cid in sorted(owner_ids):
  source=packets_by.get(cid,{});decision=lookup_by.get(cid,{});eligible={x.get('twenty_person_id'):x for x in decision.get('person_decisions',[]) if x.get('secondary_fallback_eligible')};candidates=[];existing=[]
  for item in source.get('linked_people',[]):
   tp=item.get('twenty_person') or {};tid=tp.get('twenty_person_id');lr=item.get('lookup_result') or {};person=lr.get('person') or {}
   existing.append({'twenty_person_id':tid,'fullenrich_person_id':person.get('provider_person_id') or tp.get('fullenrich_person_id'),'professional_network_url':person.get('professional_network_url') or tp.get('professional_network_url'),'normalised_name':normalise_text(person.get('full_name') or tp.get('full_name'))})
   if tid in eligible and person.get('provider_person_id'):
    candidates.append({**person,'linked_twenty_person_id':tid,'deferred_from_lookup':True,'lookup_evidence_refs':eligible[tid].get('evidence_refs') or []})
  out_packets.append({'company':source.get('company') or {'twenty_company_id':cid},'search_stage':'linked_secondary','target_priority':'SECONDARY','target_titles':[],'existing_people':existing,'search_terminal_status':'succeeded' if candidates else 'not_found','candidates':candidates,'evidence_ref':f'lookup-secondary-fallback:{cid}'})
 out=make_envelope('a2-linked-secondary-fallback-packet',packet.get('run_id','unknown'),{'search_stage':'linked_secondary','packets':out_packets,'external_calls':0});write_json_atomic(a.output,out);print(json.dumps({'status':'valid','packets':len(out_packets),'candidates':sum(len(x['candidates']) for x in out_packets),'external_calls':0,'output':str(a.output)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
