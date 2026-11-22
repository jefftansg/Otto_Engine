# Source-backed review without repeated evidence entry

23 November 2026. Candidate **1.4.0-dev.3**, proposed with the mixed-document routing correction. No final release, financial attestation or template approval.

## Uploaded statement references

`uploaded_review_sources` accepts only current analysed source documents whose fingerprints match the statement group. `source_review_evidence` records their filenames and full SHA-256 fingerprints automatically, with any optional reviewer note appended. Coverage review retains structured source references as well as the existing coverage hash and reviewer/timestamp. Source imports use the same automatic references for transaction review and import history. ZIP restoration retains those references, never the original PDFs.

The reviewer still explicitly checks and approves identity, coverage, currency, balances and transaction rows. Company/date confirmation, unique account mapping, exact coverage, gross/running-balance reconciliation, duplicate prevention and stale-source rejection remain. Missing originals cannot generate automatic references; a manual evidence note is required. Existing/manual transaction reviews still require a written note. Notes alone cannot override failed date, coverage or ledger checks.

`account_approval_errors` supplies the actual failed conditions used by both the approval API and UI: missing reviewer, missing source evidence, unchecked confirmation, incomplete setup, changed sources/period, invalid or conflicting control code and manual-account linkage. It replaces the generic rejection that incorrectly appeared to blame confirmed reporting dates for a blank evidence-location field.

## Save incomplete preparation

**Save review notes and continue** stores only preparation notes, reviewer text, suggested control code and source revision in `bank_review_drafts`. It does not create an account, clear a source issue, approve a balance or import a transaction. The saved workspace ZIP retains notes. Other account work and existing save controls remain available while unresolved accounts stay unapproved. The active issues and source-readiness checks still determine completeness.

## Clear date warnings

The OCBC daily-details parser retains its posting-date rule. A posting date outside the selected/verified export period remains a review exception, even if that date is within the company's overall financial year. Messages now show the actual date and period, explain that the bank's posting/value-date basis may differ and identify the next action. No posting/value dates are substituted, no balances are invented and no file is silently approved.

When a parser has already withheld all rows with a specific extraction exception, staging retains that primary reason without adding the secondary no-rows and missing-net-movement warnings. Real net/gross/count/coverage failures without such a primary extraction failure still remain blocking. Resolving company dates does not resolve a per-statement export/date exception.

## Validation

Eight new synthetic tests in `tests/test_review_evidence.py` cover automatic filename/hash evidence for account and transaction approval, duplicate retry/ZIP review preservation, missing or wrong source fingerprints, explicit manual evidence, manual-note requirements, precise rejection/no-mutation, unapproved preparation notes/restoration, date-root-cause messages without cascading errors and actual Auto form submission with an empty optional note. The existing detailed multi-bank UI test uses the new labels. Full local suite: **209 tests passed, no skips**, macOS arm64/Python 3.9.6. Exact-head CI is recorded in the PR.

Read-only local analysis of the three supplied affected statements confirms posting dates beyond their monthly export periods. No client documents, extracted identifiers/amounts, diagnostic logs or screenshots are committed. Source dates and accounting policy remain unchanged. Local processing only; no dependency or regulatory-determination change.
