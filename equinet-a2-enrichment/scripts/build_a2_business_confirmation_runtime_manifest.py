#!/usr/bin/env python3
"""Build the A2 business-confirmation runtime overlay manifest."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'foundations/contracts/skills/a2-business-confirmation-runtime-manifest-1.1.0.json'
STAMP='2026-08-30T17:05:11Z'
FILES=[
 'skills/a2-handoff-intake-and-initialisation/SKILL.md',
 'skills/a2-entity-resolution-and-normalisation/SKILL.md',
 'skills/a2-duplicate-and-eligibility-review/SKILL.md',
 'skills/a2-gap-analysis-and-enrichment-planning/SKILL.md',
 'skills/a2-permitted-enrichment-research/SKILL.md',
 'skills/a2-field-verification/SKILL.md',
 'skills/a2-field-verification/references/contact-verification.md',
 'skills/a2-field-verification/references/professional-verification.md',
 'skills/a2-field-verification/references/equine-business-verification.md',
 'skills/a2-evidence-confidence-and-freshness/SKILL.md',
 'skills/a2-protected-field-conflict-resolution/SKILL.md',
 'skills/a2-data-quality-and-review-readiness/SKILL.md',
 'skills/a2-review-package-and-governed-handoffs/SKILL.md',
 'scripts/build_a2_gap_plan.py','scripts/preflight_a2_source_action.py',
 'scripts/normalise_and_validate_a2_observations.py','scripts/evaluate_a2_minimum_package.py',
 'scripts/classify_a2_target_role.py','scripts/validate_a2_contact_selection.py',
 'scripts/create_a2_revision.py','scripts/build_and_validate_a2_handoff.py',
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def skill_version(path):
 text=path.read_text(encoding='utf-8');m=re.search(r'\*\*Version:\*\* `([^`]+)`',text);return m.group(1) if m else None
def main():
 missing=[x for x in FILES if not (ROOT/x).is_file()]
 if missing:print(json.dumps({'status':'fail','missing':missing},indent=2));return 1
 items=[]
 for rel in FILES:
  p=ROOT/rel;item={'path':rel,'bytes':p.stat().st_size,'sha256':sha(p)}
  if rel.endswith('/SKILL.md'):item['version']=skill_version(p)
  items.append(item)
 manifest={'manifest_id':'equinet-a2-business-confirmation-runtime','version':'1.1.0','status':'pilot_ready_no_integration','created_at':STAMP,'business_configuration_version':'0.2.0','decision_id':'A2-EQUINET-ROLES-CONTACTS-HORSEOWNER-20260830','files':items,'runtime_limits':{'default_selected_contacts':1,'maximum_selected_contacts':2,'external_actions':0},'integration_states':{'hubspot_read':'not_connected','hubspot_write':'not_connected_not_authorized','twenty':'not_connected','n8n':'not_connected','apify_harvestapi':'not_runtime_active','web':'disabled_by_default'},'historical_runtime_manifests':['a2-operational-skill-manifest-0.1.0.json','a2-wave1-runtime-manifest-0.1.0.json','a2-wave2-runtime-manifest-0.1.0.json','a2-wave3-runtime-manifest-0.1.0.json','a2-step5-runtime-manifest-0.1.0.json'],'external_actions':0}
 OUT.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps({'status':'pass','files':len(items),'output':str(OUT)},indent=2));return 0
if __name__=='__main__':raise SystemExit(main())
