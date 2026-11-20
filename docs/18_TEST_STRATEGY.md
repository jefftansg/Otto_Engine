# Test strategy

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Verified
- Owner: Engineering
- Related requirements: All IDs in the register
- Sources/evidence: tests/, sample_company/, example_imports/, demo_output/

## Purpose and scope

Provide repeatable baseline evidence and the release regression plan.

## As-is implementation (evidence-backed)

Run from the archive root on Linux using `python -m unittest discover -s tests -v`. Result: **52 passed, 0 failed, 0 errors, 0 skipped**. The verified run used Python 3.12.14 on Linux x86-64 with ReportLab 4.4.9, XlsxWriter 3.2.9, openpyxl 3.1.5, xlrd 2.0.1 and pdfplumber 0.11.9. Streamlit was absent from that interpreter. The initial `python -m pytest -q -p no:cacheprovider` could not start because pytest was absent. The unittest run used the available environment and the existing archive suite. Seven modules exercise core, mapped imports, autofill, Guided helper/integration logic, attention, clarification and brand/launcher checks. PDF/XLSX tests check signatures. Tests use bundled demo artifacts or construct fixtures. Brand tests inspect files and source. Mac UI was outside the test run.

## Upload review/deletion verification — 20 November 2026

Command: `/private/tmp/otto-delete-venv/bin/python -m unittest discover -s tests -v` on macOS arm64 / Python 3.9.6 / Streamlit 1.50.0: **73 passed, 0 failures, 0 errors, 0 skips**.

New tests exercise renamed exact duplicates, stable retry identities, overlapping coverage by account, confirmed-year cutoffs, mismatched company UEN, uncertain/unreadable documents, non-mutating suggestions, and exact-copy proposal deduplication. Deletion tests cover same-name distinct-content files, stale/empty selection rejection without mutation, clear-all, legacy hashless extraction registers, unchanged accounting entries/balances/cash flows, and current ZIP restore preserving revoked balance confirmation. AppTest drives Guided Upload and Bank selection/deletion across reruns, retention followed by deletion of only one duplicate, re-adding removed content and Advanced entry rendering.

Scope: synthetic fixtures, Python backend and Streamlit AppTest. Real browser file selection, previous-release ZIP archives and manual launcher/offline checks remain unverified; existing cutoff/reconciliation/report tests passed. Streamlit's existing container-width deprecation warnings are not failures.

## To-be requirements

Use frozen synthetic ledgers, hand-calculated expected SGD results, explicit evidence locations, and permission-reviewed/redacted bank layout samples. Keep hashes and version metadata for golden fixtures. Unit tests cover date, decimals and rules, integration covers staged approvals through export, browser E2E covers state and downloads, and UAT covers Mac and accounting review.

