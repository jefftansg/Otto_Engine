# PR #21 engineering verification — 22 November 2026

Candidate scope: branch `development/multi-bank-sgd`, original head `19f167f17b5428c2d59501d645a5ffa119a08675`, stacked on `development/ufs-report-completeness`. Isolated review checkout `Otto_Engine_multi_bank_pilot`, working branch `codex/multi-bank-sgd-review`. No merge or release-version increment authorised by this record.

## Defects found and corrected

- Registry copied the chart shallowly: modifying a result's nested account metadata could mutate the global chart. Deep isolation is now tested.
- Transfer journal IDs depended on source row order. Multi-bank bank/transfer journal IDs now bind stable source/pair identity, leaving legacy IDs unchanged.
- Registry/table editors discarded hidden intake provenance. Registry merge and read-only source columns preserve evidence, while used-account removal/renumbering and source-approved balance overrides are rejected without mutation.
- Non-finite Decimal inputs and extreme-date overlapping statements could raise uncontrolled errors. They now fail validation.
- Long multi-bank reference/journal IDs could run into adjacent PDF cells. They wrap; short balance-sheet check tables stay together in multi-bank output. Legacy single-account geometry is unchanged.
- Corporate UFS rendering could be invoked for a sole proprietor. Direct renderer now rejects it; MA/workpapers remain available and the CLI retains a prior entity PDF separately.
- CI only selected PRs targeting main, excluding this stacked pilot. PR validation now also targets development branches.

## Reproduction and results

Environment: local macOS arm64, Python 3.9.6, existing pinned M0 virtual environment, Streamlit 1.50.0; no dependency changes. Run from repository root:

```bash
python -m pip check
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

- Original unmodified pilot: **116 tests passed**, no skips.
- Revised candidate: **140 tests passed**, no skips (full existing suite plus 24 new regression/acceptance cases). Test output retained locally; final CI status is separate evidence.
- `pip check`: no broken requirements. `git diff --check`: clean.
- New suites: `test_multi_bank_review.py`, `test_bank_intake.py`, `test_multi_bank_exports.py`; original `test_multi_bank.py` runs unchanged.
- Synthetic transfer fixture independently asserts consolidated opening 1,500, closing 1,800, operating cash/profit 300, investing/financing zero, each bank closing 1,200/600, both reconciliation differences zero and exactly one balanced two-line transfer. Mismatches, incomplete pairs, duplicate references and offsetting variances remain blocking.
- Identification tests cover DBS/OCBC/UOB normalised identity, matching masked suffix collisions, institution separation, content duplicates, coverage gaps/overlaps/continuity, prior-period corroboration, boundary overrun, wrong company/currency, missing masked-only identity, malformed PDF, PDF source page and extreme dates. Source approval/import retry, rejection without mutation, stale reviews, previous review history and ZIP restoration are exercised.
- Suggestions remain proposals until explicit approval; ambiguous, cross-date and fee-netted candidates do not post. Original source facts remain unchanged by approval; later edits invalidate it. Classification stays 9999 after transaction staging.
- PDF tests extract figures and each bank's reconciliation row, require A4 geometry and every character within page bounds. Excel tests inspect actual numeric values, formulas and cached results, source hashes/row IDs, paired source rows and reviewer evidence; no Excel error cells. Legacy ZIP bank CSV header remains exactly the original eight columns.
- Streamlit AppTest exercises blank opt-in, restored reconciled pilot, blocked exports, company-change invalidation, rejected unchecked transfer approval, source inventory/identity review, staged import and source-preserving transaction editor. Existing Guided/Advanced/legacy UI regressions run in the full suite. Framework warnings from bare AppTest contexts are expected, not skipped checks.

## Render and browser inspection

Synthetic two-bank MA and UFS PDFs were rendered page by page using PDFium and inspected as an all-page contact sheet plus full-size reconciliation/source pages. Long privacy-safe bank names and reviewed transfer IDs were included. A short balance-sheet check table is now kept together rather than orphaning its final line. MA remains A4 landscape and UFS A4 portrait; baseline Helvetica sizes, colours, margins and table styles are retained. PDF page count can vary with data length.

Legacy sample outputs were compared against `engine/reports.py` from original head `19f167f`: all PDF character text, font, size and coordinates match; all Excel sheet names, cell values and formulas match. This is baseline regression evidence, not approval against the separate Lighthouse/Inner Mirror master examples. Native Excel printing and owner/accountant acceptance remain pending.

A separate local server on port 8505 was inspected in the in-app browser: blank Guided screen, explicit pilot opt-in, company controls, bank-original uploader, registry, source transaction editor, transfer inbox and blocked incomplete-report state. No real-company attestation, financial approval, deployment or production-session restart was performed. Source-review actions were exercised with synthetic AppTest fixtures.

Read-only inspection of the previously supplied OCBC originals identified one account and 11 covered reporting months for 1 December 2025–30 November 2026. November remains missing; the fictional November file was excluded from authentic coverage. No private statement, value, account number or client artifact is added to the repository. This is limited format evidence, not authenticity or client-accounting approval.

## Acceptance remains open

Wider real DBS/UOB layouts, complex transfer/cutoff policies, existing-client migration, full Guided/Auto integration, complete UFS framework/comparative/equity/disclosure/authorisation gates, approved master-template fidelity, native Excel print review, product-owner UAT and professional accounting acceptance remain outstanding. Keep PR #21 draft/unmerged and engine version **1.3.1**. Otto remains Lighthouse StudioWorks' internal service engine; no SaaS, external sharing, audit, tax or filing service is introduced.
