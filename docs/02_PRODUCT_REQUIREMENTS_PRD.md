# Product requirements

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Draft
- Owner: Product
- Related requirements: All IDs in the register
- Sources/evidence: app.py, guided.py, engine/, tests/

## Purpose and scope

Scope each requirement against v1.2.4. P0 denotes an operating or correctness gate for the relevant milestone. P1 denotes an important dependent deliverable.

## As-is implementation (evidence-backed)

See the matched code and test evidence in the traceability register. Implemented applies to the scoped behaviour, Partial to a working subset, Planned to a proposed capability, Blocked to a missing prerequisite and Unverified to behaviour lacking sufficient validation.

## Current release priority — v1.3.1

The current service scope is bookkeeping and draft UFS preparation for SME clients operated by a small preparer. Company setup comes first, with optional ACRA profile intake or manual details, followed by Documents, Bank, Other records and Reports. Company-stage clearance covers the initial name/UEN/date gate; further UFS particulars remain tracked as questions. Automated audit eligibility (OTTO-COMP-001) and filing handoff (OTTO-COMP-003) are future enhancements, not prerequisites or promised functionality in this release. Existing reconciliation, supporting-record and UFS checks remain. The historical milestone table below is a backlog, not a requirement to build the whole corporate-services suite now.

## To-be requirements

