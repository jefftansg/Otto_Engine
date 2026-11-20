# Requirements traceability

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Verified
- Owner: Engineering
- Related requirements: All IDs in the register
- Sources/evidence: requirements derived from requested scope; code and tests below

## Purpose and scope

Track implementation and evidence for the v1.2.4 baseline and milestones. Test identifiers are stable requirement-level coverage groups.

## As-is implementation (evidence-backed)

3 Implemented, 12 Partial, 6 Planned, 1 Unverified, 1 Blocked. Code evidence records where the behaviour exists or where a gap appears. Named existing tests ran in the 52-test baseline and may cover only a subset of the associated acceptance criteria.

| Requirement | Evidence | Acceptance | Test ID | Existing verification | State | Milestone |
| --- | --- | --- | --- | --- | --- | --- |
| OTTO-BASE-001 | START_ON_MAC.command; app.py; tests/test_branding.py | Current app header, sidebar, launcher and Quick Start identify v1.3.0; historical v1.2.4 evidence remains unchanged. | TEST-OTTO-BASE-001 | test_branding (86-test v1.3.0 run; 52-test baseline retained) | Implemented | M0 |
| OTTO-UX-001 | guided.py:21,87,220; app.py:31,165 | Route from bank, director and journal issues to their editors and back with an identical ledger before edits, including keyboard-only use. | TEST-OTTO-UX-001 | test_attention; test_guided (52-test run) | Partial | M1 |
| OTTO-UX-002 | app.py:67–85; engine/core.py:87–125 | Round-trip company and all five tables plus answers through ZIP. | TEST-OTTO-UX-002 | test_engine.test_package_roundtrip; test_clarifications.test_status_answers_survive_workspace_zip (52-test run) | Implemented | M1 |
| OTTO-UX-003 | engine/issue_tracker.py; engine/stages.py; guided._attention_panel; native tabs | List all issues, retain progress until checks clear, preserve/reopen history through ZIP, show tab status colours with text, and reserve toolbar clearance. | TEST-OTTO-UX-003 | test_issue_tracker; test_stages (86 tests passed; local browser tab/action/header check) | Implemented; keyboard/mobile verification pending | M1 |
| OTTO-DOC-001 | engine/importers.py:64,125,195 | Map rows with preview and rejection reasons, and preserve scan-only evidence without creating rows. | TEST-OTTO-DOC-001 | test_importers; test_autofill.test_scan_or_unlabelled_balance_never_invented (52-test run) | Partial | M2 |
| OTTO-DOC-002 | engine/intake_review.py; guided._delete_uploads; guided._upload_deletion_controls | List duplicate/uncertain-relevance flags; retain or delete by file identity; preserve saved accounting/evidence; recheck bank balances; retries do not restore deleted uploads. | TEST-OTTO-DOC-002 | test_intake_review; test_upload_deletion (73 tests passed including AppTest; manual file picker pending) | Implemented; manual browser verification pending | M2 |
| OTTO-CO-001 | engine/autofill.py:44,173; guided.py:280–345 | Record evidence and approval for each field, including directors, and leave FYE unresolved if absent. | TEST-OTTO-CO-001 | test_autofill.test_acra_missing_fye_is_not_invented; test_guided.test_demo_ACRA_profile_detected (52-test run) | Partial | M1 |
| OTTO-BANK-001 | engine/autofill.py:186; guided.py:50 | Exact boundaries and contiguous balances pass. Gaps, overlaps, account changes and mismatches fail. | TEST-OTTO-BANK-001 | test_autofill; test_clarifications.test_gap_and_mismatch_generate_questions (52-test run) | Implemented | M2 |
| OTTO-BANK-002 | engine/core.py:20,132; single 1000 control | Two accounts reconcile independently at their respective cutoffs and a transfer posts once with zero consolidated external cash flow. | TEST-OTTO-BANK-002 | None | Planned | M2 |
| OTTO-BANK-003 | engine/importers.py:262; guided.py:50,249,394; engine/core.py:132 | Identical file, overlapping extracts and same-day equal genuine transactions yield one posting per distinct bank record across restore and reordering. | TEST-OTTO-BANK-003 | test_importers.test_duplicate_import; test_attention.test_bank_rows_already_imported_not_suggested_again (52-test run) | Partial | M2 |
| OTTO-ACCT-001 | engine/core.py:48,127,132 | Unbalanced and cross-source ID collisions are rejected, reversals retain original IDs and reasoning, and cents reconcile. | TEST-OTTO-ACCT-001 | test_engine.test_unbalanced_journal_blocks; test_engine.test_demo_balances (52-test run) | Partial | M3 |
| OTTO-ACCT-002 | engine/core.py:132; app.py | Fictional journal fixture ties claims, invoice recognition and settlement, AP, accruals, deposits, prepayments and depreciation to subledgers and cash flows. | TEST-OTTO-ACCT-002 | test_engine.test_receivables_control; test_engine.test_demo_balances (52-test run) | Partial | M3 |
| OTTO-ACCT-003 | engine/core.py:87,132; one period configuration | Closing freezes input and mapping versions. Authorised reopen records reviewer, reason and new report revision. | TEST-OTTO-ACCT-003 | None | Planned | M3 |
| OTTO-ACCT-004 | engine/core.py:132; guided.py:340–428 | Unknown opening counterpart blocks readiness, mixed journals allocate cash appropriately and noncash items never affect cash flow. | TEST-OTTO-ACCT-004 | test_engine.test_bank_reconciliation_blocks; test_engine.test_demo_balances (52-test run) | Partial | M3 |
| OTTO-CLAR-001 | engine/clarifications.py:26,40,185; guided.py:137 | Answer persists after restore, leaves entries unchanged, and reviewed resolution records action, reviewer and dates. | TEST-OTTO-CLAR-001 | test_clarifications.test_status_answers_survive_workspace_zip; test_attention.test_saved_answers_do_not_erase_real_ledger_errors (52-test run) | Partial | M4 |
| OTTO-COMP-001 | engine/reports.py:194; narrative placeholders only | First/second-year, historical, continuing and group cases return Eligible, Not eligible or Requires verification with evidence and reviewer. | TEST-OTTO-COMP-001 | None | Planned | M5 |
| OTTO-COMP-002 | engine/core.py:132; app.py | Validate eligibility independently of audit status and select the edition using period start, transition and approved early application. | TEST-OTTO-COMP-002 | None | Partial | M5 |
| OTTO-COMP-003 | engine/reports.py:194; draft notes only | Record preparation and filing decisions independently with official version and leave submission with the client or appointed filer. | TEST-OTTO-COMP-003 | None | Planned | M5 |
| OTTO-REP-001 | engine/reports.py:93,278 | A4 and XLSX tie every total to the same snapshot, including source rows and reconciliations, with exceptions visible. | TEST-OTTO-REP-001 | test_engine.test_pdf_excel_signatures; test_guided.test_demonstration_reports_balance_after_review (52-test run) | Partial | M6 |
| OTTO-UFS-001 | engine/reports.py:194; guided.py:515; app.py:579 | Supported company statements tie to ledger and comparative evidence, blank attestations require review, and sole-proprietor workflow omits company UFS. | TEST-OTTO-UFS-001 | test_engine.test_pdf_excel_signatures (52-test run) | Partial | M6 |
| OTTO-UFS-002 | guided.py:510; app.py:578–580; draft exports only | Snapshot hash, signer and approval timestamp are persisted. Advanced working drafts visibly retain unresolved findings and cannot be marked authorised. | TEST-OTTO-UFS-002 | None | Planned | M6 |
| OTTO-SEC-001 | START_ON_MAC.command; engine/core.py:100; app.py:125 | Verify loopback by default, bounded malformed input, protected backups and deletion, and isolation across client sessions. | TEST-OTTO-SEC-001 | test_engine.test_package_roundtrip (52-test run) | Partial | M7 |
| OTTO-QA-001 | START_ON_MAC.command; tests/test_branding.py | Record fresh and offline relaunch, workspace restore, keyboard navigation and PDF download on supported macOS/browser combinations. | TEST-OTTO-QA-001 | test_branding.test_mac_launcher_is_executable; no live Mac run | Unverified | M7 |
| OTTO-SEC-002 | app.py:31; no tenant store | Cross-tenant access is denied and logged for users, documents, report downloads and administrator actions. | TEST-OTTO-SEC-002 | None | Planned | M8 |
| OTTO-REP-002 | demo_output/; no matching example supplied | Compare against authorised redacted source packages and sign off section, terminology and A4 layout differences. | TEST-OTTO-REP-002 | None | Blocked | M6 |

## To-be requirements

Update this register and the PRD with each approved change. Link independently defined acceptance evidence and retain historical release decisions. Keep proposed test cases listed in the test strategy until run.

## Acceptance criteria / verification

Each row has one unique requirement ID, a named acceptance check, test ID, state and milestone. v1.2.4 is the evidence baseline for every row. Future milestone assignment does not imply implementation.

## Risks, limitations and open questions

Missing test evidence denotes an unexecuted case, not a pass. Partial rows require the stated acceptance checks and status re-evaluation.

## Related documents

- [Product Requirements Prd](02_PRODUCT_REQUIREMENTS_PRD.md)
- [Test Strategy](18_TEST_STRATEGY.md)
- [Development Roadmap](19_DEVELOPMENT_ROADMAP.md)
- [Release Notes](21_RELEASE_NOTES.md)
