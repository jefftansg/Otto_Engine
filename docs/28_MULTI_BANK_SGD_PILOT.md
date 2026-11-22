# Multi-bank SGD support — development pilot (22 November 2026)

**Status:** reviewed engineering candidate for PR #21, stacked on PR #20. Not production-approved. Release version stays **1.3.1**; do not merge or release until remaining acceptance gates below are satisfied. Otto remains Lighthouse StudioWorks' internal bookkeeping, management-accounts and draft-UFS engine.

## Implemented workflow

1. Start a blank client and expand **Experimental: multiple SGD bank accounts → Enable multi-bank pilot**, or restore a pilot workspace ZIP. Existing single-account workspaces are not silently migrated. Company identity and reporting dates come first.
2. Add originals at **Identify and group bank statements → Bank statements — PDF, CSV or Excel**. Processing is local. Limit: 25 MB/file, 50 files/100 MB per batch. Keep originals separately; ZIPs save accounting data, source fingerprints, extracted summaries and review history, not original PDFs.
3. Review the inventory and source fields. Conservative DBS/OCBC/UOB header recognition identifies institution, full-number-derived account identity, masked account, explicit currency, account holder, labelled balances and exact statement periods. Supported structured CSV/Excel exports and readable PDF text are candidates; bank name alone does not guarantee layout support. PDF provenance includes page and excerpt when the field is located. Unknown currency or owner requires original-source confirmation; conflicting identities/company/currencies, unsupported currency, masked-only account numbers and ambiguous balances cannot be approved.
4. Groups use institution plus a hash of the normalised full account number. Matching last-four digits never merge distinct accounts. Exact file copies are excluded by content hash. Each account gets its own reporting-month map, exact date boundaries, gap/overlap and balance-continuity checks. Previous-period evidence may corroborate opening balances but never supplies current-year coverage. Fictional/demo documents never establish actual coverage.
5. **Approve account identity and coverage** requires a reviewer name, evidence location, confirmed company/reporting dates and explicit original-source confirmation of account/company/SGD currency/coverage/balances. Map each group to a unique control code 1000–1099. Linking an existing manual account with recorded rows requires a separate check. Approval creates metadata only: supported opening journals remain required, with no invented counterpart or balancing plug.
6. Inspect proposed transaction rows, source references and totals. **Approve and stage proposed transactions** needs a separate explicit original-source transaction review. Reliable mapped rows retain file hash, row ordinal and original bank reference, receive stable source IDs and remain unclassified (9999). Mismatched totals, unsupported extraction, warnings and manual-row overlap block batch import. For unsupported layouts or already-recorded rows, manually verify every row against originals and use **Approve existing rows after manual source review**. Net movement agreement alone does not establish gross transaction completeness. Reimporting approved sources does not append duplicates.
7. Review **Bank transactions**, supported opening/adjusting journals, claims, receivables and evidence. Categories require review. Registry edits preserve hidden provenance; used accounts cannot be removed/renumbered. Source-approved balances require re-analysis rather than a manual override. Company/date or source-row changes invalidate the relevant approvals. Prior replaced review records remain in workspace history.
8. **Review suggested internal transfers** proposes same-date, equal opposite SGD movements between distinct accounts, with references and evidence. Analysis never changes books. Multiple possible partners are labelled ambiguous and cannot be approved. **Approve this transfer pair** requires reviewer/evidence and confirmation of both originals. Approval links the two original rows without changing dates or amounts, posts one balanced two-line bank journal, and excludes the movement from external cash flows and profit. Editing source facts makes that approval stale. Cross-date/cross-year transfers, fee-netted transfers, one-to-many settlements, FX and overdrafts remain unsupported; record bank charges separately.
9. Inspect independent bank reconciliations and blocking errors. Accounts cannot offset each other's differences. Download draft MA PDF, company UFS PDF and Excel only after engineering validation passes. Arithmetic success is not accounting or director approval. Sole proprietors receive MA/workpapers, not corporate UFS.
10. **Save pilot workspace ZIP** retains all accounts, source row identities, transfer links, approval metadata and prior-review history. Re-upload originals when re-analysis is necessary. Returning to the legacy screen is not a migration procedure.