| Scenario | Test ID suffix after TEST-OTTO- | Expected assertion / evidence |
| --- | --- | --- |
| 01 First and second year | COMP-001 | Current-year first-year check and conditional second-year retest. Proposed. |
| 02 Exactly two thresholds | COMP-001 | Inclusive thresholds in both preceding FYs. Proposed. |
| 03 Only one threshold | COMP-001 | Ineligible entrant with fully known data. Proposed. |
| 04 Group fails | COMP-001 | Subsidiary standalone pass does not establish exemption. Proposed. |
| 05 Missing headcount or group figures | COMP-001 | Requires verification when outcome uncertain. Proposed. |
| 06 Loss of status | COMP-001 | One prior failing year retains status; two remove it; private-status loss triggers disqualification. Proposed. |
| 07 Independent framework | COMP-002 | Audit exemption and framework decision differ. Proposed. |
| 08 1 Jan 2027 boundary | COMP-002 | Select by start date and approved transition. Proposed. |
| 09 Monthly continuity | BANK-001 | Exact continuity, gap and mismatch. Existing autofill tests use synthetic periods; add full monthly fixture. |
| 10 Two accounts/transfer | BANK-002 | Per-account coverage and zero external movement for transfer. Existing different-account rejection only. |
| 11 Scan only | DOC-001 | Evidence only, zero invented rows. Existing unlabelled/no-text checks; add image-only PDF fixture. |
| 12 Duplicates | BANK-003 | Same file and overlap idempotency and same-value valid-payment retention. Existing mapping/reimport subset. |
| 13 Director funding | ACCT-002 | Claim, split funding, reimbursement and credit note tie. Existing demo and AR subset. |
| 14 Adjustments | ACCT-002 | Unpaid sale, accrual, prepayment, deposit and depreciation tie with expected noncash treatment. Existing AR control subset. |
| 15 Statement consistency | REP-001 | Position, TB, equity, cash and notes reconcile. Existing demo arithmetic and signature subset. |
| 16 Answer persistence | CLAR-001 | Restore answer, outstanding mandatory block, ledger unchanged. Existing restore/check subset. |
| 17 Mode navigation | UX-001 | Issue editor and back preserve ledger, verified by UI interaction. Existing shared-package and route tests. |
| 18 Evidence and reversals | ACCT-001 | Trace a figure to approved sources and reverse with a reviewer audit trail. Proposed end-to-end. |
| 19 Sole proprietor | UFS-001 | Only adapted management package and no company statement. Verify in UI. |
| 20 Missing disclosures | UFS-001 | Unsupported framework, absent comparatives and omitted required notes block authorisation. Proposed. |
| 21 Recovery and malicious input handling | SEC-001 | Bounded local parse, rejected restore retains original and export safely escapes untrusted text. Proposed. |

## Proposed external-review and audit-handoff tests (not yet executed)

| Test ID | Scenario | Required result |
| --- | --- | --- |
| TEST-OTTO-SVC-001 | Accountant reviews draft, recommends adjustment | Review and qualifications/scope recorded; corrections require explicit authorised journal; no assurance wording |
| TEST-OTTO-SVC-002 | Audit required but auditor registration or appointment missing | Block audited-status claim; request separate audit engagement and registration evidence |
| TEST-OTTO-AUD-001 | Fictional client exports audit-ready package | Frozen consistent ledger/TB/UFS, all relevant schedules, evidence index, manifest hashes and missing-item register |
| TEST-OTTO-AUD-001-NEG | Missing statement month or related-party confirmation | Incomplete status and exception visibility; no assertion of audit readiness |
| TEST-OTTO-AUD-002 | Consent denied/revoked or wrong recipient | No unauthorised export; immutable sharing log; no cross-client access |
| TEST-OTTO-UFS-003 | Draft → accountant-reviewed → director-authorised | Status transitions tied to particular immutable report revisions; no automatic audited promotion |
| TEST-OTTO-UFS-003-NEG | Accountant quality check or SSRS 4410 compilation completed | No audit assurance claim, no Otto-generated auditor's opinion |

These are planned automated/UAT scenarios; do not count as passed baseline tests. Test registration and independence records against legitimate professional evidence, not fabricated fixtures alone.

## Acceptance criteria / verification

Retain exact command, interpreter, dependencies, commit/archive identity and pass/fail/skip per run. Regression gates require arithmetic and release tests green, malformed input and duplicate coverage, layout/visual checks and Accounting/Compliance sign-off for mapped requirements. Balance evidence is independent of production readiness.

## Risks, limitations and open questions

The suite misses large layout variations, groups/regulatory decisions, report-by-report tie-outs, permissions, packaging reproducibility and live macOS. Proposed tests need professional acceptance and synthetic/authorised evidence.

## Related documents

- [Product Requirements Prd](02_PRODUCT_REQUIREMENTS_PRD.md)
- [Development Roadmap](19_DEVELOPMENT_ROADMAP.md)
- [Requirements Traceability](20_REQUIREMENTS_TRACEABILITY.md)
- [Release Notes](21_RELEASE_NOTES.md)
