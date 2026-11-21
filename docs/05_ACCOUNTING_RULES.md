# Accounting rules

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Needs review
- Owner: Accounting
- Related requirements: OTTO-ACCT-001, OTTO-ACCT-002, OTTO-ACCT-003, OTTO-ACCT-004, OTTO-BANK-002
- Sources/evidence: engine/core.py:20–355, engine/reports.py:194, tests/test_engine.py

## Purpose and scope

Define posting, corrections, cash and period reconciliations for review by Accounting.

## As-is implementation (evidence-backed)

`money` quantises to SGD cents with ROUND_HALF_UP. Bank transactions debit/credit 1000 and mirror the counter-account. Exactly one positive inflow or outflow is required. Suspense 9999 raises an error while preserving draft lines. Claims debit an expense or asset and credit a configured director liability. Invoices compute outstanding and ageing, and tie to 1100. Recognition and settlement use separate entries. Manual journals check debit/credit equality by ID and permit dates before the start, supporting opening balances. Bank and claims require in-period dates. Validation ties journal, net trial balance, position equation, imported movement, opening and closing book cash, cash flow and AR. Missing evidence or confirmations can be warnings. The app applies separate Guided and Advanced draft download gates.

## Upload removal and retained accounting records

Session upload deletion does not remove or reverse approved transactions, journals, company details, evidence or historical statement extraction registers. Removing a recognised or registered bank statement revokes bank balance confirmation and requires review again; stored balance amounts remain. Correct accounting entries through the existing editors. Exact duplicate content is proposed for import once, while retaining both uploaded filenames for user review. No posting, rounding, cutoff or accounting policy changes are introduced.

## Issue tracker and stage indicators

Progress notes and Open/In progress status do not modify or approve accounting entries. Live checks clear issues when their condition is no longer detected; cleared history is retained and recurrence reopens the issue. Answering a clarification closes that question, while any independent ledger validation remains open. Missing bank source files require rechecking rather than silently clearing historical source findings. Green stage labels describe current readiness checks, not professional certification. Existing posting, rounding, reconciliation and report-download rules remain in force.

## v1.3.1 Company-first setup

Moving company/date setup ahead of general document intake changes navigation only. No entry is posted by company setup, ACRA upload or colour status. Name/UEN/date confirmation clears the initial Company stage independently of later document-review questions; report readiness still considers outstanding questions, reconciliation and existing report-download gates. Audit exemption is not inferred from SME size or from choosing UFS preparation.

## M0 stabilization boundary

Startup, dependency pinning, deprecated UI argument replacement and source packaging do not alter posting, rounding or reporting gates. A baseline synthetic workspace is restored with identical generated entries, balances, cash flows, profit and validation errors after tracker initialization and ZIP round-trip. M0 tests retain the existing bank-opening, journal-ID collision and cash/noncash regression checks; partial accounting capabilities in the requirements register remain partial.

## To-be requirements

Fictional SGD posting patterns subject to evidence and policy review:

| Event | Debit | Credit | Evidence/control |
| --- | --- | --- | --- |
| SGD 150 bank service receipt on earned revenue | Cash 150 | Sales 150 | Check prior invoice accrual first. |
| SGD 100 unpaid sale and later settlement | AR 100, then cash 100 | Revenue 100, then AR 100 | Link allocation to invoice. |
| SGD 20 sales credit note | Revenue/returns 20 | AR 20 | Tie to original invoice and revise ageing. |
| SGD 80 director-paid software and reimbursement | Expense 80, then director liability 80 | Director liability 80, then cash 80 | Verify receipt, funding and same claim settlement. |
| SGD 1,000 deposit split by funding evidence | Cash 1,000 | Share capital 300 and director loan 700 | Match subscription and loan evidence. Mixed direct cash classifications require allocation. |
| SGD 120 accrued service | Expense 120 | Accrual or AP 120 | Verify delivery and supplier cut-off. Reverse accrual on supported settlement/recognition. |
| SGD 120 annual prepaid service | Prepayment 120, then expense 10 monthly | Cash 120, then prepayment 10 monthly | Use coverage dates and supported policy. |
| SGD 200 refundable security deposit | Deposit asset 200 | Cash 200 | Review recoverability and current/non-current split. |
| SGD 600 equipment, SGD 10 depreciation | PPE 600, then depreciation 10 | Cash/AP 600, then accumulated depreciation 10 | Approve asset policy, useful life and disposal treatment. |
| SGD 500 loan proceeds | Cash 500 | Borrowings 500 | Separate principal, interest and current maturities. |
| SGD 75 internal transfer | Destination bank 75 | Source bank 75 | Match both statements and exclude consolidated external movement. |
| SGD 40 business credit card charge | Expense/asset 40 | Card payable 40 | Match card settlement to liability, avoiding duplicate expense. |

Only post an opening counterpart backed by prior approved TB, statements or funding evidence. Preserve reversals as linking entries. Separate foreign-currency transaction amount, base currency, rate/date/source, settlement and period-end remeasurement when FX is scoped. Use posted decimals, record rounding differences and set currency-specific precision policy. Derive cash from actual external cash movements, exclude noncash claims and depreciation and disclose material noncash financing/investing activity as applicable. Close only after reviews, then record locks, adjustments and approved reopen. Log stable severity and issue IDs for error, warning and information.

## Acceptance criteria / verification

Reconcile each bank account to statement and ledger by period, each subledger to its control account, prior equity plus reviewed movements to closing equity and opening cash plus flows to closing cash. Test corrections and source collisions, credit notes, split movements and classification compatibility. Snapshot totals must survive workspace restore.

## Risks, limitations and open questions

Single bank and fixed COA limit transfers, FX, accumulated depreciation and liability detail. A category marked Noncash can receive a cash bank posting, while report flow sections omit a Noncash category. Reproduced on the fictional demo by appending a SGD 20 bank withdrawal coded 5700 at period end and changing statement closing from SGD 1,768 to SGD 1,748. Core returned zero errors, Noncash was SGD −20, and visible operating/investing/financing/unallocated flows still totalled SGD 1,768 with zero opening cash. The displayed lines therefore disagree with closing cash. Mixed manual cash journals use a single category or Unallocated. A shared journal ID may merge sources. Missing statement amounts can default to zero in core. Review structural flags and mapping policy before authorisation.

## Related documents

- [Data Model](04_DATA_MODEL.md)
- [Report Specifications](10_REPORT_SPECIFICATIONS.md)
- [Test Strategy](18_TEST_STRATEGY.md)
- [Open Questions](23_OPEN_QUESTIONS.md)

### Obsolete source history removal

Removing an uploaded source or saved statement extraction summary does not reverse or delete recorded transactions or evidence. Saved statement-history removal revokes bank balance confirmation while retaining amounts for review. Corrections to the books still require the existing transaction/correction workflow.

## OCBC extraction fix — 21 November 2026

OCBC abbreviated balance labels are treated as explicit source proposals, subject to the existing ambiguity, account, coverage and continuity checks. Recognition does not approve a balance or post transactions. Accounting recognition and measurement rules are unchanged.

## Otto Auto accounting invariants (planned, 21 November 2026)

AI extraction/classification is advisory only; approved transactions continue through deterministic Decimal double entry, bank reconciliation, period cutoff, reversals and source identity rules. An absent monthly statement, inconsistent opening/closing balances, or a date-altered demo document cannot establish financial completeness. Provisional drafts must be labelled; unresolved material errors prohibit authorised reports. See [Otto Auto specification](25_AI_FIRST_AUTO_EXPERIENCE.md).