## Accounting and export contract

`company.json` retains the explicit registry:

```json
"bank_accounts": [
  {"code":"1000","name":"Bank A","currency":"SGD","opening":"1000","closing":"1200","confirmed":true,"coverage_confirmed":true},
  {"code":"1001","name":"Bank B","currency":"SGD","opening":"500","closing":"600","confirmed":true,"coverage_confirmed":true}
]
```

The above manual flags require actual source review; they are not automated source-coverage certification. Newly source-reviewed accounts additionally store `managed_intake`, `account_key`, `bank`, `masked_account`, `statements`, `coverage_review` and `transactions_review`. Review records bind account, current company/reporting context, source summaries and row facts. `bank_source_imports`, `bank_import_reviews`, `transfer_reviews` and `bank_review_history` preserve import/review state. Do not manually manufacture approval records.

Multi-bank `bank.csv` adds `bank_account_code`, `transfer_id`, `source_sha256`, `source_row`, `source_reference`; ordinary legacy CSVs retain their eight original columns. Reference uniqueness is per account. Transfer IDs and bank source references produce stable journal identities across row reorder and ZIP restore. Global chart dictionaries are deeply isolated per generated result. Current-period manual cash journals remain blocking errors in the pilot.

MA adds individual account reconciliation and consolidated cash-flow schedules. PDF source/journal IDs wrap within existing table geometry. Excel adds Bank Accounts, Statement Sources and Internal Transfers workpapers with source/reviewer links. Single-account sample PDF text/font/position and Excel sheet/cell/formula equality against the original PR head were checked; this is regression evidence, not owner approval of historical master-template fidelity.

## Acceptance evidence and remaining gates

The untouched PR head `19f167f` passed **116 tests**. The revised candidate's full existing/new suite, environment, numerical fixtures, PDF rendering and UI scope are recorded in [multi-bank verification](milestones/MULTI_BANK_SGD_REVIEW_2026-11-22.md). Synthetic evidence never establishes a real client's completeness.

| Gate | Candidate result / remaining work |
| --- | --- |
| Per-bank reconciliations and consolidation | Verified synthetic: A opens 1,000, receives 500, transfers 300, closes 1,200; B opens 500, receives 300, pays 200, closes 600. Consolidated opening 1,500, operating flow/profit 300, closing 1,800; investing/financing zero. Offsetting errors remain blocking. |
| Identification / grouping / coverage | Conservative supported-format tests and read-only OCBC check executed. Wider DBS/UOB production-layout evidence and owner UAT remain required. No scan/OCR support. |
| Transfer suggestions | Review-only, ambiguity, stale approval, amount/date mismatch, duplicate rejection and restore cases verified. Timing differences and complex settlements remain blocked/unsupported. |
| Restore / legacy | Source metadata/reviews persist; duplicate retry is idempotent; single-account regressions pass. Automated conversion of historical clients is not implemented. |
| Report accuracy / presentation | Numeric PDF/XLSX assertions, all-page PDF geometry/render inspection and legacy sample equality executed. Native Excel print inspection and approved-master/owner fidelity sign-off remain outstanding. |
| Product / accounting acceptance | Not granted by tests. Framework eligibility, full disclosures, comparatives, equity and authorisation requirements in OTTO-FS-001–006 remain separate dependencies. No compliance or final-report claim. |
| Deployment / release | PR remains draft/unmerged, engine label stays 1.3.1. CI must pass on the revised PR; no release increment or production rollout. |

## Follow-up scope

Existing-client conversion needs backup, mapping and opening-evidence acceptance before activation. The pilot bypasses single-account editors to prevent data loss; full Guided/Auto integration is still pending. Dedicated director setup and richer editing, cross-date/cutoff policies, bank overdrafts, FX, complex transfers and complete financial-statement/template acceptance remain open. No external SaaS/licensing or audit/filing workflow is introduced.
