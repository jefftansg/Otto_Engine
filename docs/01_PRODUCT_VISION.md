# Product vision

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Draft
- Owner: Product
- Related requirements: OTTO-BASE-001, OTTO-UX-001, OTTO-REP-001, OTTO-UFS-001
- Sources/evidence: README.md, app.py, assets/, engine/reports.py

## Purpose and scope

Lighthouse Studio Works Pte. Ltd., Singapore owns Otto Financial Report Engine. Its tagline is **Clear Numbers for a Brighter Tomorrow**. Otto helps small business owners assemble records, gives bookkeepers reviewable classifications and workpapers, and gives directors and accountants a traceable preparation draft. Service providers need repeatable work across clients. Sole proprietors need business management reporting suited to their entity type.

## As-is implementation (evidence-backed)

The Python/Streamlit bundle prepares local SGD management reports and company-form draft UFS. The four supplied Otto PNG assets include the original logo and assets used for the mascot, sidebar and favicon. The brand direction is navy and teal. Settings, rules and manual review drive computation.

## Current operator and release focus — v1.3.1

The user operates an SME service offering bookkeeping and UFS preparation first, rather than a corporate-secretarial practice with an audit/accounting team. Keep the initial workflow Company → Documents → Bank → Other records → Reports. Company name, UEN and financial year precede general accounting intake; optional ACRA extraction can assist setup without requiring a secretarial workflow. Keep reconciliation, adjustments, disclosures and client questions needed for draft UFS. Corporate-secretarial workflows, audit services and automated audit-exemption assessment, tax filing and ACRA/XBRL submission are deferred capabilities requiring a separate future scope decision.

## To-be requirements

Position Otto as a preparation tool for two services: bookkeeping and management accounts, and preparation of UFS from accounting records. Exclude corporate income tax computations, ECI, Form C-S, GST returns, IRAS submissions, ACRA annual returns, XBRL filing, corporate secretarial work, assurance and automatic SSRS 4410 reports. AI assistance, if approved, proposes classifications or evidence requests subject to human review.

## Acceptance criteria / verification

Benchmark against the same fictional cases prepared manually. Measure median preparer minutes from intake to clean draft, percentage of material lines tied to source, reconciliation exceptions per case, time to resolve client queries and number of unsupported assumptions detected on review. Successful pilot requires full source traceability for sampled material lines, zero silent posting and zero unresolved arithmetic errors in the authorised cohort. Set time targets after measuring the baseline.

## Risks, limitations and open questions

Multiple-client operation needs identity and storage controls. Draft arithmetic checks cover only supplied data. Director responsibility and professional review apply throughout.

## Related documents

- [Product Requirements Prd](02_PRODUCT_REQUIREMENTS_PRD.md)
- [User Workflows Ux](08_USER_WORKFLOWS_UX.md)
- [Development Roadmap](19_DEVELOPMENT_ROADMAP.md)
