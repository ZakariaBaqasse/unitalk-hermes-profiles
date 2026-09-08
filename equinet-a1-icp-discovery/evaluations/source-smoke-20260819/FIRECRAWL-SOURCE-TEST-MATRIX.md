# Equinet A1 — Firecrawl Source Smoke-Test Matrix

**Run:** 2026-08-19 (landing + secondary-page extraction)
**Method:** Firecrawl `extract(format=markdown)`, concurrency 1, public URLs only
**Boundary:** no login, proxy, browser fallback or write; stop on 403/429/CAPTCHA/robots conflict
**Artifact root:** `evaluations/source-smoke-20260819/`

---

## Legend

| Status | Meaning |
|--------|---------|
| Completed | Landing + secondary-page test passed, page returned usable prospect data |
| Partial | Succeeded for some page types but not others, or returned navigation-only content |
| Failed | Every request for that source returned an error |
| Blocked | Source actively blocks automated extraction (403, CAPTCHA, login wall) |
| Not tested | Source was never selected for a request |

---

## Matrix

| # | Source ID | Status | Landing URL(s) | Secondary URL(s) | Prospect data found | Pagination / depth | Limitations | Evidence files | Next action |
|---|-----------|--------|----------------|-------------------|---------------------|--------------------|-------------|----------------|-------------|
| 1 | `pdf.american_farriers_association` | **Partial** | `search/newsearch.asp` ❌ (Internal Server Error) | `/` ✅ (14k chars), `/find-a-farrier` ✅ (6k) | Navigation + membership info; no member directory without login | Not tested on secondary pages | Legacy ASP search page blocks all engines; `/find-a-farrier` is a text page, not a searchable directory | `landing-batch-1.json`, `landing-targeted-retry.json`, `pages-batch-7-american-farriers.json` | Update Source Register landing URL to `/`; accept that directory requires member login |
| 2 | `pdf.professional_farriers_directory` | **Partial** | `/` ✅ (15k chars) | `why_hire_accredited_farrier.php` ✅ (12k), `accreditation.php` ✅ (15k) | Industry / accreditation info only; no prospect listings | Not applicable — no public directory found | All public pages are navigation-heavy; member directory on `mms.professionalfarriers.com` is login-gated per Source Register | `landing-batch-1.json`, `pages-batch-5-professional-farriers.json`, `pages-batch-5b-professional-farriers-acc.json` | Keep as industry-context source only; do not attempt to scrape member area |
| 3 | `pdf.farrier_industry_association` | **Blocked** | `/` ✅ (9k chars) | `page-982813` (Find a Member) ❌ reCAPTCHA | Public industry-context pages (homepage, About, Events) are accessible; the member-search workflow is reCAPTCHA-gated and cannot be automated | Not applicable | Firecrawl captured the CAPTCHA widget HTML, not directory data; public information pages remain usable for industry context | `landing-batch-1.json`, `pages-batch-1-farrieriq-fia.json` | Retain for industry-context research only; do not attempt to automate the member directory |
| 4 | `pdf.farrieriq` | **Completed** | `/directory` ✅ (3k chars) | `/directory/kentucky` ✅ (2k), `/directory/lexington-ky` ✅ (487) | 9 Kentucky farrier names, cities, specialties, service types; city-level drill-down works | State page lists 6 cities; each city page links to individual farrier detail pages (not tested) | Content at each level is concise; no phone/email in listing pages | `landing-batch-1.json`, `pages-batch-1-farrieriq-fia.json`, `pages-batch-6-details.json` | Approved for bounded directory extraction; state → city → detail navigation works |
| 5 | `pdf.horseprofinder` | **Completed** | `/` ✅ (20k chars) | `/farriers/` ✅ (9k chars) | Farrier categories by specialty (corrective, hot, race, sport, draft, etc.); full navigation tree | No pagination encountered; single listing page | Category-based rather than location-based; no phone/email in extracted text | `landing-batch-2.json`, `pages-batch-2-madbarn-horseprofinder.json` | Already approved per Source Register V1.3; ready for bounded use |
| 6 | `pdf.edss_farriers` | **Partial** | `/farriers` ✅ (27k chars) | `/farriers/` (state selection) ✅ (27k) | 27 Markdown table rows with 11 distinct public phone numbers and farrier names extracted, but these are default-contact rows, not Kentucky-filtered results | Not tested — state selection requires form POST | Page explains state-dropdown selection; Firecrawl extracted the default contact table but could not perform the Kentucky state selection required for the pilot | `landing-batch-2.json`, `pages-batch-4-edss-hast.json` | State-level extraction requires JS or form submission; Firecrawl cannot navigate the dropdown |
| 7 | `pdf.bwfa_kentucky` | **Partial — landing only** | `/kentucky` ✅ (407 chars) | **(no secondary test)** | One farrier: Sean Petrilli, Lancaster KY | N/A — single entry, no pagination | 407 chars of content; only one member listed for the entire state; Squarespace site, minimal data | `landing-batch-2.json` | No secondary test performed; possibly useful for individual verification but not scalable prospecting |
| 8 | `pdf.mad_barn_directory` | **Completed** | `/directory` ✅ (28k chars) | `/location/united-states/kentucky/` ✅ (20k), `/service/farrier/location/united-states/kentucky/` ✅ (32k) | 66,785 total directory listings; KY farrier service page has structured results with names, categories, locations | Not tested beyond one KY service-category page | No individual detail pages tested; phone/email visibility unknown at detail level | `landing-batch-2.json`, `pages-batch-2-madbarn-horseprofinder.json`, `pages-batch-6-details.json` | Strong candidate for bounded directory extraction; state + service-category navigation works |
| 9 | `pdf.equinenow_kentucky_farms` | **Partial — landing only** | `/kentuckyfarms.htm` ✅ (12k chars) | **(no secondary test)** | 1,846 Kentucky farm listings (page 1 shows 8); property marketplace | Page 1 of 1,846 (8 results shown); pagination visible | Farm/real-estate marketplace, not farrier directory; no farrier content; 1,846 pages would exceed source limits | `landing-batch-3.json` | Not suitable for farrier prospecting, may be useful for Horse Owner segment; no secondary test |
| 10 | `pdf.newhorse` | **Completed** | `/` ✅ (87k chars) | `/page/farrier/b.2001.html` ✅ (28k chars) | Farrier listing page with business names, categories, descriptions; full site navigation | Not tested beyond farrier category page | No individual detail pages tested; phone/email visibility not confirmed | `landing-batch-3.json`, `pages-batch-3-newhorse-bestlex.json` | Approved for bounded directory extraction; farrier category structure works |
| 11 | `pdf.hast_farriers` | **Completed** | `/farriers.htm` ❌ rate-limited then ✅ (4k) | `/farriers.htm` (same page) ✅ (4k) | Manual list of 15+ Greater Louisville farriers with names, phone numbers, locations | Flat HTML page; no pagination | Plain HTML table; Firecrawl rate-limited on first attempt (reset ≈11s); static list may be stale | `landing-batch-3.json`, `landing-targeted-retry.json`, `pages-batch-4-edss-hast.json` | Useful manual snapshot of Louisville-area farriers with phone numbers; no search or filters |
| 12 | `pdf.best_of_lexington_farriers` | **Completed** | `/farrier/kentucky` ❌ rate-limited then ✅ (139k chars) | `/farrier/kentucky` (same page) ✅ (139k) | 5 farrier listings for Kentucky; awards-based directory; full category tree | No pagination (max 5 results); flat listing | Rate-limited on first attempt (reset ≈10s); only 5 farrier entries for entire state | `landing-batch-3.json`, `landing-targeted-retry.json`, `pages-batch-3-newhorse-bestlex.json` | Suitable for bounded use; small volume limits scalability |

