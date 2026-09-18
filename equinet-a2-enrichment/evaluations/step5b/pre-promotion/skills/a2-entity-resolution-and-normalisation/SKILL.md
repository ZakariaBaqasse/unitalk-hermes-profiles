---
name: a2-entity-resolution-and-normalisation
description: Use whenever Equinet A2 must normalise a prospect person or organisation and compare possible matches before enrichment. Produces conservative match proposals without merging records, inventing relationships or treating a domain as a unique identifier.
---

# A2 Entity Resolution and Normalisation

## Delivery status

**Version:** `0.1.0-draft.1`  
**Status:** `WAVE 1 DRAFT — NOT APPROVED`

## Mission

Normalise identity signals and classify possible matches before duplicate and eligibility review. Preserve all source values. Produce a proposal only; never merge or modify an external record.

## Inputs

A JSON request containing:

- `source_entity`: the A2 person or organisation;
- `candidate_matches`: zero or more comparison entities;
- optional name, website/domain, business email, business phone, organisation context and public-profile URLs.

Every entity requires `entity_type` equal to `person` or `organisation`.

## Command

```bash
/opt/data/profiles/equinet-a2-enrichment/.venv/bin/python \
  /opt/data/profiles/equinet-a2-enrichment/scripts/normalise_and_resolve_a2_entities.py \
  <request.json> --output <resolution.json>
```

## Deterministic method

1. Unicode-normalise and case-fold names.
2. Remove punctuation and spacing variation; remove common legal suffixes only for comparison.
3. Canonicalise website domains, emails, phones and public-profile URLs.
4. Compare only signals supplied in both records.
5. Treat domain as one signal, never a unique identifier by itself.
6. Use `confirmed_match` only when a matching name plus a strong identifier, or multiple strong identifiers, agree without a conflicting compared field.
7. Use `possible_match` when only one identity basis agrees.
8. Use `conflict` when matching and contradictory material signals coexist or several records are confirmed.
9. Use `unresolved` when evidence is insufficient.
10. Preserve the canonical record; return a separate resolution result for review.

## Outputs

- normalised source entity;
- candidate-level signals and match statuses;
- overall canonical identity-resolution recommendation;
- human-review requirement;
- zero external actions.

## Boundaries

Do not create a person, organisation, alias or relationship not supported by the handoff or explicit evidence. Do not use fuzzy model judgement as a deterministic match. Do not query HubSpot or any external source from this skill.

## Handoff

Pass the result to `a2-duplicate-and-eligibility-review`. A possible match, conflict or unresolved identity requires review before research.
