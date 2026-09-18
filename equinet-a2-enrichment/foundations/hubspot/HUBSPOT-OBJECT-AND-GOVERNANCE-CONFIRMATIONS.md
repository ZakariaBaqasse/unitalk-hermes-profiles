# Equinet HubSpot Object and Governance Confirmations

**Version:** `1.0.0`  
**Recorded at:** `2026-08-25T10:28:44Z`  
**Source:** Confirmed by Séverine from Equinet-provided responses  
**Profile:** `equinet-a2-enrichment`

## 1. Object confirmations

| Object | Confirmation | A2 consequence |
|---|---|---|
| Creator | Does not exist in HubSpot | No A2 change is required. If a future specialist requires Creator, Unitalk must propose a separate schema for Mustad/Equinet approval. |
| Campaign | Exists as a standard HubSpot object, not a custom object | A2 may later reference the standard Campaign object when an approved mapping requires campaign provenance. Unitalk must not create a duplicate Campaign custom object. |
| Complaints | Confirmed custom object | No direct A2 use is approved. |
| Sample Requests | Confirmed custom object | Existing approval workflows remain specific to Sample Requests and are not an A2 enrichment-review workflow. |

## 2. Confirmed HubSpot governance roles

| Responsibility | Confirmed person/account |
|---|---|
| HubSpot Super Admin | Tahmineh Goljan |
| HubSpot Super Admin | Faezeh Yazdani |
| HubSpot Super Admin | Lucija Batarelo |
| HubSpot Super Admin service/placeholder account | Mustad HubSpot |
| CRM/business owner | Tahmineh Goljan |
| CRM/business owner | Lucija Batarelo |
| Approve new HubSpot properties, objects and workflows | Tahmineh Goljan |
| Approve new HubSpot properties, objects and workflows | Lucija Batarelo |
| Approve Unitalk OAuth connection | Tahmineh Goljan |
| Approve Unitalk OAuth connection | Faezeh Yazdani |
| Approve Unitalk OAuth connection | Lucija Batarelo |

## 3. Authority boundaries

These confirmations are useful for routing future technical decisions, but they do not activate an integration or authorise an action.

- Super Admin status does not itself approve A2 business outputs, CRM writes, provider spend, pilot activation or production acceptance.
- `Mustad HubSpot` is a service or placeholder account and cannot serve as a human approver.
- The confirmed CRM/business owners may approve HubSpot properties, objects and workflows within the stated scope.
- The A2 business reviewer and backup reviewer remain to be confirmed separately.
- The OAuth approver list identifies who may approve the connection; no OAuth connection or scope has yet been granted or verified.
- Every sensitive action still requires recorded approval, a verified authorised account, minimum necessary scopes and an audit record.

## 4. Work now unlocked

Unitalk can now:

1. route the proposed HubSpot field/object/workflow mapping to Tahmineh Goljan and Lucija Batarelo for business/CRM approval;
2. route the future OAuth approval request to Tahmineh Goljan, Faezeh Yazdani or Lucija Batarelo;
3. distinguish human approvers from the `Mustad HubSpot` service/placeholder account;
4. avoid designing a duplicate Campaign custom object;
5. mark Creator as absent and out of scope for A2;
6. prepare a role-based technical approval register for later integration work.

## 5. Remaining gaps

- named A2 business reviewer;
- backup A2 reviewer;
- action-level approval matrix for enriched records and field changes;
- provider and budget approvers;
- actual OAuth grant and approved scopes;
- read-only HubSpot connection and verification;
- any future Creator schema required by another specialist profile.

## 6. Readiness statement

```text
HubSpot technical approvers: confirmed
CRM/business owners: confirmed
Property/object/workflow approvers: confirmed
OAuth approvers: confirmed
OAuth connection: not granted or connected
A2 business reviewer and backup: not confirmed
A2 HubSpot writes: prohibited
```
