# M0 Baseline Audit — Kickoff and Initial Findings

- **Product:** Otto Financial Report Engine
- **Review date:** 20 November 2026 (Singapore)
- **Milestone:** M0 — Baseline Stabilisation / audit
- **Status:** **In progress; initial technical baseline established, release gate NOT approved**
- **Source of truth:** [GitHub main](https://github.com/jefftansg/Otto_Engine) at commit `23e5b92def48a8d01a222fac8f1c570118a5c24d`
- **Initial kickoff code-change scope:** None. The kickoff recorded evidence and acceptance criteria. The user later explicitly requested Company-first UI changes and M0 stabilization; those implementation/verification results are recorded separately below. This does not waive any release gate.
- **Baseline version printed by launcher:** v1.2.4; GitHub contains additional changes after the older downloadable v1.2.4 ZIP.

## Executive assessment

**Automated checks for current GitHub main pass, but M0 is not yet signed off.** The latest [GitHub Actions Python tests run](https://github.com/jefftansg/Otto_Engine/actions/runs/44747199264), triggered by the merge commit above on 20 November 2026, completed successfully on Ubuntu / Python 3.12: **73 tests passed** (`python -m unittest discover -s tests -v`; job `136325458788`). The CI workflow installs `requirements.txt` and runs this unittest discovery. It does not run a real macOS desktop/browser end-to-end test.

An older, separately uploaded release archive `Otto_Financial_Report_Engine_v1.2.4_Mac.zip` was also tested locally as a **comparison fixture, not a copy of current main**. SHA-256: `5ecd9e6baaf17b65023e22223f75032ce0026cf33490b4e08fe888e93760187c`. ZIP integrity passes. Using Python 3.13.5 on Linux x86-64, its **52 tests passed after restoring the launcher executable bit**. A normal extraction in this environment initially stripped that bit (51 pass, 1 launcher-permission failure); the ZIP entry itself retains Unix mode `0755`. This does **not** demonstrate a Mac installation defect; verify with Finder and `unzip` on a real Mac.

The older archive's sample report command `python run_demo.py --input sample_company --output <scratch>` generated:
- `Management_Accounts_DRAFT.pdf`: **12 A4 landscape pages**
- `Unaudited_FS_DRAFT.pdf`: **5 A4 portrait pages**
- `Financial_Workpapers_DRAFT.xlsx`: **16 sheets**
- **0 blocking errors and 5 professional-review warnings**, covering statement-balance confirmation, financial-year confirmation, framework eligibility, director review and disclosures.

These numbers establish regression evidence for **the old archive only**. The live repository has a different `app.py`, `guided.py`, `engine/core.py`, `engine/reports.py` and test files, plus new upload-review/deletion files. Do not represent the older archive sample run as a rendering test of commit `23e5b92`.

## Repository inventory and build environment

| Area | Current GitHub main evidence |
| --- | --- |
| UI | `app.py` (Streamlit), `guided.py` (Guided five-stage intake and Advanced routing) |
| Accounting | `engine/core.py` (SGD, deterministic double entry, static chart of accounts) |
| Imports and automation | `engine/importers.py`, `engine/autofill.py`, `engine/intake_review.py`, `engine/attention.py`, `engine/clarifications.py` |
| Outputs | `engine/reports.py` (PDF and Excel draft reports) |
| Automated tests | Nine `tests/test_*.py` files; CI count 73 |
| Mac entry point | `START_ON_MAC.command`, `requirements.txt` |
| Test infrastructure | `.github/workflows/tests.yml`: Ubuntu Python 3.12 on pull request and push to main |
| Documentation | `README.md`, `AGENTS.md`, existing 23 numbered `docs/*.md` files and release files |
| Fixtures | Fictional `sample_company/` and `example_imports/` |
| Visual assets | Original Otto logo, mascot, icon and wordmark in `assets/` |
| Dependency policy | Version **ranges**, not a fully locked hash-resolved environment: `streamlit>=1.35,<2`, `reportlab>=4.0,<5`, `xlsxwriter>=3.1,<4`, `openpyxl>=3.1,<4`, `xlrd>=2.0,<3`, `pdfplumber>=0.11,<1` |

**Caveat:** GitHub CI validates the current tree, while the locally recreated release ZIP validates the older packaged source. No full local checkout of the current GitHub main was executed in the isolated environment; GitHub Actions is the live-tree test evidence. Verify the precise tested requirements in [Test strategy](../18_TEST_STRATEGY.md), which distinguishes current tests from planned cases.

## Priority stability findings and release blockers

| ID | Priority | Evidence / issue | Owner | Required M0 action |
| --- | --- | --- | --- | --- |
| M0-01 | **P0** | **Working baseline drift:** current `main` contains code beyond the published v1.2.4 ZIP, despite the launcher retaining the v1.2.4 label. Core/UI/report files differ by Git blob SHA. | Engineering / Product | Select and label a canonical release commit and reproducible downloadable build; record exact build ↔ commit provenance. |
| M0-02 | **P0** | **No current-main Mac UAT:** Ubuntu CI passes but Finder launcher, browser upload controls, keyboard flow, downloads, save/restore and offline relaunch remain unverified for commit `23e5b92`. | Engineering / Mac tester | Complete signed Mac test sheet below with evidence. |
| M0-03 | **P0** | **Draft financial reports not ready for issue:** current `generate()` warns on framework, director review and missing disclosures. PDF output remains a draft and no professional financial-statement compliance conclusion has been established. | Accounting / Compliance | Review current-main sample PDF/XLSX together and validate statement and disclosure completeness for selected entity/framework. |
| M0-04 | **P0** | **Opening balances:** `generate()` requires bank statement opening and closing balances and ties them to ledger opening/closing values. Unproven opening counterpart cannot safely be inferred. | Accounting / Engineering | Run first-year and migrated-opening fixtures, including director funding/share capital, missing opening data and conflicting bank statements. |
| M0-05 | **P0** | **Journal and cash-flow integrity:** current core detects cross-source journal-ID collisions and errors on cash movements mapped to Noncash/Unallocated categories. Full mixed-cash and adjustment regression coverage remains incomplete. | Accounting / Engineering | Document golden test vectors for reversals, mixed journal legs, cash/noncash entries and reference collisions; reproduce any defect before fixing. |
| M0-06 | **P0** | **Original uploaded evidence is not restored from workspace ZIP:** README states editable tables and answers are saved, while original documents must be retained separately. | Product / Security | Add explicit user-facing backup/retention acceptance check; test restore without originals and ensure missing evidence is not shown as available. |
| M0-07 | P1 | **Document parsing coverage:** text PDF tables, CSV, XLSX and XLS; scanned/image-only PDFs cannot be posted automatically. Unrecognised layouts and partial PDF page inspection need review. | Engineering / Accounting | Define supported bank/document test matrix; check row counts, missed pages, duplicates, statement continuity and rejected-import nonmutation. |
| M0-08 | P1 | **Dependency and installation drift:** version-range dependencies and CI's Linux Python 3.12 do not prove repeatability or Python 3.9+/Mac compatibility; runner logged Node 20 deprecation for Actions. | Engineering | Capture dependency versions and requirements hash for release; test supported macOS/Python variants; schedule CI action updates separately. |
| M0-09 | P1 | **Legal/regulatory rules not implemented:** audit exemption, reporting framework selection, year-specific disclosures and filings are independently documented but not certified or automatically assessed. | Compliance / Accounting | Keep unimplemented status in PRD, block regulatory certification wording, verify official sources before M5/M6. |
| M0-10 | P1 | **No production-grade multitenancy or approval ledger:** local-first single workspace, draft reports and limited preservation of review history; external accountant/audit handoff remains planned. | Product / Security | Preserve scope boundaries; defer roles, audit-ready exports, workflow approvals and commercial deployment to their roadmap milestones. |

The highest-risk areas derive from direct reading of current `engine/core.py`, `engine/importers.py`, `guided.py` and `engine/reports.py`, plus the [existing gap register](../23_OPEN_QUESTIONS.md). **These are risks, coverage gaps or limitations, not all verified software defects.** Do not assign a passing/failing defect status without a reproducible test.

## M0 verification matrix and acceptance criteria

| Check | Evidence presently available | Gate |
| --- | --- | --- |
| Source inventory / main commit recorded | Commit `23e5b92`, GitHub tree and source list | **Pass (initial)** |
| CI regression tests against current main | 73/73 passed, GitHub Actions run `44747199264` | **Pass** |
| Older ZIP integrity / 52 tests | ZIP checksum, test run after `chmod +x` | **Pass (older package only)** |
| Current-main sample PDF / Excel regeneration and visual review | Not executed locally for current main | **Pending** |
| Bank reconciliation and cash-flow independent golden ledgers | Existing automated subset; broader vectors not executed | **Pending** |
| Old saved-workspace ZIP compatibility with current main | No cross-version restore run | **Pending** |
| Mac Finder launch, first-run install, offline reopen | Not observed on current main | **Pending** |
| Real browser file picker, multiple PDFs/CSV/XLS/XLSX, delete/retain | Streamlit AppTest + synthetic tests; no human browser test | **Pending** |
| Professional UFS and Singapore compliance review | No signed accounting/compliance acceptance | **Pending** |
| Release provenance, signed residual-risk record and Product approval | Not recorded | **Pending** |

### Mac UAT checklist (perform on a safe fictional workspace)

- [ ] Record Mac model/chip, macOS version, Python version, Chrome/Safari versions and commit/build identifier.
- [ ] On a clean unzip, double-click `START_ON_MAC.command`; verify the executable bit and first-run dependency installation.
- [ ] Verify `http://localhost:8501` launches Guided Mode; sidebar and Otto logo display; Advanced routing works.
- [ ] Upload fictional ACRA PDF plus bank PDF, CSV, XLS and XLSX, including duplicate copies and unsupported/scanned examples.
- [ ] Confirm the FY and bank statement period, test missing months, overlaps, wrong UEN and arithmetic mismatch handling.
- [ ] Check that deletion/retention affects proposed uploads only, without silently modifying posted entries or records.
- [ ] Import confirmed transactions, classify them, verify journal/TB/bank tie-outs; enter and reverse a manual adjustment.
- [ ] Generate PDF/XLSX drafts, visually check all pages (no truncation), note any warnings and compare key figures to independent calculations.
- [ ] Save workspace ZIP, close browser and Terminal, reopen offline and restore; confirm questions, entries and warnings persist.
- [ ] Confirm original uploaded files **are not assumed preserved** by the workspace ZIP, and client records remain private to the local machine.

**Completion rule:** M0 is not complete solely because all automated tests pass. Owner sign-off requires the supported platform matrix, independent accounting checks, reproducible build provenance, a resolved/accepted defect register, and no unacknowledged P0 release blockers. Do not market the current outputs as audited, approved, or automatically Singapore-standards-compliant.

## Suggested M0 handoff artefacts

1. A canonical commit/tag ↔ downloadable build manifest with checksum and exact dependency versions.
2. Fresh current-main test transcript and archived CI link.
3. Redacted/fictional golden ledger fixtures and document-import cases, with explicit expected amounts.
4. Mac UAT run and screenshot/video evidence, recording pass/fail/blocked.
5. Accountant-reviewed report pack and a concise accepted-risk/defect list.
6. Formal M0 sign-off by Product and Engineering, with Accounting/Compliance approval for financial reporting assumptions.

## Subsequent engineering stabilization — v1.3.1 candidate

The Company-first, issue-tracker and version-label changes were separately requested by the user before the explicit instruction to carry on M0 stabilization. [Run 44752853119](https://github.com/jefftansg/Otto_Engine/actions/runs/44752853119) passed 100 tests and pip check in each of the three compatible CI environments at candidate head `432f43c`. [The stabilization record](../24_M0_STABILIZATION.md) records the updated local evidence; the initial 73-test/main and older-archive evidence above remains historical.

| Finding | Updated evidence | Remaining boundary |
| --- | --- | --- |
| M0-01 provenance | v1.3.1 app/launcher/docs; committed-source ZIP builder, per-file manifest and SHA-256 sidecar; repeat builds compared byte-for-byte | Product selects/approves the release candidate; no GitHub Release or tag is published automatically |
| M0-02 Mac UAT | 100 tests on macOS 14.6 arm64 / Python 3.9.6, repeated on a clean dependency install; shell-invoked first launch, safe busy-port handling and offline relaunch verified | Finder double-click, keyboard/mobile, full file-format/manual workflow and real attestations remain pending |
| M0-03 draft reports | Current candidate demo pack regenerated with 0 blocking errors and 5 retained review warnings; technical visual/data QA is recorded in the stabilization record | No professional UFS/disclosure or compliance approval is inferred |
| M0-04/05 accounting | Opening, journal collision and cash/noncash regressions plus five hand-calculated funding/opening/mixed-cash/reversal/cutoff vectors pass; legacy restore preserves outputs | Broader independent golden ledgers and professional acceptance remain pending |
| M0-06 evidence restore | Legacy synthetic ZIP plus issue-history/missing-source tests pass; original source files remain excluded and the UI explains retention | Real client record-retention acceptance remains with the preparer |
| M0-07 parsing | Synthetic duplicate/rejection/cutoff and optional ACRA browser upload checks pass | No claim of all bank layouts, all formats or scanned OCR support |
| M0-08 dependencies | Exact dependency constraints; pip check; clean install and cached offline launch; CI matrix extended | Check current PR results for Linux 3.9/3.12 and Mac 3.12; no unrun platform is certified |
| M0-09/10 scope | Audit/secretarial/tax/filing expansion and professional-partner/audit-handoff features remain future/planned | No regulatory certification, multi-tenant deployment or external evidence sharing introduced |

**M0 remains in progress and not signed off.** Engineering stabilization does not replace the completion rule or human acceptance above. Dates in the browser were not attested by the agent after automatic approval review rejected that action; synthetic AppTest covers form mechanics only.

## Out-of-scope work until M0 acceptance

No new product features, AI classification refactor, automated audit-exemption certification, tax/GST/ACRA/XBRL filing, multi-tenant deployment, accountant portal, independent audit procedures, audit opinion generation, or audit-ready package implementation as part of this initial baseline.

## Links

- [Product requirements](../02_PRODUCT_REQUIREMENTS_PRD.md)
- [Accounting rules](../05_ACCOUNTING_RULES.md)
- [Test strategy](../18_TEST_STRATEGY.md)
- [Roadmap](../19_DEVELOPMENT_ROADMAP.md)
- [Traceability](../20_REQUIREMENTS_TRACEABILITY.md)
- [Open questions](../23_OPEN_QUESTIONS.md)
- [GitHub Actions verification run](https://github.com/jefftansg/Otto_Engine/actions/runs/44747199264)
