# Complete financial statements and reporting readiness

- Date: 2026-11-22
- Status: Approved direction by product owner; implementation and verification pending.
- Priority: P0, after preserving M0 stability; reporting-completeness and template-fidelity gates precede Auto UX enhancements.
- Baseline: v1.3.1 (do not increment release version for documentation changes).

## Product and service scope

Lighthouse StudioWorks provides bookkeeping, management accounts and company unaudited financial statement preparation to Singapore small business owners. Otto is Lighthouse's internal reporting tool, not a customer-facing software or licensing offer. Management accounts target P&L, balance sheet, cash flow statement, trial balance, general ledger, bank reconciliation and relevant schedules. For companies, prepare a complete framework-appropriate UFS including position, profit/loss and OCI where applicable, equity movements (or documented permitted alternative), cash flows, notes, Directors' Statement and required comparisons. Sole proprietors receive entity-appropriate reports, not corporate UFS or directors' statements. Corporate tax computation/filing, GST, audit, ACRA/XBRL filing and company-secretarial work remain excluded.

## Baseline gap

The existing engine already calculates cash flows and checks unallocated cash and the bank movement tie-out (engine/core.py); engine/reports.py renders a simplified equity roll-forward and a direct-method cash flow working summary in the UFS, with a cash flows workbook sheet. Do not rebuild or claim these are absent. Existing summary, comparative information, classification, full framework disclosures, presentation and release checks are not yet validated to complete-statement standard. Inspect current source/tests before coding; preserve existing passing behavior.

## Requirements and independently calculated acceptance scenarios

| ID | Implementation target | Acceptance test |
| --- | --- | --- |
| OTTO-FS-001 | Generate cash flow statement from reconciled journal snapshot, direct method initially if permitted; show operating, investing, financing, opening/closing cash and FX effect if applicable; classify gross/net and interest/dividends/tax under chosen framework and policy. Exclude noncash items and internal transfers. | TEST-OTTO-FS-001: opening cash 1,000 + customer receipts 500 - operating payments 200 - equipment purchases 300 + loan proceeds 400 = closing cash 1,400; operating 300, investing -300, financing 400. Separate fixture: unpaid sale, accrual, depreciation and director-funded expense produce no cash movement. Transfer between cash accounts nets zero; unsupported multi-account/FX scenarios explicitly blocked until supported. |
| OTTO-FS-002 | Equity roll-forward by component: supported opening balances, capital issued, distributions, profit/loss, OCI when applicable, policy changes/restatements and other movements; use sign-correct evidence and avoid double-counting unclosed prior profits. Only use combined income/retained earnings presentation where the selected framework permits and reviewer records rationale. | TEST-OTTO-FS-002: opening capital 1,000 and retained earnings 200; issue shares 500; profit 300; dividends 100; closing capital 1,500, retained earnings 400, total equity 1,900. Tie to SOFP; verify director loan not equity, errors and noncash capital movements. |
| OTTO-FS-003 | Store reviewed prior-period values for each required primary statement and note; current/prior labels, reporting periods and consistent mappings. First-year and restatement logic must be explicitly assessed. Unknown is not zero. | TEST-OTTO-FS-003: subsequent-year fixture with approved opening and comparative figures, missing comparative blocks issue, legitimate first-year treatment requires reviewer evidence; restatement reconciles to opening equity. |
| OTTO-FS-004 | Framework/version-specific completeness register with mandatory/conditional sections, note cross-references, directors' particulars and documented relief/alternative checks. No automatic compliance assertion; directors' approval tied to an immutable revision. | TEST-OTTO-FS-004: missing cash flow, equity, required note, comparative or unsupported framework leaves blocking exception; permitted alternative and relief require evidence; sole proprietor never receives corporate form even in CLI/renderer. |
| OTTO-FS-005 | Shared ledger-to-report model for MA/UFS PDF and XLSX, identical values, traceability and template-first styling with approved A4 layout and readable separate sections. Management accounts include cash flow report; preserve existing schedules; no fixed page count that sacrifices completeness. | TEST-OTTO-FS-005: extract rendered values and workbook cells, reconcile to independent ledger expectations and each other; verify labels, no clipping, current/prior columns, stable font and margins, visual golden masters approved by owner. |
| OTTO-FS-006 | Release and approval gates: unresolved material amounts, unallocated classifications, unknown opening balance, missing bank coverage, incomplete statements, unsupported features or disclosures prevent issue/authorisation; working drafts remain available, conspicuously marked and list exceptions. Preserve legacy ZIP support and original inputs. | TEST-OTTO-FS-006: inject each gap and verify export labelled incomplete, no final approval; resolve evidence, rerun, verify immutable snapshot, reviewer and director authorisation; existing regression suite passes. |

## Reconciliation controls

Assets = liabilities + equity. All journal/TB debits and credits balance. Profit and applicable OCI flow into equity. Opening equity + all movements = closing equity by component. Opening cash + external operating/investing/financing net flows + applicable FX effect = closing cash/equivalents; reconcile to SOFP and relevant bank reconciliations, with scope differences disclosed. Cash transfers within cash/equivalents and noncash transactions do not inflate cash flows. No plug or forced balancing entry. Unallocated/missing evidence must be explicit blockers; journal changes require approval. All values derive from one frozen ledger snapshot and mapping version.

## Development order

1. Audit current calculations, sample outputs and existing tests; establish independent golden ledgers and preserve M0.
2. Extend cash-flow classification and presentation; maintain single SGD account baseline and explicitly block unsupported cases.
3. Implement component-level equity roll-forward and comparative data model.
4. Implement framework-specific completeness checks and approval gates; review with a suitably experienced Singapore financial-reporting accountant.
5. Update approved MA/UFS templates, PDF/XLSX, visual tests and shared Guided/Advanced outputs; maintain legacy workspace restore.
6. Execute existing regression suite, new independent cases, Mac/browser UAT, accountant and product-owner acceptance before declaring release ready. Do not claim tests passed before execution.

## Regulatory references

Verify the applicable edition by reporting period and entity eligibility with Accounting. Singapore ASC frameworks: https://www.acra.gov.sg/regulations/accounting-standards-financial-reporting-surveillance/accounting-standards/ . Review applicable FRS 1/7, SFRS(I) 1-1/1-7, or SFRS for Small Entities sections 3, 6, 7, plus relevant disclosures. ACRA preparation guidance: https://www.acra.gov.sg/manage/companies/legal-requirements-common-offences/preparing-financial-statements/ . Relief: https://www.acra.gov.sg/manage/companies/legal-requirements-common-offences/preparing-financial-statements/applying-for-financial-reporting-reliefs/ . Filing/preparation distinction: https://www.acra.gov.sg/manage/companies/legal-requirements-common-offences/filing-financial-statements-in-xbrl-format/requirements-exemptions/ . Audit exemption does not itself exempt preparation; relevant dormant companies or documented relief need separate assessment. No regulatory or professional sign-off is represented by this document.
