# Open questions

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Needs review
- Owner: Product
- Related requirements: OTTO-REP-002, OTTO-COMP-001, OTTO-COMP-002, OTTO-BANK-002, OTTO-UFS-002, OTTO-QA-001
- Sources/evidence: Archive inventory, source audit and ACRA source review

## Purpose and scope

Capture work requiring evidence, authorisation or an accountable product decision.

## As-is implementation (evidence-backed)

The archive supplies sample inputs/outputs and historical release notes. It contains no identifiable Inner Mirror package, no general live bank-layout validation, no prior full source trees and no executed Mac UI evidence from this environment. Primary Act and detailed ASC endpoints were inaccessible. All 52 tests in the supplied suite passed.

## To-be requirements

| Rank | Question or missing evidence | Owner | Resolution and impact |
| --- | --- | --- | --- |
| P0 | Can Compliance retrieve current Act ss199/201/201A/205B/205C, Schedule and effective instruments, including any 2026 consultation outcome? | Compliance | Record enacted/current text and first-year consolidation, notice and signature requirements before using decisions for clients. |
| P0 | Which ASC applicability/transition texts and interpretations govern FRS, SFRS(I), Small Entities and FRS 119 for supported clients? | Compliance | Approve period-specific framework rules, comparatives and transition evidence. |
| P0 | What evidence supports openings, historical equity and director advances on first-year and migrated files? | Accounting | Approve opening policy, rejection conditions and independent golden cases. |
| P0 | How should cash/Noncash, mixed allocations and cross-source journal IDs be handled? | Accounting and Engineering | Reproduce issues with fictional fixtures, choose mapping and ID policy and approve correction scope. |
| P0 | Which cases can export incomplete drafts, and who may authorise UFS? | Product and Accounting | Approve review-only output and immutable issue gate. |
| P0 | Which MacOS, Python and browser versions will be supported? | Engineering | Obtain a Mac test environment and check fresh install, offline relaunch, workflow and layout. |
| P1 | Can the owner supply redacted, authorised latest Inner Mirror management and UFS PDFs/workpapers? | Product | Confirm report field and pagination design baselines before M6 sign-off. |
| P1 | Which bank/Bizfile variants, entity types, currencies and multi-period scenarios should be supported? | Product | Obtain consented sample inputs and define the production support matrix. |
| P1 | What evidence retention, backup, restore, authorised access and client separation apply? | Product and Privacy | Assign DPO/legal review and approve operational requirements before pilot. |
| P1 | Can prior ZIP versions or source tags verify compatibility and history? | Engineering | Test actual representative restores and attach dated evidence. |

## Questions on outsourcing and audit readiness

| Priority | Question | Responsible party | Evidence needed |
| --- | --- | --- | --- |
| P0 | Which qualifications, contractual obligations, review procedures and sign-off are required for a per-client accountant? | Product / Accounting | Scope, credentials, liability, confidentiality and escalation policy |
| P0 | What if an audit firm also supplied bookkeeping or financial statement preparation? | Independent auditor / Compliance | Case-specific assessment against Singapore professional ethics and independence restrictions |
| P0 | Is this client's audit legally required, requested by lenders/investors, or voluntary? | Client / Compliance | Evidence of audit-exemption evaluation, group status, notices and contractual terms |
| P1 | Who contracts with and appoints the auditor? | Client / Product | Direct engagement letter and valid auditor appointment |
| P1 | Which documents may be shared in the audit package and with whom? | Client / Privacy | Specific consent, redaction, access/revocation, retention and disclosure log |
| P1 | How is an authentic external signed auditor's report verified and linked? | Product / Auditor | Provenance and immutable status rules; no Otto-generated opinion |
| P1 | Should future partner offers include SSRS 4410 compilation or SSRE review? | Product / Practitioner | Independent engagement and marketing/assurance terminology approval |

## Acceptance criteria / verification

Each closure identifies evidence, named reviewer, dated decision, impacted requirements and a regression case when applicable. P0 issues gate the relevant milestone rather than document publication.

## Risks, limitations and open questions

Remain in documentation and preparation scope pending explicit implementation approval. Prioritise reproducibility and policy findings before commercial work.

## Related documents

- [Document Extraction](06_DOCUMENT_EXTRACTION.md)
- [Audit Exemption Eligibility](13_AUDIT_EXEMPTION_ELIGIBILITY.md)
- [Accounting Framework Eligibility](14_ACCOUNTING_FRAMEWORK_ELIGIBILITY.md)
- [Test Strategy](18_TEST_STRATEGY.md)
- [Development Roadmap](19_DEVELOPMENT_ROADMAP.md)
- [Decision Log](22_DECISION_LOG.md)

## Otto Auto pending design decisions (21 November 2026)

Determine OCR/batch limits, AI provider or local inference and client consent, configurable materiality/provisional approval gates, user-template mapping without statutory disclosure loss, and measured success targets for migration from Guided to Auto. Keep these unresolved until separately designed and tested. See [Otto Auto specification](25_AI_FIRST_AUTO_EXPERIENCE.md).

## Report design prerequisites (P0, 21 November 2026)

Obtain the specific previously accepted MA and UFS documents (prefer original editable DOCX/XLSX plus PDFs) and confirm fonts, sizes, margins, section sequence, numbering and template use rights. Decide canonical PDF/DOCX rendering strategy only after comparison. Until then, golden-master fidelity and editable Word claims remain unverified. See [Report Design System](26_REPORT_DESIGN_SYSTEM_AND_TEMPLATE_FIDELITY.md).
