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

## Current priority override — v1.3.1

Focus near-term delivery on the user's first two services: bookkeeping and draft UFS preparation. Company-first setup and a simple single-preparer workflow precede broader service expansion. Retain reconciliations, corrections, UFS particulars/disclosures and reliable exports as core work. Corporate-secretarial workflows, audit services/automated audit-exemption assessment, tax preparation/filing and ACRA/XBRL submission are future scope requiring a new product decision. The milestone table is a historical backlog; it does not authorise those expansions or make the eligibility-suite milestones prerequisites to the current service offering.

## M0 stabilization checkpoint — v1.3.1

Engineering verification now covers pinned dependencies, clean/offline Mac launch, safe occupied-port handling, runtime/source preflight, old-schema workspace/report preservation, 100 local tests and reproducible source-release inventory. CI adds Linux 3.9/3.12 and macOS 3.12 checks; consult the current PR for actual results. [M0 record](24_M0_STABILIZATION.md) names residual checks and owners. This is an engineering baseline, not professional UFS approval or a production-service launch. Keyboard/mobile acceptance, manual attestation and all historical ZIPs remain outside the verified evidence.

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

## Additions to milestones: external review and audit handoff (planned)

- **M5 — Compliance design:** define role/engagement distinctions, contractor competence, directors' duties, auditor registration/independence escalation, and the difference between ordinary accountant quality review, SSRS 4410 compilation, SSRE assurance review and SSA audit.
- **M6 — Reporting controls:** optional contracted accountant review and findings, management-approved adjusting entries, disclosure review and immutable directors' approval of financial statement revisions (OTTO-SVC-001 and OTTO-UFS-003).
- **M7 — Audit-ready output:** consent-restricted read-only evidence bundle, hashes, ledger-to-document traceability, reconciliation/exception completeness, auditor requests and disclosed data log (OTTO-AUD-001/002); external Singapore accountant and registered auditor UAT.
- **M8 — Commercial partnership:** optional fixed-fee outsourced accountant review and auditor referral/coordination, appropriate professional contracts, and **separate client engagement** of the independent auditor (OTTO-SVC-002). No Otto audit opinion, formal compilation issuance, tax filing or XBRL filing.

Do not infer deployment or commercial-service readiness from these documented plans. Human review and assurance responsibilities remain with the respective professionals.

## M0 execution status — started 20 November 2026

**Status: In progress; not signed off.** GitHub `main` commit `23e5b92` is the technical source baseline. The latest Ubuntu/Python 3.12 CI run passed 73 automated tests, but live Mac UAT, current-main PDF/XLSX visual checks, versioned package provenance, and independent accounting sign-off remain outstanding.

See the [M0 Baseline Audit](milestones/M0_BASELINE_AUDIT_2026-11-20.md) for the reproducible test evidence, 10 prioritised findings, acceptance gates and Mac manual test checklist. The initial kickoff alone did not authorise source changes. Subsequent user-requested engineering stabilization and its evidence are recorded separately in the M0 supplement; no accounting-policy change or future-scope expansion is implied.

## Acceptance criteria / verification

For each release record archive integrity and unchanged/changed inputs, compatibility and migration effects, executed test matrix and environment, redacted sample reports, security and source review, residual risks and owner sign-off. At M0 prioritise bank opening evidence, journal ID collisions, cash/noncash mapping, draft gates and official authority retrieval.

## Risks, limitations and open questions

Feasibility depends on approved datasets, Mac/browser access, primary rules and Accounting review. Resolve commercial scope and supported entity/period/layout list before committing to dates.

## Related documents

- [Product Requirements Prd](02_PRODUCT_REQUIREMENTS_PRD.md)
- [Test Strategy](18_TEST_STRATEGY.md)
- [Requirements Traceability](20_REQUIREMENTS_TRACEABILITY.md)
- [Open Questions](23_OPEN_QUESTIONS.md)

## Otto Auto priority after M0 (21 November 2026)

Prioritise document-first UX over peripheral modules once M0 is validated: (1) upload-first prototype, (2) deterministic source inventory/coverage/deduplication, (3) AI classification proposals with human approval, (4) consolidated exceptions and draft reporting, (5) synthetic regression, Mac/browser usability and accountant pilot. Planned only; no delivery claims for v1.3.1. See [Otto Auto specification](25_AI_FIRST_AUTO_EXPERIENCE.md).

## P0 priority correction — report fidelity first (21 November 2026)

Before polishing the proposed Otto Auto workflow, secure the old approved MA/UFS report templates, define a canonical layout/style schema, reproduce their typography/spacing/table design deterministically and pass golden-master visual and accounting checks. Preserve the M0 stability gate. Otto Auto can then simplify intake while reusing the approved report renderer. Planned, no implementation claimed. See [Report Design System](26_REPORT_DESIGN_SYSTEM_AND_TEMPLATE_FIDELITY.md).
