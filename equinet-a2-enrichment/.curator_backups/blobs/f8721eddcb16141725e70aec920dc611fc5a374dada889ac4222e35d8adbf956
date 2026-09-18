---
name: a2-contact-resolution-and-selection
description: "Use when A2 decides Lookup/Search and retained People."
version: 0.1.0
author: Unitalk
license: Proprietary
metadata:
  hermes:
    tags: [equinet, a2, identity-resolution]
    related_skills: [a2-fullenrich-connector, a2-twenty-fullenrich-workflow]
---

# A2 Contact Resolution and Selection

## When to Use

Use after FullEnrich Lookup or Search returns a compact decision packet.

## Commands

```bash
python scripts/build_lookup_decision_packet.py <companies.json> <lookups.json> --output <packet.json>
python scripts/validate_lookup_decisions.py <packet.json> <decisions.json> --output <validation.json>
python scripts/build_search_candidate_packet.py <companies.json> <search.json> --output <packet.json>
python scripts/validate_person_selection_decisions.py <packet.json> <decisions.json> --output <validation.json>
```

The LLM decides identity, Company match, employment relationship, role priority, retention and Search necessity. `a2RoleStatus` is the employment relationship with the target Company: `CURRENT_AT_COMPANY`, `NOT_CURRENT_AT_COMPANY`, or `UNVERIFIED`. `CURRENT_AT_COMPANY` requires a confirmed Company match; `NOT_CURRENT_AT_COMPANY` requires a mismatch. Role priority remains separate. Validators enforce exact provider titles, active role rules, maximum-two selection and real IDs. Resolution progresses `primary → owner → linked_secondary → secondary → completed_no_target`. A verified, current, Company-confirmed A1-linked `SECONDARY` Person is marked as a deferred fallback during Lookup. After primary and Owner fail, resolve that linked Person with zero provider Search calls; if selected, Contact Enrich and update the exact existing Twenty Person. Run paid secondary Search only if no linked fallback is selected. A retained primary/owner-stage Person must be `PRIMARY`; linked and paid secondary stages must retain `SECONDARY`. Domainless ambiguous results are not linked automatically. Existing stale or non-primary People remain linked.