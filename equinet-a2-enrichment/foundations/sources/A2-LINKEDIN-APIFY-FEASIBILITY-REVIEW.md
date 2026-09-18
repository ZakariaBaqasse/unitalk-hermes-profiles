# A2 LinkedIn and Apify Feasibility Review

> **Historical feasibility artifact.** The active SOC-1 through SOC-8 clarification preserves its automation blocks while adding URL-only capture of explicit professional social links from approved official-site pages and preferring an exact LinkedIn company URL for any future separately authorised profile-search action.

**Version:** `0.1.0`  
**Reviewed at:** `2026-08-25T11:02:38Z`  
**Status:** `TECHNICAL CAPABILITY CONFIRMED — RUNTIME USE BLOCKED PENDING RIGHTS, PRIVACY AND VENDOR APPROVAL`  
**Profile:** `equinet-a2-enrichment`

## 1. Executive decision

LinkedIn can be useful for discovering or checking a person's current professional role, especially when an official company website links directly to the person's LinkedIn profile. It should not be treated as the sole authoritative source and it is not currently approved for automated A2 extraction.

Apify currently lists community Actors that can technically:

- take a LinkedIn company URL or company name and return employees with current-position data;
- search LinkedIn people using company URLs, job titles and locations;
- take an individual LinkedIn profile URL and return current and previous work experience;
- optionally attempt to find an email through a separate email-search process.

Technical availability does not create permission. LinkedIn's current User Agreement prohibits scraping or copying profiles and other service data with scripts, robots, crawlers or other automated means unless LinkedIn explicitly permits it separately. The identified Actors are Community Actors maintained by HarvestAPI, not Apify-maintained Actors. Apify states that it does not vet or guarantee the security, accuracy or legal compliance of Community Actors and that customers must assess permissions and third-party rights.

**Recommendation:** keep these Actors as `blocked_pending_rights_and_vendor_review`. Do not activate them for A2 pilot or production under the current evidence.

## 2. Actors identified

### 2.1 LinkedIn Company Employees Scraper

- Actor: `harvestapi/linkedin-company-employees`
- URL: `https://apify.com/harvestapi/linkedin-company-employees`
- Maintainer: HarvestAPI
- Store classification: Community Actor

Advertised inputs:

- LinkedIn company URLs, preferably;
- company names, with an attempted LinkedIn-company match;
- optional employee locations;
- optional fuzzy query;
- optional strict job-title filters;
- optional LinkedIn industry IDs;
- optional years at the company;
- maximum-result and pagination controls.

Advertised outputs/modes:

- Short: full name, profile URL, summary, location and current positions;
- Full: extended profile details including work experience, education and skills;
- Full plus email search: profile data plus an independent attempt to find email addresses.

The Actor states that it can process company names, but an exact LinkedIn company URL is safer because company-name resolution can select the wrong organisation.

The page states that one query may return no more than 2,500 LinkedIn results and that one-by-one company mode can accept up to 1,000 companies. These product limits are not appropriate A2 operating limits.

### 2.2 LinkedIn Profile Scraper plus Email

- Actor: `harvestapi/linkedin-profile-scraper`
- URL: `https://apify.com/harvestapi/linkedin-profile-scraper`
- Maintainer: HarvestAPI
- Store classification: Community Actor

Advertised inputs:

- LinkedIn profile public identifiers;
- LinkedIn profile URLs;
- LinkedIn profile IDs.

Advertised outputs include:

- name and headline;
- current position;
- current and previous work experience;
- location;
- education, skills, certifications and other profile content;
- optional independent email search.

### 2.3 LinkedIn Profile Search Scraper

- Actor: `harvestapi/linkedin-profile-search`
- URL: `https://apify.com/harvestapi/linkedin-profile-search`
- Maintainer: HarvestAPI
- Store classification: Community Actor

Advertised search filters include:

- current company LinkedIn URLs;
- previous company LinkedIn URLs;
- current and past job titles;
- location;
- industry IDs;
- total years of experience;
- years at the current company;
- fuzzy search query.

This Actor could technically support role-based employee discovery from a known company page.

## 3. Email-search boundary

The Actor documentation explicitly states that email addresses are not extracted from LinkedIn profiles. The optional email mode performs a separate email-search and SMTP-validation process and does not guarantee a result.

Therefore, if ever approved:

- a discovered email must not be labelled `source: LinkedIn`;
- the email-search provider and methodology must be recorded separately;
- source provenance and validation evidence must remain separate;
- personal versus work-email policy must pass;
- paid-email lookup requires budget approval;
- deliverability verification does not create consent to contact.

For the first A2 pilot, the email-search mode should remain disabled.

## 4. Current terms and governance findings

### LinkedIn User Agreement

- URL: `https://www.linkedin.com/legal/user-agreement`
- Effective date shown: November 3, 2025

Section 8.2 states that users must not develop, support or use software, scripts, robots, crawlers, browser plugins or other means to scrape or copy LinkedIn services, including profiles and other data. It also restricts copying or using information obtained directly or through third-party search tools, aggregators or brokers without the relevant content owner's consent.

An Actor's statement that it needs no cookies or account does not remove this restriction.

### Apify General Terms

