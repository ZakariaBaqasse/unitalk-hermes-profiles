#!/usr/bin/env python3
"""Create, advance, inspect, and resume an A2 enrichment run ledger."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from a2_twenty_fullenrich_common import load_json,sha256_json,utc_now,write_json_atomic
STAGES=['created','pulled','claimed','website_planned','website_fetched','website_person_observations_validated','website_decisions_validated','facebook_complete','website_people_selected','lookup_complete','lookup_decisions_validated','search_complete','selection_decisions_validated','contact_enrichment_complete','write_plan_validated','twenty_written','reconciled','terminal']
def main():
 ap=argparse.ArgumentParser();sub=ap.add_subparsers(dest='cmd',required=True)
 s=sub.add_parser('start');s.add_argument('--run-id',required=True);s.add_argument('--ledger',type=Path,required=True);s.add_argument('--company-ids',nargs='*',default=[])
 a=sub.add_parser('advance');a.add_argument('--ledger',type=Path,required=True);a.add_argument('--stage',choices=STAGES,required=True);a.add_argument('--artifact',action='append',default=[])
 g=sub.add_parser('status');g.add_argument('--ledger',type=Path,required=True)
 x=ap.parse_args()
 if x.cmd=='start':
  if x.ledger.exists():raise SystemExit('ledger already exists')
  d={'schema_id':'a2-enrichment-run-ledger','schema_version':'0.1.0','run_id':x.run_id,'created_at':utc_now(),'updated_at':utc_now(),'stage':'created','company_ids':x.company_ids,'artifacts':[],'audit':[],'external_actions':0};d['ledger_sha256']=sha256_json({k:v for k,v in d.items() if k!='ledger_sha256'});write_json_atomic(x.ledger,d)
 elif x.cmd=='advance':
  d=load_json(x.ledger);old=d['stage'];new=x.stage
  if STAGES.index(new)<STAGES.index(old):raise SystemExit('run stage cannot move backwards')
  d['stage']=new;d['updated_at']=utc_now()
  for item in x.artifact:
   p=Path(item);d['artifacts'].append({'path':str(p),'sha256':sha256_json(load_json(p)) if p.suffix=='.json' and p.exists() else None})
  d['audit'].append({'at':utc_now(),'from':old,'to':new});d['ledger_sha256']=sha256_json({k:v for k,v in d.items() if k!='ledger_sha256'});write_json_atomic(x.ledger,d)
 else:d=load_json(x.ledger)
 print(json.dumps({'run_id':d['run_id'],'stage':d['stage'],'companies':len(d.get('company_ids',[])),'artifacts':len(d.get('artifacts',[])),'ledger':str(x.ledger)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
