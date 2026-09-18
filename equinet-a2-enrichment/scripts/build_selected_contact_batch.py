#!/usr/bin/env python3
"""Build a selected-contact batch from validated Lookup and staged Search decisions."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import load_json,make_envelope,write_json_atomic

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--lookup-packet',type=Path);ap.add_argument('--lookup-decisions',type=Path);ap.add_argument('--search-packet',type=Path,action='append',default=[]);ap.add_argument('--selection-decisions',type=Path,action='append',default=[]);ap.add_argument('--run-id',required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();selected=[];seen=set();selected_companies=set()
 if len(a.search_packet)!=len(a.selection_decisions):raise SystemExit('each --search-packet requires a matching --selection-decisions')
 if a.lookup_packet and a.lookup_decisions:
  packet=load_json(a.lookup_packet);validation=load_json(a.lookup_decisions);packets={x['company']['twenty_company_id']:x for x in packet.get('packets',[])}
  for d in validation.get('validated_decisions',[]):
   p=packets.get(d.get('company_id'),{});items={x['twenty_person'].get('twenty_person_id'):x for x in p.get('linked_people',[])}
   for pd in d.get('person_decisions',[]):
    if not pd.get('retain_as_target'):continue
    item=items.get(pd.get('twenty_person_id'),{});person=(item.get('lookup_result') or {}).get('person') or {};pid=person.get('provider_person_id')
    if not pid or pid in seen:continue
    seen.add(pid);selected_companies.add(d.get('company_id'));selected.append({'request_id':f'contact-{pid}','company_id':d.get('company_id'),'twenty_person_id':pd.get('twenty_person_id'),'provider_person_id':pid,'full_name':person.get('full_name'),'first_name':person.get('first_name'),'last_name':person.get('last_name'),'professional_network_url':person.get('professional_network_url'),'company_name':p.get('company',{}).get('name'),'company_domain':p.get('company',{}).get('domain'),'source_kind':'existing','selected_target_priority':'PRIMARY','selection_stage':'lookup'})
 for packet_path,decision_path in zip(a.search_packet,a.selection_decisions):
  packet=load_json(packet_path);validation=load_json(decision_path);packets={x['company']['twenty_company_id']:x for x in packet.get('packets',[])}
  for d in validation.get('validated_decisions',[]):
   cid=d.get('company_id');p=packets.get(cid,{});candidates={x.get('provider_person_id'):x for x in p.get('candidates',[])}
   if cid in selected_companies and d.get('selected_provider_person_ids'):raise SystemExit(f'{cid}: multiple Search stages selected People')
   for pid in d.get('selected_provider_person_ids') or []:
    person=candidates.get(pid)
    if not person or pid in seen:continue
    duplicate=next((x for x in d.get('candidate_decisions',[]) if x.get('provider_person_id')==pid),{}).get('duplicate_of_twenty_person_id')
    seen.add(pid);selected_companies.add(cid);selected.append({'request_id':f'contact-{pid}','company_id':cid,'twenty_person_id':duplicate,'provider_person_id':pid,'full_name':person.get('full_name'),'first_name':person.get('first_name'),'last_name':person.get('last_name'),'professional_network_url':person.get('professional_network_url'),'company_name':p.get('company',{}).get('name'),'company_domain':p.get('company',{}).get('domain'),'source_kind':'existing' if duplicate else 'new','selected_target_priority':d.get('selected_target_priority'),'selection_stage':d.get('search_stage')})
 out=make_envelope('a2-selected-contact-batch',a.run_id,{'selected_people':selected});write_json_atomic(a.output,out);print(json.dumps({'status':'valid','selected_people':len(selected),'output':str(a.output)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