| Requirement | Priority | State | User story | Acceptance check | Test |
| --- | --- | --- | --- | --- | --- |
| OTTO-BASE-001 | P0 | Implemented | As an operator I can identify the release from launcher and application and run backend checks. | App header, sidebar, launcher and current release documentation consistently identify v1.3.1; original branding assets remain present. | TEST-OTTO-BASE-001 |
| OTTO-UX-001 | P0 | Partial | As a preparer I can navigate five stages and relevant Advanced editors in one workspace. | Route from bank, director and journal issues to their editors and back with an identical ledger before edits, including keyboard-only use. | TEST-OTTO-UX-001 |
| OTTO-UX-002 | P0 | Implemented | As a preparer I can save and reopen the active workspace including answers. | Round-trip company and all five tables plus answers through ZIP. | TEST-OTTO-UX-002 |
| OTTO-DOC-001 | P0 | Partial | As a preparer I can inspect PDF, XLSX, XLS and CSV evidence before importing. | Map rows with preview and rejection reasons, and preserve scan-only evidence without creating rows. | TEST-OTTO-DOC-001 |
| OTTO-CO-001 | P0 | Partial | As a preparer I can review proposed company fields and confirm reporting dates. | Record evidence and approval for each field, including directors, and leave FYE unresolved if absent. | TEST-OTTO-CO-001 |
| OTTO-BANK-001 | P0 | Implemented | As a reviewer I can check exact single-account coverage and continuity. | Exact boundaries and contiguous balances pass. Gaps, overlaps, account changes and mismatches fail. | TEST-OTTO-BANK-001 |
| OTTO-BANK-002 | P0 | Planned | As a reviewer I can reconcile independent bank accounts and their transfers. | Two accounts reconcile independently at their respective cutoffs and a transfer posts once with zero consolidated external cash flow. | TEST-OTTO-BANK-002 |
| OTTO-BANK-003 | P0 | Partial | As a preparer I can retry imports without duplicate postings or lost valid rows. | Identical file, overlapping extracts and same-day equal genuine transactions yield one posting per distinct bank record across restore and reordering. | TEST-OTTO-BANK-003 |
| OTTO-ACCT-001 | P0 | Partial | As an accountant I can post balanced, evidence-linked journals and reverse corrections. | Unbalanced and cross-source ID collisions are rejected, reversals retain original IDs and reasoning, and cents reconcile. | TEST-OTTO-ACCT-001 |
| OTTO-ACCT-002 | P0 | Partial | As an accountant I can account for director expenses, receivables and adjustments. | Fictional journal fixture ties claims, invoice recognition and settlement, AP, accruals, deposits, prepayments and depreciation to subledgers and cash flows. | TEST-OTTO-ACCT-002 |
| OTTO-ACCT-003 | P0 | Planned | As a reviewer I can lock and reopen a period while preserving prior issued versions. | Closing freezes input and mapping versions. Authorised reopen records reviewer, reason and new report revision. | TEST-OTTO-ACCT-003 |
| OTTO-ACCT-004 | P0 | Partial | As a reviewer I can verify opening balances and classify cash flows. | Unknown opening counterpart blocks readiness, mixed journals allocate cash appropriately and noncash items never affect cash flow. | TEST-OTTO-ACCT-004 |
| OTTO-CLAR-001 | P0 | Partial | As a preparer I can request, save and review evidence-linked client answers. | Answer persists after restore, leaves entries unchanged, and reviewed resolution records action, reviewer and dates. | TEST-OTTO-CLAR-001 |
| OTTO-COMP-001 | Future | Planned | As a reviewer I can assess audit exemption and retain dated evidence. | First/second-year, historical, continuing and group cases return Eligible, Not eligible or Requires verification with evidence and reviewer. | TEST-OTTO-COMP-001 |
| OTTO-COMP-002 | P0 | Partial | As a reviewer I can choose and substantiate a reporting framework for a dated period. | Validate eligibility independently of audit status and select the edition using period start, transition and approved early application. | TEST-OTTO-COMP-002 |
| OTTO-COMP-003 | Future | Planned | As a reviewer I can document filing obligations for handoff. | Record preparation and filing decisions independently with official version and leave submission with the client or appointed filer. | TEST-OTTO-COMP-003 |
| OTTO-REP-001 | P0 | Partial | As a preparer I can export management accounts and reconcile working papers. | A4 and XLSX tie every total to the same snapshot, including source rows and reconciliations, with exceptions visible. | TEST-OTTO-REP-001 |
| OTTO-UFS-001 | P0 | Partial | As a reviewer I can prepare a complete entity-appropriate draft UFS. | Supported company statements tie to ledger and comparative evidence, blank attestations require review, and sole-proprietor workflow omits company UFS. | TEST-OTTO-UFS-001 |
| OTTO-UFS-002 | P0 | Planned | As a reviewer I can authorise a specific report snapshot after blocking issues are resolved. | Snapshot hash, signer and approval timestamp are persisted. Advanced working drafts visibly retain unresolved findings and cannot be marked authorised. | TEST-OTTO-UFS-002 |
| OTTO-SEC-001 | P0 | Partial | As a client I can keep records private and recover securely. | Verify loopback by default, bounded malformed input, protected backups and deletion, and isolation across client sessions. | TEST-OTTO-SEC-001 |
| OTTO-QA-001 | P0 | Unverified | As a Mac operator I can launch, use and recover the app in a supported browser. | Record fresh and offline relaunch, workspace restore, keyboard navigation and PDF download on supported macOS/browser combinations. | TEST-OTTO-QA-001 |
| OTTO-SEC-002 | P1 | Planned | As a service provider I can serve multiple clients with access controls and audit trails. | Cross-tenant access is denied and logged for users, documents, report downloads and administrator actions. | TEST-OTTO-SEC-002 |
| OTTO-REP-002 | P1 | Blocked | As a product owner I can approve layout against Inner Mirror examples. | Compare against authorised redacted source packages and sign off section, terminology and A4 layout differences. | TEST-OTTO-REP-002 |

## Acceptance criteria / verification

Run the named tests and verify the additional cases in the test strategy before promoting a requirement. Preserve legacy ZIP compatibility and verify duplicate retries, rejected imports, mixed dates, missing evidence, unsupported entity/framework and long-text exports. Measure input resource use at parser limits and record restart/recovery behaviour.

## Risks, limitations and open questions

A passing test for a subset cannot promote a Partial requirement. Thresholds and report semantics require Accounting and Compliance review.

## Related documents

- [User Workflows Ux](08_USER_WORKFLOWS_UX.md)
- [Test Strategy](18_TEST_STRATEGY.md)
- [Requirements Traceability](20_REQUIREMENTS_TRACEABILITY.md)
- [Open Questions](23_OPEN_QUESTIONS.md)
