# Otto Financial Report Engine v1.3.0

Otto helps Singapore businesses and their preparers assemble bookkeeping records, management accounts and draft unaudited financial statements (UFS). Lighthouse Studio Works Pte. Ltd. owns the product. **Clear Numbers for a Brighter Tomorrow.**

![Otto original logo](assets/otto_original_logo.png)

## Review or remove uploaded files

In Guided **Upload** or **Bank**, review the **Flagged files — your decision** list. Open **Review or delete uploaded files**, select files, then choose **Retain selected files** or **Delete selected files**. Flags include exact duplicates, possible overlapping statement coverage, financial-year mismatches, different company UENs and uncertain relevance. Nothing is deleted automatically; supporting documents may still be useful. Retain choices last for this session. Deletion keeps saved accounting/evidence records and original disk files, and requires bank balances to be rechecked when a statement is removed.

## Follow issues through to clearance

The five Guided sections are tabs: green **Cleared**, amber **Needs attention**, grey **Not started**. Text and symbols accompany the colours. Each tab lists every current issue with its priority and next action. Select **Issue to handle** to read the full details, open the relevant tab or Advanced editor, and save progress notes as **Open** or **In progress**. Checks clear resolved items automatically, retain cleared history and reopen recurring problems. Missing source files leave historical bank-source issues in **Needs recheck**. Save the workspace ZIP to retain notes/history, or download the issue-list CSV. Progress and green labels do not approve accounting entries.

Requires Streamlit 1.50 or later. The launcher installs the updated requirements. Streamlit's developer controls occupy their own top strip above Otto branding.

## Run locally

On macOS, unzip the release, open `START_ON_MAC.command` and keep Terminal open. Open <http://localhost:8501>. The launcher creates a local virtual environment and installs dependencies when needed. See the [v1.3.0 Quick Start](QUICK_START_v1.3.0.md) for setup and troubleshooting.

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

The [v1.3.0 release note](RELEASE_NOTES_v1.3.0.md) covers upload review, the persistent issue tracker and coloured stage tabs. The [original v1.2.4 release note](RELEASE_NOTES_v1.2.4.md) and [earlier releases](docs/previous_releases/RELEASE_NOTES_v1.2.3.md) remain available.

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
