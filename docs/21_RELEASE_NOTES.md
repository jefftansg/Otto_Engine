# Release notes

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Verified
- Owner: Engineering
- Related requirements: OTTO-BASE-001, OTTO-QA-001
- Sources/evidence: RELEASE_NOTES_v1.3.1.md, RELEASE_NOTES_v1.3.0.md, RELEASE_NOTES_v1.2.4.md, docs/previous_releases/, START_ON_MAC.command, app.py, assets/, tests/

## Purpose and scope

Record what the supplied release verifies and what shipped historical notes report.

## As-is implementation (evidence-backed)

The current app, sidebar, launcher, README and Quick Start identify v1.3.1. The v1.2.4 baseline audit and historical release notes are retained below. Source confirms Otto page title, PNG branding assets, default Guided path, Otto ZIP download name and branded PDF code. README and [release note](../RELEASE_NOTES_v1.2.4.md) describe the branding release as based on v1.2.3. Independent historical source trees were unavailable, so the stated change history is attributed to the bundled notes.

| Release | Archive record and described focus |
| --- | --- |
| v1.1 | [Release note](previous_releases/RELEASE_NOTES_v1.1.md) for guided intake and multi-format uploads. |
| v1.2 | [Release note](previous_releases/RELEASE_NOTES_v1.2.md) for smart intake. |
| v1.2.1 | [Release note](previous_releases/RELEASE_NOTES_v1.2.1.md) for Guided Mode. |
| v1.2.2 | [Release note](previous_releases/RELEASE_NOTES_v1.2.2.md) for clarification questions. |
| v1.2.3 | [Release note](previous_releases/RELEASE_NOTES_v1.2.3.md) for attention routing and checks. |
| v1.3.1 | [Release note](../RELEASE_NOTES_v1.3.1.md): Company-first SME setup and M0 startup/dependency/release stabilization. |
| v1.3.0 | [Release note](../RELEASE_NOTES_v1.3.0.md): upload review/deletion, persistent issue tracker, coloured native tabs, toolbar clearance and prominent engine-version labels. |
| v1.2.4 | [Release note](../RELEASE_NOTES_v1.2.4.md) and current inspected source for branding and local drafts. |

## v1.3.0 — upload review and deletion (20 November 2026)

User-requested changes on `codex/delete-uploaded-files`, based on commit `838565d`:

- Guided Upload and Bank steps show a flagged-file list and let the user retain or delete selected files. No automatic deletion.
- Exact byte duplicates are flagged, including renamed copies. Retrying the same filename/content is idempotent. Overlapping same-account statement periods are flagged as possible duplicates, not proven duplicates.
- Flag statements wholly or partly outside a confirmed financial year, ACRA profiles with a different UEN, and unreadable/unrecognised documents. Uncertain relevance is explicitly labelled; supporting, opening and comparative evidence may be useful.
- Retaining records the decision for the current reasons in this session. A changed reason requires a fresh decision. Decisions and source files are not included in workspace ZIPs.
- Deletion removes only selected session uploads, resets the uploader to prevent automatic restoration, clears cached inspections, and refreshes proposals. Saved company details, transactions, evidence and historical extraction registers remain. Removing a recognised/registered bank statement revokes balance confirmation. Bank amounts remain available for review.
- Exact duplicate statement content contributes only one set of proposed bank rows. Existing duplicate, cutoff, reconciliation and approval gates still apply.
- No workspace schema migration, accounting policy change, external publishing or deployment. Advanced retains its existing uploader removal controls.

Verification: macOS arm64, Python 3.9.6, Streamlit 1.50.0, isolated temporary virtual environment. `/private/tmp/otto-delete-venv/bin/python -m unittest discover -s tests -v`: **73 passed, 0 failures, 0 errors, 0 skips**. Includes Streamlit AppTest for Guided Upload/Bank deletion, retain-then-delete and Advanced entry. Synthetic fixtures only; no real client uploads inspected. Browser file-picker interactions and older release ZIP archives have not been manually verified. Existing Streamlit width deprecation warnings remain.

## v1.3.0 — issue tracker and stage navigation (20 November 2026)

- Replace five command-style stage buttons with native Upload, Company, Bank, Other records and Reports tabs. Existing Continue and issue actions select their destination tab. Streamlit minimum is now 1.50 for the supported tab default parameter.
- Tab labels include both colour and text: green/Cleared, amber/Needs attention and grey/Not started. Status derives from current data, confirmations, outstanding questions, document-review decisions and existing checks. Regression reopens a stage. These indicators do not grant approval or change existing report-download gates.
- Every clarification question is listed individually; extraction and uncategorised question caps are removed. Grouped validation and source issues expose all details, with no two-message truncation.
- All five tabs show the full issue list, priority, status and next action. Select an issue to see its details, route to the correct tab or Advanced editor, record Open/In progress notes, recheck or export CSV. No manual Clear bypass is provided.
- `company.json` stores optional `issue_register` with first/last observation, notes, transition history and cleared timestamps. Current checks clear issues; recurrence reopens them. Missing bank source files leave previously raised source-dependent issues in Needs recheck. Older ZIPs acquire the register on first Guided use; existing source PDFs remain excluded.
- Reserve a separate top toolbar strip with 5.5rem of main-content clearance so Streamlit developer controls do not overlap Otto branding. Browser bookmark tooltips are outside the app.