- URL: `https://docs.apify.com/legal/general-terms-and-conditions`
- Effective date shown: July 9, 2026

Apify states that use of third-party services is governed by those third parties' terms and that customers are responsible for obtaining required accounts, licences and permissions. Customers are also responsible for the legality and appropriateness of Customer Data.

### Apify Actor Terms

- URL: `https://docs.apify.com/legal/actor-terms-and-conditions`

Apify states that Community Actors are not reviewed, vetted, endorsed or monitored for quality, security, accuracy or legal compliance. Customers must assess the Actor and permission level. The Creator may have access to Actor inputs and outputs, and the Creator is not treated as an Apify subprocessor under the Apify DPA.

This is material for Mustad Data governance and requires vendor/subprocessor review before any use.

## 5. Safe A2 role-verification path now

The recommended current workflow is:

```text
A1 handoff or official business website
→ retain an explicitly linked LinkedIn company/profile URL as a discovery reference
→ authorised human opens the public LinkedIn profile manually
→ human confirms only the minimum current professional facts
→ record profile URL, observed role, company and observation date
→ A2 treats the role as evidence subject to freshness/conflict review
```

If the official business website itself identifies the person and role, use that official-site statement as the primary evidence and keep LinkedIn as optional secondary context.

For small Farrier and Horse Owner businesses, LinkedIn coverage may be lower than official websites, association listings, Facebook business pages or direct Equinet confirmation. This must be measured rather than assumed.

## 6. Potential automated path only after approval

If LinkedIn or another authorised data provider grants an acceptable automated-use route, the safest A2 flow would be:

```text
Official business site or validated A1 record
→ exact LinkedIn company/profile URL
→ approved limited-permission provider/Actor
→ retrieve only name, current title, current company, location and profile URL
→ verify company match and current-position dates
→ create field-level evidence
→ human review
```

Do not collect by default:

- full education history;
- full career history;
- skills and endorsements;
- recommendations;
- follower/connections counts;
- posts;
- open-to-work status;
- personal descriptions unrelated to the commercial purpose;
- profile photos;
- inferred personal emails or phone numbers.

## 7. Required approvals before any Actor test

### Rights and platform review

- LinkedIn written permission, approved API route or documented legal/commercial exception for the exact use;
- confirmation of permitted fields, storage, reuse and retention;
- confirmation that company-employee discovery and profile retrieval are covered.

### Community Actor due diligence

- Actor permission level, with limited permissions required unless a separately justified exception is approved;
- HarvestAPI identity, privacy terms, security practices and data locations;
- whether the Creator can access inputs and outputs;
- subprocessors and retention;
- incident and deletion process;
- code/reputation review and support expectations;
- current pricing and rate limits.

### Equinet business decisions

- role types to search;
- maximum people per company;
- allowed fields;
- allowed regions;
- whether company-name matching is permitted or exact company URL is required;
- whether manual LinkedIn verification is sufficient for the pilot;
- reviewer and conflict process;
- budget and approver.

### Unitalk runtime controls

- exact Actor ID and pinned version/build;
- input and output allowlists;
- one-company and low-result pilot caps;
- no email-search mode initially;
- idempotency and cost cap;
- evidence, audit and deletion controls;
- no direct HubSpot write;
- independent role/company-match validation.

## 8. Recommended status by option

| Option | Recommendation | Status |
|---|---|---|
| Official company Team/About page | Primary role source when explicit | Recommended for bounded A2 gap verification |
| LinkedIn URL retained as a reference | Store the professional URL already published by the business/person | Permitted only under approved data-minimisation policy |
| Human manual LinkedIn role check | Small-volume role verification | Candidate for pilot after Equinet confirms the procedure |
| Official LinkedIn/API route | Preferred automation route if the licence covers the use | Integration pending |
| Licensed professional-data provider with documented rights | Candidate alternative to direct LinkedIn scraping | Provider benchmark pending |
| Apify HarvestAPI Community Actors | Technically capable but not authorised under current evidence | `blocked_pending_rights_and_vendor_review` |
| Automated account/browser LinkedIn access | Do not use | Blocked |

## 9. Pricing and capability caveat

The Actor pages contain current marketing and pricing claims, but some pricing text differs between page headers and README mode descriptions. Pricing is controlled by the Actor developer and may change. Verify the live Apify Console price, Actor build, permission level and event definitions immediately before any approved benchmark.

Do not use published user counts, ratings, recent modification dates or “no cookies” claims as evidence of legal compliance, data accuracy or suitability for Mustad Data.

## 10. Decision

**Unitalk recommendation:**

1. Treat LinkedIn as a useful secondary role-discovery and role-verification source, not the default authoritative source.
2. Use official company websites and authorised CRM/direct confirmation first.
3. Permit manual LinkedIn verification only after Equinet approves the minimal fields and operating procedure.
4. Keep the three HarvestAPI Actors blocked from A2 runtime until rights, vendor, privacy, security, retention, permission-level and budget reviews pass.
5. If an automated route becomes permissible, test the Company Employees Actor with exact company URLs and strict role filters; then use the Profile Scraper only for selected profile URLs.
6. Keep email discovery as a separate, initially disabled provider step with independent provenance.

No A2 source register, runtime allowlist or integration is changed by this review.
