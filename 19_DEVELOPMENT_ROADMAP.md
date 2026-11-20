# Development roadmap

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Draft
- Owner: Product
- Related requirements: All IDs in the register
- Sources/evidence: Baseline audit, docs/20_REQUIREMENTS_TRACEABILITY.md, master documentation milestone scope

## Purpose and scope

Sequence work for reliability and commercial readiness. Scope is proposed and requires implementation approval.

## As-is implementation (evidence-backed)

v1.2.4 is a local single-account SGD preparation tool. 52 existing backend tests passed. The baseline archive and documentation audit support M0 with unresolved application, source and platform gaps.

## To-be requirements

| Milestone | Depends on | Outcome and deliverables | Acceptance gate | Risk and exclusions |
| --- | --- | --- | --- | --- |
| M0 Baseline audit | None | Reproducible inventory, checksums, known issues, dependency and Mac verification plan | Archive diff reviewed, test run recorded, risk owners assigned | Dependency and platform drift. Feature development excluded. |
| M1 Onboarding | M0 | Effective five-stage intake, confirmed company/period, workspace preservation | Missing FYE stays pending, legacy ZIP and keyboard flow pass | Unseen profiles. Direct Bizfile excluded. |
| M2 Bank intake | M1 | Multi-account staging, distinct source identity, reconciliation and reviewer controls | Coverage, overlap, transfers, scan and false-positive fixtures pass | Layout variety. OCR and FX require separate approval. |
| M3 Ledger integrity | M2 | Posting identities, reversals, adjustments, subledgers and period close | Independent balanced golden ledgers reconcile; issue blocks enforced | Legacy conversion. Tax computation excluded. |
| M4 Clarification | M1, M3 | Prioritised evidence requests, client-safe exports and audited resolution | Answers survive restore and preserve entries; correction requires approval | Disclosure to wrong recipient. Automated posting excluded. |
| M5 Eligibility | M0, M1 | Versioned, evidence-backed audit/framework/filing review | Compliance reviewer signs rule scenarios and primary texts | Regulatory change. Filing and legal certification excluded. |
| M6 Report completeness | M3, M4, M5 | Complete management and entity-appropriate UFS with comparisons, notes, snapshot review | Package ties to ledger, approved layouts and exception/approval rules | Missing Inner Mirror references. Audit and compilation report issuance excluded. |
| M7 Reliability/security/UAT | M6 | Recovery, dependency control, confidentiality, Mac/browser and professional UAT | Verified restore, privacy and accessibility gates and signed acceptance | Software-vendor data and version drift. Hosting excluded. |
| M8 Commercial evaluation | M7 | Tenant/role model, licensing, identity, subscription and hosting assessment | Tenant isolation and privacy/licensing review before deployment decision | Concurrent access and commercial risk. Production rollout requires its own authorisation. |

## Acceptance criteria / verification

For each release record archive integrity and unchanged/changed inputs, compatibility and migration effects, executed test matrix and environment, redacted sample reports, security and source review, residual risks and owner sign-off. At M0 prioritise bank opening evidence, journal ID collisions, cash/noncash mapping, draft gates and official authority retrieval.

## Risks, limitations and open questions

Feasibility depends on approved datasets, Mac/browser access, primary rules and Accounting review. Resolve commercial scope and supported entity/period/layout list before committing to dates.

## Related documents

- [Product Requirements Prd](02_PRODUCT_REQUIREMENTS_PRD.md)
- [Test Strategy](18_TEST_STRATEGY.md)
- [Requirements Traceability](20_REQUIREMENTS_TRACEABILITY.md)
- [Open Questions](23_OPEN_QUESTIONS.md)