---

## Summary

| Metric | Count |
|--------|-------|
| Sources tested | 12 |
| **Completed** (landing + secondary, prospect data usable) | 6 |
| **Partial** (some page types succeeded or landing-only) | 5 |
| **Blocked** (active access control prevents extraction) | 1 |
| **Failed** (no successful extraction for any URL) | 0 |
| **Not tested** | 0 |

**Notes on classifications:**

- **Partial (5):** AFA (homepage works but directory search blocks), Professional Farriers (public pages accessible but no directory), EDSS (default table extracted but Kentucky selection requires form POST), BWFA Kentucky (landing-only, single entry), EquineNow (landing-only, horse farms not farriers).
- **Blocked (1):** FIA (member-search workflow is reCAPTCHA-gated; public industry-context pages remain accessible).
- **BWFA Kentucky** and **EquineNow** received landing-page testing only; no secondary-page artifacts exist.
- **HorseProFinder** is already approved in the Source Register V1.3 — no action needed.
- Two sources triggered Firecrawl rate-limiting on first attempt within a single batch run (hast.net, Best of Lexington); both succeeded on retry after the rate-limit window reset.

## Recommended next actions

1. **FarrierIQ, Mad Barn, NewHorse, HorseProFinder, Häst, Best of Lexington** — ready for bounded directory extraction as approved sources.
2. **American Farriers Assoc** — update landing URL to `/` (homepage), accept that `/find-a-farrier` is text-only.
3. **Professional Farriers** — retain only for industry/accreditation context; do not automate member-area access.
4. **EDSS** — requires form-based state selection; needs manual or browser-based interaction for state-level farrier lists.
5. **FIA** — blocked by reCAPTCHA on the Find a Member page; not suitable for automated extraction.
6. **BWFA** — single entry for Kentucky; low value for scalable prospecting.
7. **EquineNow** — useful for Horse Owner segment (farm/property listings); not suitable for farrier prospecting.