Validation: macOS arm64, Python 3.9.6, Streamlit 1.50.0. `/private/tmp/otto-delete-venv/bin/python -m unittest discover -s tests -v`: **86 passed, 0 failures, 0 errors, 0 skips**. Covers lifecycle/reopen, rejected manual clear, missing-source restore, legacy package initialization, ZIP/CSV persistence, unchanged accounting totals, complete question/detail lists, tab rendering, progress/action routing, and green-to-amber regression. A local browser preview verified native tab switching, issue-to-Company routing and logo clearance. Synthetic fixtures only. Manual keyboard, narrow-screen and every supported historical release archive remain unverified. Existing Streamlit container-width deprecation warnings remain.

## v1.3.1 — Company-first SME preparation

Company is the first/default tab, followed by Documents, Bank, Other records and Reports. Company accepts manual setup and an optional ACRA PDF; extraction still requires an explicit apply action and date confirmation. Initial Company clearance depends on name, UEN and confirmed dates. Document flags, issue actions, source-recheck links, navigation colours and the sidebar follow the new order. Company forms precede the issue list. Service scope is bookkeeping and draft UFS preparation; broader corporate-secretarial, audit, tax and filing services remain future scope. The audit-exemption link is informational only. Header, sidebar, launcher and current docs identify v1.3.1. See [release note](../RELEASE_NOTES_v1.3.1.md) and [Quick Start](../QUICK_START_v1.3.1.md).

## M0 stabilization evidence — v1.3.1

100 tests passed locally and from a clean temporary installation on macOS 14.6 arm64 / Python 3.9.6 / Streamlit 1.50.0. Fresh launch, offline relaunch without reinstall, exact dependency-pin matching, active-port refusal and legacy workspace/report compatibility passed. Startup now checks before dependency installation, supports an explicit alternate port, and allows immediate restart after connections close. Requirements and constraints are fingerprinted together; deprecated width arguments are removed. CI covers Linux 3.9/3.12 and macOS 3.12. Committed-source releases use a deterministic ZIP builder with per-file SHA-256 manifest and checksum sidecar. See [M0 record](24_M0_STABILIZATION.md) for scope and remaining manual acceptance.

The expanded M0 candidate suite passes 100 tests locally and in all three jobs of [CI run 44752853119](https://github.com/jefftansg/Otto_Engine/actions/runs/44752853119). Current-candidate sample reports were regenerated and technically reviewed; professional approval and manual UAT remain pending. See the M0 record for the rendered-workbook blank-string preview limitation and the independent saved-file check.

## To-be requirements

Release update template: version/date, supported platform, scope and associated requirements, verified user-visible changes, migration/restore implications, exact verification commands/results, known gaps, authority version impacts, archive digest and reviewer approvals.

## Acceptance criteria / verification

Current unittest run recorded 52 passed. Reproduce with the command in the test strategy and verify ZIP integrity and Mac behaviour separately. Attribute historical claims to their notes unless historical artifacts are available.

## Risks, limitations and open questions

Historical test counts and differences cannot be replayed from the supplied ZIP alone. Live Mac render and older ZIP compatibility need dedicated evidence.

## Related documents

- [System Architecture](03_SYSTEM_ARCHITECTURE.md)
- [Test Strategy](18_TEST_STRATEGY.md)
- [Development Roadmap](19_DEVELOPMENT_ROADMAP.md)
- [Decision Log](22_DECISION_LOG.md)

## v1.3.1 follow-up — obsolete document removal (21 November 2026)

Added “Saved statement history” with “Select obsolete statement history to remove” and “Remove selected statement history” in Guided Documents/Bank and Advanced Setup. These summaries can survive a workspace restore even when PDFs are unavailable. Added selected available-upload removal in Advanced intake. Original files and accounting/evidence records are preserved. Removing history requires bank balances to be reverified; save a new ZIP to retain the removal. Existing ZIPs are not modified.

Verification for this follow-up: `python -m unittest discover -s tests -v` — 103 tests passed, no failures or skips, using the local v1.3.1 virtual environment (Python 3.9 / pinned M0 dependencies). Includes Guided/Advanced removal, stale-selection rejection, selective same-name record removal, workspace restore and unchanged accounting totals. AppTest covered UI mechanics; live browser and native Mac removal flows were not manually retested.

## OCBC extraction fix — 21 November 2026

v1.3.1 parser follow-up: recognise OCBC BALANCE B/F, BALANCE C/F and complete date headings beside BUSINESS GROWTH ACCOUNT or on a separate line. No values inferred from filenames or transaction totals. Full unittest suite: 109 passed, no failures or skips, local Python 3.9 / M0 pinned environment. Read-only local validation of 11 user-provided statements passed summary extraction and adjacent balance continuity; client files/data were not added to source or fixtures. November fictional material was excluded from this continuity validation. No live posting or balance approval was performed.
