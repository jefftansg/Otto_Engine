# M0 stabilization record — Otto v1.3.1

Date: 20 November 2026 (Singapore). Scope: an engineering baseline for local bookkeeping and draft UFS preparation. This record does not certify UFS, audit exemption, filing compliance or commercial readiness.

## Relationship to the baseline audit

The [M0 baseline audit](milestones/M0_BASELINE_AUDIT_2026-11-20.md) defines the acceptance gates and remains in progress, not signed off. This document supplements its initial evidence with separately requested engineering changes and checks. It does not close professional UFS, independent golden-ledger, Finder/keyboard/mobile or Product-acceptance gates. Newer main-branch professional-partner and audit-handoff documentation is preserved as planned scope, with AGENTS.md's preparation/review/audit boundaries retained.

## Source and release identity

`scripts/build_release.py` builds from committed `HEAD`, not the working directory. Each release contains `SOURCE_MANIFEST.json` with its exact commit, version, file sizes and SHA-256 hashes; a sibling `.zip.sha256` file identifies the archive. The source-only ZIP excludes local environments, untracked files and saved client data. Launcher executable permissions are preserved. Two builds from the same commit are compared for byte identity during release verification. Prior release documentation remains historical evidence.

## Verified local matrix

| Check | Environment / evidence | Result |
| --- | --- | --- |
| Full regression suite | macOS 14.6 arm64, Python 3.9.6, Streamlit 1.50.0; existing installation | 100 passed; 0 failures/errors/skips |
| Clean dependency installation and suite | Fresh .venv; 95 tests initially, then expanded current-source suite | 100 passed; all installed versions match pins; pip check clean |
| First launcher start | Actual START_ON_MAC.command on isolated port 8513 | Healthy Streamlit endpoint after dependency installation |
| Offline relaunch | PIP_NO_INDEX=1, same environment and dependency fingerprint | Healthy endpoint; no dependency reinstall |
| Busy port | Start a second copy against a live test server | Clear failure before installation; original server stays healthy |
| Immediate restart | Stopped server leaves recently closed connections | Initial preflight failure found and fixed with SO_REUSEADDR; restart and active-listener rejection retested |
| Legacy saved workspace | Fictional sample_company files from commit 838565d in tests/fixtures/workspace-v1.2.4.zip | Restore, tracker initialization and ZIP round-trip preserve all tables and generated accounting results |
| Company-first UI | In-app browser against isolated port 8512; synthetic ACRA fixture | Company selected first; optional PDF accepted; field population requires explicit action |
| UI warning cleanup | Full AppTest suite after width-argument migration | No use_container_width deprecation messages |
| Cross-platform CI | [Run 44752853119](https://github.com/jefftansg/Otto_Engine/actions/runs/44752853119), head 432f43c | 100 tests and pip check passed on each of all three configured environments |
| Shell syntax | zsh -n START_ON_MAC.command | Passed |

Dependency pins describe the tested environment. The declared Python range is 3.9–3.12; CI exercises Linux 3.9/3.12 and macOS 3.12. The compatibility matrix uses Ubuntu 22.04/Python 3.9, Ubuntu 24.04/Python 3.12 and macOS 15/Python 3.12 with Node 24 actions. Moving ubuntu-latest no longer provided Python 3.9, and the macOS 14 hosted image had retired; those configuration failures were diagnosed before the compatible runner update. Ubuntu 22.04 legacy coverage will need migration before its announced retirement. The [verified CI run](https://github.com/jefftansg/Otto_Engine/actions/runs/44752853119) for source head `432f43c` passed all three jobs: Ubuntu 22.04/Python 3.9, Ubuntu 24.04/Python 3.12, and macOS 15/Python 3.12. Each job ran 100 tests and pip check successfully. Later PR checks identify the final documentation/release commit; no unrun platform is inferred from local success. There is no claim of a fresh physical Mac/Finder double-click or a network-disconnected computer test; offline testing disabled package-index access after dependencies were installed.

## Current candidate report and ledger QA

The source candidate regenerated `run_demo.py --input sample_company` with **0 blocking errors and 5 retained review warnings**. Technical review rendered all **12 management-account PDF pages, 5 UFS PDF pages and 16 workbook sheets**. All PDF text stayed within page bounds, draft markings and review messages remained visible, and no obvious page/table overlap was found. Excel cached results and formula text tie to independent sample controls: bank/assets 1,768; liabilities 650; equity 1,118; revenue 1,500; expenses 482; profit 1,018; trial-balance totals 2,250 each; operating cash 1,268 plus financing 500 equals closing bank 1,768. Workbook error scan found no formula error cells. The [report QA inventory](milestones/M0_REPORT_QA_v1.3.1.json) records file hashes and engine source blobs. Technical QA is not professional review of recognition, framework, disclosures or compliance.

The Artifact workbook preview displayed shared-string index `91` in a few cells whose source value is the empty string. Independent inspection of the saved XLSX confirmed the original blank cells are correct; no source workbook change was made. Native Excel/Safari/Finder testing remains pending, so these previews are not native-application proof.

Additional literal-amount regression vectors are in `tests/test_m0_golden_ledgers.py`:

| Vector | Independent expected outcome |
| --- | --- |
| First-year director loan 1,000 | Bank 1,000; liability 1,000; profit 0; financing cash 1,000, no sales |
| Supported opening cash/equity 500, then software payment 100 | Closing cash/equity 400; profit -100; operating cash -100; absent opening counterpart triggers errors without inventing capital |
| Cash 100 with mixed sales 60 / director loan 40 manual journal | Mixed-classification error; 100 remains Unallocated for review, not guessed into categories |
| Accrual 80 and its supported reversal | Both journal IDs and four lines retained; net profit/liability/cash zero |
| Manual adjustment after year end | Both late lines rejected; zero posted entries and profit |

These are engineering controls, not professionally accepted golden ledgers for every accounting scenario. M0-03/04/05 remain subject to the baseline audit's broader acceptance gate.

## Open acceptance and known limitations

| Item | Owner | Status / boundary |
| --- | --- | --- |
| Real company/date confirmation and professional UFS review | User/preparer | Manual acceptance remains. Automatic approval review blocked clicking the browser's records/director attestation. Synthetic AppTest covers the form without claiming real verification. |
| Keyboard-only and narrow-screen operation | Otto maintainer / user | Not yet manually verified. Native tabs include readable status text and symbols. |
| Other historical client ZIPs | User/preparer | One baseline synthetic schema fixture is verified; no claim about every historical archive or real client layout. |
| Wider bank layouts and complete UFS disclosures | User/preparer | Existing known limitations remain in the requirements register; draft labels and existing import/report gates remain. |
| Dependency updates and licence/security review | Otto maintainer | Pins are engineering reproducibility evidence, not an independent licence or vulnerability audit. Refresh pins only after rerunning the relevant matrix. |
| Additional services | Product owner | Corporate-secretarial, audit services/automated audit assessment, tax filing and ACRA/XBRL submission remain future scope. |

## Reproduction

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -m unittest discover -s tests -v
zsh -n START_ON_MAC.command
python3 scripts/build_release.py
```

Use a free port for a separate smoke-test session: `OTTO_PORT=8513 ./START_ON_MAC.command`. Save any real workspace ZIP before stopping its running process. The launcher never kills another application.
