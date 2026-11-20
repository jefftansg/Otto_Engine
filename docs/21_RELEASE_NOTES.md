# Release notes

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Verified
- Owner: Engineering
- Related requirements: OTTO-BASE-001, OTTO-QA-001
- Sources/evidence: RELEASE_NOTES_v1.2.4.md, docs/previous_releases/, START_ON_MAC.command, app.py, assets/, tests/

## Purpose and scope

Record what the supplied release verifies and what shipped historical notes report.

## As-is implementation (evidence-backed)

Launcher and current release notes identify v1.2.4. Source confirms Otto page title, PNG branding assets, default Guided path, Otto ZIP download name and branded PDF code. README and [release note](../RELEASE_NOTES_v1.2.4.md) describe the branding release as based on v1.2.3. Independent historical source trees were unavailable, so the stated change history is attributed to the bundled notes.

| Release | Archive record and described focus |
| --- | --- |
| v1.1 | [Release note](previous_releases/RELEASE_NOTES_v1.1.md) for guided intake and multi-format uploads. |
| v1.2 | [Release note](previous_releases/RELEASE_NOTES_v1.2.md) for smart intake. |
| v1.2.1 | [Release note](previous_releases/RELEASE_NOTES_v1.2.1.md) for Guided Mode. |
| v1.2.2 | [Release note](previous_releases/RELEASE_NOTES_v1.2.2.md) for clarification questions. |
| v1.2.3 | [Release note](previous_releases/RELEASE_NOTES_v1.2.3.md) for attention routing and checks. |
| v1.2.4 | [Release note](../RELEASE_NOTES_v1.2.4.md) and current inspected source for branding and local drafts. |

## Unreleased — upload review and deletion (20 November 2026)

User-requested changes on `codex/delete-uploaded-files`, based on commit `838565d`:

- Guided Upload and Bank steps show a flagged-file list and let the user retain or delete selected files. No automatic deletion.
- Exact byte duplicates are flagged, including renamed copies. Retrying the same filename/content is idempotent. Overlapping same-account statement periods are flagged as possible duplicates, not proven duplicates.
- Flag statements wholly or partly outside a confirmed financial year, ACRA profiles with a different UEN, and unreadable/unrecognised documents. Uncertain relevance is explicitly labelled; supporting, opening and comparative evidence may be useful.
- Retaining records the decision for the current reasons in this session. A changed reason requires a fresh decision. Decisions and source files are not included in workspace ZIPs.
- Deletion removes only selected session uploads, resets the uploader to prevent automatic restoration, clears cached inspections, and refreshes proposals. Saved company details, transactions, evidence and historical extraction registers remain. Removing a recognised/registered bank statement revokes balance confirmation. Bank amounts remain available for review.
- Exact duplicate statement content contributes only one set of proposed bank rows. Existing duplicate, cutoff, reconciliation and approval gates still apply.
- No workspace schema migration, accounting policy change, external publishing or deployment. Advanced retains its existing uploader removal controls.

Verification: macOS arm64, Python 3.9.6, Streamlit 1.50.0, isolated temporary virtual environment. `/private/tmp/otto-delete-venv/bin/python -m unittest discover -s tests -v`: **73 passed, 0 failures, 0 errors, 0 skips**. Includes Streamlit AppTest for Guided Upload/Bank deletion, retain-then-delete and Advanced entry. Synthetic fixtures only; no real client uploads inspected. Browser file-picker interactions and older release ZIP archives have not been manually verified. Existing Streamlit width deprecation warnings remain.

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
