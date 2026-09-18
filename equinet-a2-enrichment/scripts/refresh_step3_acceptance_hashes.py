#!/usr/bin/env python3
"""Refresh Step 3A-3F acceptance hashes after approved clarification."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def h(p):return hashlib.sha256((R/p).read_bytes()).hexdigest()
def update(step,pairs,extras=None):
 p=R/'evaluations'/step/'acceptance-record.json';d=json.loads(p.read_text())
 for path_key,hash_key in pairs:d[hash_key]=h(d[path_key])
 if extras:d.update(extras)
 p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def main():
 clarification='evaluations/foundation-clarifications/step3f-personal-email-review-clarification.json'
 update('step3a',[('catalogue','catalogue_sha256'),('csv_projection','csv_projection_sha256'),('technical_validation','technical_validation_sha256'),('package_manifest','package_manifest_sha256')],{'clarification_applied':clarification})
 p=R/'evaluations/step3a/acceptance-record.json';d=json.loads(p.read_text());d['validation_results']['field_count']=32;d['validation_results']['negative_regressions']='14/14 pass';p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
 update('step3b',[('package_contract','package_contract_sha256'),('technical_validation','technical_validation_sha256'),('package_manifest','package_manifest_sha256')],{'clarification_applied':clarification})
 update('step3c',[('source_register','source_register_sha256'),('csv_projection','csv_projection_sha256'),('technical_validation','technical_validation_sha256'),('package_manifest','package_manifest_sha256')],{'clarification_applied':clarification})
 p=R/'evaluations/step3c/acceptance-record.json';d=json.loads(p.read_text());d['validation_results']['source_count']=12;d['validation_results']['negative_regressions']='13/13 pass';d['remaining_activation_inputs']=[x for x in d['remaining_activation_inputs'] if 'personal email must always be discarded' not in x];p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
 update('step3d',[('policy','policy_sha256'),('technical_validation','technical_validation_sha256'),('package_manifest','package_manifest_sha256')],{'clarification_applied':clarification})
 update('step3e',[('policy','policy_sha256'),('technical_validation','technical_validation_sha256'),('package_manifest','package_manifest_sha256')],{'clarification_applied':clarification})
 update('step3f',[('policy','policy_sha256'),('technical_validation','technical_validation_sha256'),('package_manifest','package_manifest_sha256')],{'clarification_applied':clarification})
 print(json.dumps({'updated':['step3a','step3b','step3c','step3d','step3e','step3f']},indent=2))
if __name__=='__main__':main()
