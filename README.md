# Otto Financial Report Engine v1.4.0-dev.4

**Unreleased development branch:** Otto Auto is the default, with shared multi-bank review, transfer suggestions and provisional reporting. Build version is 1.4.0-dev.4; historical stable release remains 1.3.1; PR #21 is merged into its development base; no final release or accounting approval is implied. See [combined candidate usage and evidence](docs/29_AUTO_MULTI_BANK_INTEGRATION.md).

Otto helps Singapore businesses and their preparers assemble bookkeeping records, management accounts and draft unaudited financial statements (UFS). Lighthouse Studio Works Pte. Ltd. owns the product. **Clear Numbers for a Brighter Tomorrow.**

![Otto original logo](assets/otto_original_logo.png)

## Current service scope

Otto is for an SME service provider offering **bookkeeping and draft unaudited financial statements (UFS)** first. The historical v1.3.1 Guided workflow is **Company → Documents → Bank → Other records → Reports**. This development branch opens **Auto → upload → review account groups/exceptions → provisional reports**; select Guided or Advanced in the sidebar for detailed work. Company setup accepts manual details or an optional ACRA Business Profile, then confirms the financial year before accounting records are reviewed. Initial Company clearance covers company name, UEN and confirmed dates; further particulars and disclosures remain in the issue list for UFS preparation.

Corporate-secretarial workflows, audit services/automated audit-exemption assessment, tax preparation/filing and ACRA/XBRL submission are future scope, not current deliverables. Bookkeeping adjustments, reconciliation and the particulars needed for draft UFS remain supported. Audit exemption is informational guidance, separate from preparation and filing requirements.

## Future service model: external review and audit handoff (planned)

Otto is a **bookkeeping and financial statement preparation tool**, not an audit service. A small Singapore service provider may operate without employing an accountant or auditor, while engaging an external suitably experienced Singapore financial-reporting accountant on a case-by-case contract. Company directors remain responsible for the records, financial statements and approval of the final accounts.

For clients that require an audit, the **client company appoints an independent ACRA-registered public accountant / appropriate registered accounting entity** under a separate audit engagement. A future Otto workflow may supply an evidence-linked **audit-ready handoff package** (planned); the auditor independently decides the procedures, evidence requests and opinion. Otto must not issue or imitate an auditor's opinion, mark its reports `Audited`, or represent itself as an audit firm.

A professional **SSRS 4410 compilation engagement**, if commissioned, is separately scoped and reported by the engaged practitioner and provides **no audit assurance**. A formal assurance review under SSRE is also different from a preparer's quality-control check. Auditor independence must be evaluated by the appointed practitioner before accepting any combined preparation/audit arrangement; Otto does not decide independence automatically.

See [UFS preparation](docs/11_UFS_PREPARATION_AND_DISCLOSURES.md), [report specifications](docs/10_REPORT_SPECIFICATIONS.md), [Singapore compliance](docs/12_SINGAPORE_COMPLIANCE.md) and [roadmap](docs/19_DEVELOPMENT_ROADMAP.md). **Partner onboarding, professional sign-off workflow and audit-ready export are proposed features, not implemented in the current v1.3.1 release.**

## Review or remove uploaded files

In Guided **Documents** or **Bank**, review the **Flagged files — your decision** list. Open **Review or delete uploaded files**, select files, then choose **Retain selected files** or **Delete selected files**. Flags include exact duplicates, possible overlapping statement coverage, financial-year mismatches, different company UENs and uncertain relevance. Nothing is deleted automatically; supporting documents may still be useful. Retain choices last for this session. Deletion keeps saved accounting/evidence records and original disk files, and requires bank balances to be rechecked when a statement is removed.

## Follow issues through to clearance

The five Guided sections are tabs: green **Cleared**, amber **Needs attention**, grey **Not started**. Text and symbols accompany the colours. Each tab lists every current issue with its priority and next action. Select **Issue to handle** to read the full details, open the relevant tab or Advanced editor, and save progress notes as **Open** or **In progress**. Checks clear resolved items automatically, retain cleared history and reopen recurring problems. Missing source files leave historical bank-source issues in **Needs recheck**. Save the workspace ZIP to retain notes/history, or download the issue-list CSV. Progress and green labels do not approve accounting entries.

This release uses the verified dependency versions in `constraints-m0.txt`, including Streamlit 1.50.0. Python 3.9–3.12 is the declared runtime range; see the M0 verification record for tested platforms. The launcher installs the pinned requirements. Streamlit's developer controls occupy their own top strip above Otto branding.

## M0 stabilization

Startup checks for an incomplete release, unsupported Python and an occupied port before installing dependencies. If another Otto session uses port 8501, save its workspace ZIP and stop its Terminal with Control+C; Otto never stops it for you. To run a separate session, use `OTTO_PORT=8502 ./START_ON_MAC.command` and open the printed address. Subsequent launches reuse the verified environment offline. Changes to either requirements or constraints trigger a dependency recheck.

[The M0 verification record](docs/24_M0_STABILIZATION.md) lists completed checks and remaining acceptance work. Build a ZIP containing only committed source with `python3 scripts/build_release.py`; it includes `SOURCE_MANIFEST.json` and writes a `.zip.sha256` sidecar. Saved client data, local virtual environments and untracked files are excluded.

