# Equinet A2 Incidental Personal-Email Decision

**Decision ID:** `A2-FULLENRICH-INCIDENTAL-PERSONAL-EMAIL-20260906`  
**Recorded at:** `2026-09-06T13:38:10Z`  
**Recorded by:** Séverine, Unitalk Operations  
**Status:** `BUSINESS RULE CONFIRMED — INTEGRATION PENDING`

## Confirmed rule

Personal email is not requested by default from FullEnrich. If FullEnrich returns a personal email incidentally, A2 retains it as `person.personal_email_candidate` on the A2 contact with exact provider provenance and verification status. It remains distinct from professional email, requires human review, does not satisfy professional contactability by itself, does not create consent or outreach authority and is not written automatically to HubSpot.

This decision supersedes only the unexpected-personal-email handling in `A2-FULLENRICH-SOURCE-ROUTING-20260906`. All other FullEnrich routing and contact-limit rules remain unchanged.
