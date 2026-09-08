# Equinet A1 — ICP Configuration

**Version:** `2.0.0`
**Status:** Approved for production
**Applies to:** `equinet-a1-icp-discovery`  
**Candidate contract:** `1.0.0`

## Purpose

This configuration defines who A1 should treat as an Equinet ICP candidate. It does not contain scoring weights. The later scoring configuration will assign numeric points to the approved criteria without changing their business meaning.

## Production scope

- Approved countries: United States, Australia and New Zealand.
- There is no default country, region/state or city.
- Country, region/state and city must be supplied before discovery.
- Country and region codes are resolved through the approved deterministic location mapping.
- Missing, ambiguous or conflicting locations block launch and require clarification.
- Complete and unambiguous user-supplied locations require no additional confirmation.
- Both segments are measured separately.
- Farriers are the primary segment; professional/commercial Horse Owners are secondary.

## Farrier summary

### Standard qualified profile

An active professional Farrier, full-time or part-time, with evidence of current hoof-care work and plausible professional product usage or purchasing influence.

### Priority signals

- established or broad client base;
- regular business activity;
- service in a high-equine-activity area;
- performance, sport, corrective or therapeutic specialisation;
- certification or strong professional experience;
- sport or competition-horse focus;
- multi-Farrier or established business;
- product-selection influence;
- recent association, event, certification or professional activity.

### Lower-priority pathway

An apprentice or junior Farrier may be retained as future potential when active entry into the profession is evidenced. This pathway requires human review and cannot automatically produce a high-priority prospect.

### Exclusion

Hobby-only, inactive, or unsubstantiated contacts with no evidence of professional hoof-care activity are not qualified professional prospects.

## Horse Owner summary

### Standard qualified profile

A professional or commercial Horse Owner or equine operation managing more than three horses. Included types are professional owners, farms, breeders, boarding and training stables, equestrian centres, competition yards, trainers and stable managers with purchasing influence.

### Priority signals

- performance or competition disciplines;
- breeding activity;
- professional equine network;
- high-equine-activity geography;
- recent competition, sale, acquisition or expansion signal;
- recurring need for professional hoof-care products and services;
- purchasing or product-selection influence.

### Threshold handling

The current confirmed threshold is **more than three horses**. If the count is unknown or at/below the threshold but strong commercial signals exist, A1 sends the candidate to human review and never qualifies it automatically. This V1 exception pathway was approved by Séverine.

### Exclusion

A casual single-horse recreational owner with no evidence of professional activity, purchasing influence or commercial orientation is outside the A1 ICP.

## Shared exclusions

When confirmed by the authoritative source, A1 must not treat these records as new prospects:

- duplicate records;
- existing customers;
- active opportunities;
- partners or distributors;
- competitors;
- opted-out or suppressed contacts.

A previously lost opportunity is sent to review rather than excluded automatically. Until HubSpot is connected, these CRM checks remain explicitly `unavailable`; A1 must never claim that they passed.

## Minimum A1 review package

A real candidate entering review must include:

- identity and segment;
- prospect type;
- approved-country location with country, region/state and city;
- at least one approved or conditional source;
- evidence for every confirmed criterion;
- qualification and exclusion status;
- score status, confidence and next action;
- batch duplicate-check result;
- audit correlation ID.

Public professional contact details are optional. When present, they may be retained by A1 because Séverine approved their reuse by A2, but each detail must reference its public source.

## Status labels

- **Confirmed by Equinet:** directly stated in the supplied A1 blueprint responses.
- **Confirmed by Séverine:** explicitly decided during Unitalk configuration.
- **Proposed by Unitalk:** safe implementation rule derived from confirmed requirements and still open to review.
- **Pending Equinet confirmation:** business exception or boundary that remains unresolved.

## Validated decisions

The original criteria decisions remain approved. The production geography amendment adds:

1. Unknown or at/below three horses plus strong commercial signals → human review, never automatic qualification.
2. Production discovery covers the United States, Australia and New Zealand with no default location.
3. An active apprentice is future potential, lower priority and always human-reviewed.
4. A previously lost opportunity is human-reviewed rather than automatically excluded.
5. The proposed minimum A1 review package is approved.

The production geography amendment was authorised on 2026-09-03. If Equinet later provides a conflicting instruction, the Equinet-approved instruction takes precedence and requires a versioned configuration update.