## Run locally

On macOS, unzip the release, open `START_ON_MAC.command` and keep Terminal open. Open <http://localhost:8501>. The launcher creates a local virtual environment and installs dependencies when needed. See the [current Quick Start](QUICK_START_v1.4.0-dev.4.md) for setup and troubleshooting.

For explicit local setup, use a supported Python 3 environment. Check compatibility with the selected dependency versions.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --browser.gatherUsageStats false
```

Use synthetic inputs in `example_imports/guided_demo/` or load the bundled demo from the sidebar. Save work using **Save my work (ZIP)** and retain original uploads separately in approved storage. The ZIP carries editable records and answers.

## Verified baseline and gaps

| Area | v1.2.4 evidence |
| --- | --- |
| Local workflow | Streamlit Guided default with five stages and shared Advanced workspace. Mac launcher and branding regression tests passed on Linux. A live Mac run remains pending. |
| Extraction | PDF text/tables, XLSX, XLS and CSV with review. Company and bank extraction use heuristics. Image-only PDFs require other evidence or a bank export. |
| Accounting | One SGD bank control account, deterministic double entry and static COA. Validation includes balances, bank arithmetic and receivables tie-out. Advanced keeps incomplete working drafts available. |
| Clarifications | Contextual questions and ZIP-persisted answers, plus client PDF and CSV. Journal correction requires a separate action. |
| Outputs | A4 management and company draft UFS PDF, XLSX workpapers and workspace ZIP. Comparatives, framework assessment and supporting disclosures need review. |
| Service boundaries | Bookkeeping, management accounts and draft UFS preparation. Corporate tax, ECI/Form C-S, GST, IRAS, ACRA filings and XBRL, audit/assurance, secretarial work and automatic compilation-report issuance are outside scope. |

## Audit and tests

On 20 November 2026 (Singapore baseline), the extracted archive ran **52 passing tests, 0 failures, 0 errors, 0 skips** under Linux using the command below. The audit covers source, fixtures, bundled outputs and existing documentation. See [Test strategy](docs/18_TEST_STRATEGY.md) for coverage and limitations.

```bash
python -m unittest discover -s tests -v
```

## Repository map

```text
app.py, guided.py, START_ON_MAC.command   Local UI and launcher
requirements.txt                          Python dependencies
engine/                                   Accounting, import, review and reports
tests/                                    Seven automated test modules
sample_company/                           JSON/CSV demo accounting package
example_imports/                          Synthetic intake and question examples
demo_output/                              Example PDF/XLSX/ZIP outputs
run_demo.py, make_*example*.py             Demo and fixture generators
assets/                                   Four supplied Otto PNGs
docs/                                     Documentation and archived release notes
```

The [v1.3.1 release note](RELEASE_NOTES_v1.3.1.md) covers Company-first setup and the focused service scope. The [v1.3.0 release note](RELEASE_NOTES_v1.3.0.md) covers upload review, the persistent issue tracker and coloured stage tabs. The [original v1.2.4 release note](RELEASE_NOTES_v1.2.4.md) and [earlier releases](docs/previous_releases/RELEASE_NOTES_v1.2.3.md) remain available.

## M0 baseline stabilisation — in progress

The canonical source baseline is GitHub `main` at commit `23e5b92def48a8d01a222fac8f1c570118a5c24d`, not the older v1.2.4 downloadable ZIP. The latest [GitHub Actions test run](https://github.com/jefftansg/Otto_Engine/actions/runs/44747199264) passed **73 automated tests**; however Mac/browser acceptance, reproducible release packaging, and accountant review of financial reports remain pending. **Do not describe M0 as complete or the draft UFS as approved.**

See [M0 Baseline Audit — Kickoff and Initial Findings](docs/milestones/M0_BASELINE_AUDIT_2026-11-20.md) for test evidence, risks, and acceptance checklist.

## Documentation

- [Product Vision](docs/01_PRODUCT_VISION.md)
- [Product Requirements Prd](docs/02_PRODUCT_REQUIREMENTS_PRD.md)
- [System Architecture](docs/03_SYSTEM_ARCHITECTURE.md)
- [Data Model](docs/04_DATA_MODEL.md)
- [Accounting Rules](docs/05_ACCOUNTING_RULES.md)
- [Document Extraction](docs/06_DOCUMENT_EXTRACTION.md)
- [Acra Company Profile](docs/07_ACRA_COMPANY_PROFILE.md)
- [User Workflows Ux](docs/08_USER_WORKFLOWS_UX.md)
- [Clarification Engine](docs/09_CLARIFICATION_ENGINE.md)
- [Report Specifications](docs/10_REPORT_SPECIFICATIONS.md)
- [Ufs Preparation And Disclosures](docs/11_UFS_PREPARATION_AND_DISCLOSURES.md)
- [Singapore Compliance](docs/12_SINGAPORE_COMPLIANCE.md)
- [Audit Exemption Eligibility](docs/13_AUDIT_EXEMPTION_ELIGIBILITY.md)
- [Accounting Framework Eligibility](docs/14_ACCOUNTING_FRAMEWORK_ELIGIBILITY.md)
- [Acra Filing Scope And Xbrl](docs/15_ACRA_FILING_SCOPE_AND_XBRL.md)
- [Regulatory Sources And Versioning](docs/16_REGULATORY_SOURCES_AND_VERSIONING.md)
- [Security And Privacy](docs/17_SECURITY_AND_PRIVACY.md)
- [Test Strategy](docs/18_TEST_STRATEGY.md)
- [Development Roadmap](docs/19_DEVELOPMENT_ROADMAP.md)
- [Requirements Traceability](docs/20_REQUIREMENTS_TRACEABILITY.md)
- [Release Notes](docs/21_RELEASE_NOTES.md)
- [Decision Log](docs/22_DECISION_LOG.md)
- [Open Questions](docs/23_OPEN_QUESTIONS.md)

## Planned Otto Auto experience (21 November 2026)

**Product direction, not implemented in v1.3.1:** a document-first default: upload bank statements, bookkeeping files and report templates; Otto identifies source-backed details and missing months; review only material exceptions; generate clearly labelled draft Management Accounts/UFS and workpapers. Advanced keeps detailed accounting controls on the same ledger. Optional AI interpretation proposes classifications but cannot post without approval or bypass deterministic reconciliations. The current Company-first five-stage Guided workflow remains unchanged in this release. See [Otto Auto specification](docs/25_AI_FIRST_AUTO_EXPERIENCE.md).

## Planned Otto Auto (21 November 2026)

**Not implemented in v1.3.1.** Target default: upload statements, bookkeeping and templates; automatically identify evidence-backed details and missing periods; review material exceptions; download draft Management Accounts/UFS/workpapers. Optional AI proposes categories, while humans approve postings and the deterministic ledger reconciles totals. Advanced retains full controls. Current Company-first Guided flow remains unchanged. See [Otto Auto specification](docs/25_AI_FIRST_AUTO_EXPERIENCE.md).

## Report layout quality — P0 requirement (21 November 2026)

Otto's target is **template-first reporting**, not a generic autogenerated PDF appearance. The original user-approved Management Accounts and UFS templates must define fonts, sizes, margins, table rules, pagination and section order. Report outputs require independent accounting validation **and** signed-off visual golden-master comparison. DOCX editing/export is proposed, not currently verified implemented. The historical reference templates are still required before claiming exact matching. See [Report Design System and Template Fidelity](docs/26_REPORT_DESIGN_SYSTEM_AND_TEMPLATE_FIDELITY.md).

## P0 reporting completeness — development direction (22 November 2026)

Lighthouse StudioWorks is the customer-facing Singapore SME bookkeeping and reporting provider; Otto is its internal engine, not a separately marketed software product. The intended management package includes cash flow reporting. Company UFS must include framework-appropriate primary statements, equity movements, cash flows, required comparatives, notes and Directors' Statement. Existing cash flow and equity working summaries require strengthening and acceptance, not greenfield development. No new implementation, compliance approval or release is asserted. See [financial statement completeness specification](docs/27_FINANCIAL_STATEMENT_COMPLETENESS.md).

## Multi-bank SGD development pilot (22 November 2026)

The development branch adds an explicit manual-entry multi-bank pilot, per-account reconciliations, reviewed transfer pairs, consolidated ledger/cash flows and draft PDF/XLSX changes. It is not a released feature. Automated bank detection, period coverage, migration and full acceptance remain pending. See [pilot specification](docs/28_MULTI_BANK_SGD_PILOT.md).

## Unreleased multi-bank SGD review candidate

The development pilot supports local supported-format bank identification/grouping, independent source coverage and bank reconciliation, reviewed transaction staging and explicit transfer suggestions. It remains Lighthouse StudioWorks' internal preparation engine. Existing single-account workspaces retain their workflow; migration is not automatic. See [pilot usage and acceptance gates](docs/28_MULTI_BANK_SGD_PILOT.md) and [verification evidence](docs/milestones/MULTI_BANK_SGD_REVIEW_2026-11-22.md). PR #21 is merged into development/ufs-report-completeness; follow-up fixes remain separately reviewed and the development build is **1.4.0-dev.4**; engineering test success does not approve UFS or template fidelity.

## Sidebar upload and OCBC daily-details correction

The unreleased candidate keeps Auto document upload near the top of the sidebar. OCBC daily-details account names come from the header, not transfer counterparties; Ledger Balance proposals require reconciliation, and exports printed before period-end remain incomplete. No ACRA document is required merely to identify the account holder; missing UEN stays unknown. [Fix and 189-test evidence](docs/30_OCBC_DAILY_HEADER_FIX.md).

## Monthly exports and later bank postings

In **1.4.0-dev.4**, supported OCBC daily-detail exports can contain transactions posted after the selected monthly export end. Original posting dates are retained. Printed balances/counts/totals, confirmed financial-year cutoffs and duplicate checks still apply; later postings do not extend source coverage. See [scope and validation](docs/34_LATE_BANK_POSTING_DATES.md).
