# Twenty Live Schema Snapshot — Step 10

Observed through authenticated Twenty REST metadata and record reads. No production write was executed by this implementation session.

## Connectivity and confirmed capabilities

- Metadata and Core API reads return HTTP 200.
- Equinet confirms the configured key can write, create People, create Company–Person associations and filter by A2 enrichment status.
- No webhook/event integration is required.

## Objects

- Company ID: `89cb0885-61c0-4d39-989f-b7f0cf248dc9`
- Person ID: `4220f12d-d3ec-4268-ad2f-64c4453859fa`
- `Company.people`: one-to-many
- `Person.company`: many-to-one through `companyId`

## A2 Company fields

`a2EnrichmentStatus`, `a2EnrichmentVersion`, `a2EnrichmentRunId`, `a2ProcessingStartedAt`, `a2LastAttemptedAt`, `a2LastEnrichedAt`, `a2NextRetryAt`, `a2EnrichmentErrorCode`.

Company statuses: `NOT_ENRICHED`, `PROCESSING`, `ENRICHED`, `PARTIALLY_ENRICHED`, `COMPLETED_NO_TARGET`, `RETRYABLE_ERROR`, `BLOCKED`.

## A2 Person fields

`a2IdentityStatus`, `a2RoleStatus`, `a2RolePriority`, `a2CompanyMatchStatus`, `a2EnrichmentStatus`, `a2FullenrichPersonid`, `a2LastVerifiedAt`, `a2LastEnrichedAt`, `a2EnrichmentRunId`.

`a2FullenrichPersonid` is unique. The internal token is intentionally preserved exactly.

## Population snapshot

- 40 Companies; 35 People.
- 35 Companies had one linked Person and five had none.
- Only six Companies had a domain URL, so domainless FullEnrich Search is required.
- Existing People had no populated job title or LinkedIn URL.
- Existing names are generally stored as a full name in `firstName` with empty `lastName`; preserve raw data and derive a lookup name without automatic source rewrite.

## Mapping controls

A1 discovery, qualification, ICP and evidence-confidence fields remain read-only. Generic `emails` is used only for professional email under the A2 write policy. Generic `phones` stores the selected FullEnrich mobile/direct value only when empty or A2-owned; different populated manual values are preserved. Incidental personal email is not automatically written to Twenty.
