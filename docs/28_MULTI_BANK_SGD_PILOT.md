# Multi-bank SGD support — development pilot (22 November 2026)

**Status:** code candidate on development branch, not production-ready. No version increment, no accounting approval, no new test-pass claim. This branch is stacked on PR #20 (financial statement completeness).

## What the pilot implements
- Explicit opt-in on a blank client, or restore of a workspace with a bank registry; the old Guided/Advanced single-account screens are bypassed to prevent data loss.
- One company, multiple SGD bank control accounts using codes 1000–1099 (maximum 100). Private workspace chart of accounts, never global mutation. Account names should be privacy-safe.
- Account-specific reviewed opening/closing statement balances and explicit manual confirmation of period coverage. Bank rows have a mandatory account code and source reference unique within the account. Separate reconciliations detect offsetting variances even when consolidated totals agree.
- Explicit paired internal transfers: two same-date equal/opposite amounts, distinct registered accounts, common reviewer-assigned transfer ID, both counter-accounts TRANSFER, source references and evidence IDs. Post one balanced two-line journal; exclude from external cash flows and P&L. Unmatched, ambiguous, cross-date or fee-netted transfers block reporting. No heuristic auto-posting.
- Consolidated ledger, draft PDF individual bank reconciliation table and XLSX Bank Accounts tab. Source account and transfer IDs survive ZIP round trips. Ordinary legacy workspaces retain their existing CSV format.
- Manual-entry pilot screen; report download is blocked when ledger errors exist. No automated report approval.

## Workspace contract
In company.json, add:
```json
"bank_accounts": [
  {"code":"1000","name":"Bank A","currency":"SGD","opening":"1000","closing":"1200","confirmed":true,"coverage_confirmed":true},
  {"code":"1001","name":"Bank B","currency":"SGD","opening":"500","closing":"600","confirmed":true,"coverage_confirmed":true}
]
```
Only use true following review of the statement evidence. Add bank_account_code and transfer_id to bank.csv. Existing date, reference, deposit, withdrawal, account_code and evidence_ref remain. For opening cash, enter supported opening journals dated before FY start; no invented counterpart or auto-balancing plug. Current-period manual cash postings are blocked in this pilot. Configure directors in the workspace separately if needed; dedicated director setup, bulk CSV editing and richer UI are follow-up work.

## Synthetic acceptance ledger
Bank A opens 1,000, receives customer revenue 500, transfers 300 to Bank B, closes 1,200. Bank B opens 500, receives internal transfer 300, pays operating expense 200, closes 600. Consolidated opening 1,500, operating net cash 300, closing 1,800, profit 300, financing/investing zero. The same bank reference can exist across accounts, not twice in one account. The tests also cover offsetting reconciliation errors, missing/mismatched transfer legs, duplicate references, unsupported currency, manual cash and missing registry, legacy global chart isolation, ZIP round trip and draft report signatures.

## Remaining P0 development
1. Automatically extract bank identity, masked account number, currency, periods and source locations from supported DBS/OCBC/UOB statement formats. Confirm identity and grouping per account; don't guess.
2. Validate exact statement coverage, date continuity, opening/closing arithmetic, duplicate imports and bank-specific transaction identity automatically per account. Manual confirmation in pilot is NOT equivalent.
3. Propose potential transfer candidates with explicit reviewer approval, not automatic posting. Support cross-date cash in transit, separate bank charges, one-to-many settlement and reversals only after accounting policy review. Handle cross-year cutoffs.
4. Support existing client conversion with backup, opening evidence, duplicate/idempotency controls and legacy restoration. Integrate into Guided and Auto (shared ledger; no loss of evidence).
5. Complete per-account evidence and review trails, cash/equivalent and bank-overdraft presentation, MA cash flow statement, equity, comparatives and framework checks per OTTO-FS-001–006. Foreign currency/FX is later scope.
6. Execute entire regression suite and new tests, inspect every rendered output against independent numerical and visual fixtures, verify Mac/browser pilot and obtain accounting/product-owner acceptance. Do not treat signature checks as layout approval.

## Traceability
OTTO-BANK-002 and OTTO-FS-001: partial candidate. TEST-OTTO-BANK-002: pilot synthetic tests in tests/test_multi_bank.py; full multi-account intake/coverage and cutoff acceptance remain open. Existing M0 acceptance remains a dependency. 
