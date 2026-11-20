# ACRA company profile

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Draft
- Owner: Product
- Related requirements: OTTO-CO-001, OTTO-DOC-001
- Sources/evidence: engine/autofill.py:44–94,173–184, guided.py:280–345, tests/test_autofill.py

## Purpose and scope

Propose setup fields from uploaded business profiles with reliable evidence.

## As-is implementation (evidence-backed)

| Field | Current detection and review |
| --- | --- |
| Name and UEN | Common company title or separately labelled values, UEN regex. |
| Incorporation | Labelled incorporation or registration date only. |
| Entity type | Common private-company wording or name suffix, subject to confirmation. |
| Address and primary activity | Bounded registered office lines and labelled activity. |
| FYE | Explicit date label. A separate suggested start uses a 12-month heuristic and may clip to incorporation. |
| Directors and secondary activity | Manual setup/review, with no general profile parser demonstrated. |

The supplied texts exercise sample headings and missing FYE. There is no verified official template-version coverage, authenticity check or live Bizfile integration.

## To-be requirements

Store candidate, source label/location, hash, observed date and status per field. Validate UEN form, actual company identity, entity classification, date order, related party names and director effective dates against approved evidence. Obtain permission to retain the minimum necessary profile. For missing or inconsistent FYE ask for a dated official record, annual return or authorised director confirmation. Incorporation alone provides no FYE.

## Acceptance criteria / verification

Extract fixture name and UEN, leave unsupported fields pending, retain evidence and approvals on restore, show conflicting upload proposals side by side, and prevent automatic replacement of an approved value. Test reformatted headings, missing FYE and another entity type.

## Risks, limitations and open questions

Request consented redacted examples of Bizfile versions, director lists, historical entries and first periods. Distinguish historical profile dates from active records.

## Related documents

- [Document Extraction](06_DOCUMENT_EXTRACTION.md)
- [User Workflows Ux](08_USER_WORKFLOWS_UX.md)
- [Singapore Compliance](12_SINGAPORE_COMPLIANCE.md)
- [Open Questions](23_OPEN_QUESTIONS.md)
