# Contact Verification

## Accepted contact observations

- Use only an explicitly published or authorised professional email, published business phone or approved FullEnrich mobile phone.
- Preserve the source wording and evidence reference.
- Normalise email case and phone formatting deterministically.
- Attempt professional email, published business phone and FullEnrich mobile for a selected contact. At least one verified channel satisfies the minimum when the others are unavailable; missing mobile alone does not block review.
- Retain one selected named contact by default and at most two with a documented large-organisation or shared-responsibility reason.
- A free-mail domain may still be a business contact when the official business site explicitly publishes it for professional use; record the publication context.

## Rejections and holds

- Reject generated or inferred email patterns.
- Reject contact data without a passed source action and evidence reference.
- Do not request personal email from FullEnrich by default. If it is returned incidentally, retain it separately as `person.personal_email_candidate` with provider provenance and verification status for human review; do not treat it as professional contactability or place it in CRM or outreach automatically.
- Keep `not_found`, `unavailable`, `not_checked` and `error` distinct.

Contact availability, verification or deliverability never creates consent, outreach eligibility or sending authority.
