# Bank postings after a monthly export end

23 November 2026. Candidate **1.4.0-dev.4**. The user explicitly authorised accepting later posting dates because bank transactions may be posted after the monthly export period. This supersedes the monthly end-date restriction described in docs/30 and docs/33 for supported OCBC daily-detail statements. No final release or professional/template approval.

## Changed behaviour

`engine.ocbc_daily.propose_rows` accepts an original posting date after the selected export end. It keeps that posting date unchanged and records the boundary difference in the transaction's source notes. It continues to reject unreadable dates, dates before the export start and dates later than the printed-on date. Full printed debit/credit counts, gross totals, running balances and opening/closing movement must still reconcile uniquely. No value date is substituted and no financial amounts are inferred.

`engine.bank_intake.staged_rows` applies the confirmed financial-year date range to imported postings. A later monthly posting inside that year can proceed to explicit review/import; a posting outside the confirmed year remains a cutoff exception. Non-daily statement layouts retain their existing per-statement date restrictions. Statement coverage remains based on the selected/verified export period and print date; a later posting never extends coverage or clears missing months.

Overlapping posting dates may repeat across exports. Within each account, matching original source reference, posting date and deposit/withdrawal across different source fingerprints raise a possible-repeat exception. Otto does not silently delete or count the transaction twice. Existing exact-file/source-row retry and import-review guards remain. Review is still required before staging and classification; no client data is posted by analysis.

This change concerns source import eligibility. It does not determine accrual recognition dates, change financial-year setup, invent journal adjustments or authorise a final financial statement. Separate framework/owner/template decisions remain open.

## Validation

Five new synthetic tests in `tests/test_late_posting.py` cover a month-boundary posting inside a two-month financial year, unchanged posting dates and source metadata through approval/import/ZIP, duplicate retry prevention, possible repeats across different monthly files with rejection without mutation, unchanged gross/running-balance checks, pre-period/post-print date rejection and explicit-review requirements. Earlier strict monthly-cutoff regressions now assert the user-authorised behaviour while retaining the financial-year cutoff test.

Full local suite: **214 tests passed, no skips**, macOS arm64/Python 3.9.6. Exact-head CI is recorded in the PR. No report renderer/layout, dependency, ledger arithmetic or regulatory determination changes.

Read-only local re-analysis of the three supplied affected statements now extracts their transactions without monthly end-date exceptions, retaining the later original posting dates. No private documents, identifiers, amounts or diagnostic output are committed. This check does not approve their transactions, resolve other missing coverage or alter the user's running workspace.
