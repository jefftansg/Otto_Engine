# Report specifications

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Draft
- Owner: Accounting
- Related requirements: OTTO-REP-001, OTTO-REP-002, OTTO-UFS-001, OTTO-UFS-002
- Sources/evidence: engine/reports.py:93–350, demo_output/, guided.py:497–516, app.py:567–582

## Purpose and scope

Specify source fields, totals and evidence for each package. The bundled demo has a 12-page A4 landscape management PDF and a 5-page A4 portrait UFS PDF. The archive contains no identifiable Inner Mirror reference. Use these examples provisionally and verify packaging against authorised reference examples when available.

## As-is implementation (evidence-backed)

| Management component | Fields and mapping | Format and tie |
| --- | --- | --- |
| Cover / overview | Company, UEN, period, SGD, draft state and financial totals | PDF and XLSX overview. Draw totals from one result. |
| Balance Sheet | Account code/name, assets positive debit, liabilities/equity positive credit, prior unclosed profit and current result | PDF/XLSX. Assets equal liabilities plus equity. |
| P&L | Period income credit, expenses debit, result income less expenses | PDF/XLSX. Profit flows to equity. |
| Trial Balance | Account code, debit and credit columns split from signed net balances | PDF/XLSX. Equal net debit/credit totals. |
| General Ledger | Date, journal, account, description, debits/credits, evidence; XLSX includes source type | Tie totals by account and period to both statements. |
| Bank reconciliation | Opening, imported movement, expected and entered closing, ledger close and net difference | PDF/XLSX. Direct equality check, no timing difference register. |
| A/R ageing | Invoice, customer, due date, ageing bucket and amount minus paid | Tie year-end balance to 1100. Buckets current, 1–30, 31–60, 61–90, 91+. |
| Source bank | Date, reference, narrative, deposits, withdrawals, classification and evidence | PDF/XLSX. Compare with statement and ledger bank entries. |
| Director schedule | Date, director, merchant/description, amount, expense code, evidence, nominated liability balance | PDF/XLSX. Tie claims, repayments and balances. |
| Evidence register | Reference, type, filename, review status, remarks | PDF/XLSX. Resolve all material references. |
| Explanatory notes and review | Policy inputs, source limitations and error/warning register | Management PDF notes and XLSX validation. |
| Cash flow and source ledgers | Operating/investing/financing/unallocated, opening and closing cash, journals, invoices and claims | XLSX includes these schedules. A/P ageing is proposed. |

UFS uses a portrait PDF. Position and earnings derive from the same result. Equity and cash flows share a printed section in source. Notes contain ledger amounts plus user-entered text and placeholders. Re-running `python run_demo.py --input sample_company --output <scratch-directory>` produced the same A4 orientations and page counts, with zero blocking errors and five review items. The rebuilt workbook has 16 tabs. It shows assets SGD 1,768, liabilities SGD 650 and equity SGD 1,118, a zero bank variance and closing cash SGD 1,768. The archive demo remains the provisional layout baseline.

## To-be requirements

| UFS component | Field and conditional logic | Trace downstream |
| --- | --- | --- |
| Identification and approval | Entity, UEN, period/as-at date, SGD, framework edition, status, signatory and dates | Reviewed company/period metadata and approval record. |
| Directors' statement | Company-only, applicable statutory content from authorised evidence | Board approval and eligible signatories. |
| Financial position | Current/non-current presentation, current and comparative figures, mapped accounts and note keys | Closing TB and comparative snapshot. |
| Comprehensive income | Revenue, other income, expenses, tax, profit and any applicable OCI | Period ledger and classification policy. |
| Changes in equity | Opening, owner transactions, distributions, adjustments and total comprehensive income by component | Opening support and journals tie to closing position. |
| Cash flows | Opening, external operating/investing/financing flows, FX effect if applicable, ending, material noncash disclosures | Reconcile cash ledger and control accounts. |
| Policies and disclosures | Basis, recognition, estimates, related parties, going concern and other conditional notes | Framework checklist, schedules, signed evidence and note-to-line link. |

PDF layout uses A4, labelled units, repeated table headers, wrapped descriptions, visible draft state, page numbering and enough width for signed cents. Proposed example layout: cover/readiness → primary tables → detailed schedules → review findings. Workbook tabs use typed numeric values, frozen headers and drill-down keys. Preserve a frozen run ID, report-line ID, mapping rule and version, constituent ledger lines, journal IDs and original document locations. Record missing comparative/disclosure values as unresolved and avoid defaulting missing values to zero.

## Proposed audit-ready evidence package (not implemented)

Produce a read-only, versioned and explicitly **client-authorised** ZIP, not an audit report:

| Folder | Required content | Control |
| --- | --- | --- |
| 00_Manifest | Company, FY, framework edition, report revision, export date, file inventory/hash, incomplete-record flags | Verify files and provenance |
| 01_Statements | Draft/authorised UFS plus Management Accounts | Trace figures to frozen TB |
| 02_Books | Trial balance, general ledger, journals and adjustments | Debits/credits and report totals reconcile |
| 03_Bank | Statements for every account, per-account reconciliations and cutoff evidence | Balances and coverage verified |
| 04_Schedules | A/R and A/P, director loans, share capital, fixed assets, accruals, prepayments, contracts and related parties as applicable | Schedules agree with control accounts |
| 05_Evidence | Authorised receipts, invoices, claims, contracts, minutes, confirmations | Evidence IDs link to posting and report lines |
| 06_Review | Clarification questions/answers, accounting review findings, outstanding issues and approvals | Missing evidence explicitly shown |
| 07_Handoff | Client-authorised recipient, sharing record, auditor query log and any external auditor report link | No forged or Otto-issued audit opinion |

Exclude data not authorised for disclosure. Never mark a package complete merely because all files successfully export; unresolved gaps remain visible. External accountant quality checks do not turn the UFS into audited statements.

## Acceptance criteria / verification

Verify no clipped rows with long names and wide figures, all component totals agree with the TB, equity roll-forward and cash reconcile, and each material line traces back to evidence. Advanced working drafts visibly carry errors. Guided checks company/bank/classification/other records, crucial questions and accounting errors before enabling downloads. Require explicit separate approval for any issued report.

## Risks, limitations and open questions

PDF signature tests do not validate field placement. XlsxWriter converts Decimal to numeric spreadsheet values. Review formula ranges on empty workbooks and cash flow table handling for Noncash classifications. Confirm Inner Mirror examples and expected investor/client package content.

## Related documents

- [Accounting Rules](05_ACCOUNTING_RULES.md)
- [Ufs Preparation And Disclosures](11_UFS_PREPARATION_AND_DISCLOSURES.md)
- [Test Strategy](18_TEST_STRATEGY.md)
- [Open Questions](23_OPEN_QUESTIONS.md)

## Proposed Otto Auto output rules (21 November 2026)

Management Accounts, UFS and PDF/XLSX workpapers must derive from one deterministic frozen ledger snapshot and reconcile to the cent. Each report records financial period, source coverage, exceptions, snapshot and draft/provisional status. Missing genuine FY-end evidence blocks final authorisation. Exclude audit/assurance, tax and filing claims. This is planned, not shipped. See [Otto Auto specification](25_AI_FIRST_AUTO_EXPERIENCE.md).

## P0 visual/layout acceptance override (21 November 2026)

**Template fidelity is mandatory, not cosmetic.** Use approved MA/UFS master templates as visual authorities: fonts and point sizes, margins, heading hierarchy, line spacing, table column widths, cell padding, rules, currency/comparative conventions, page breaks, page numbering and section sequence must be fixed per template revision. The frozen ledger remains the numerical authority. Require visual golden-master review plus accounting tie-outs for release. DOCX output is planned and must not be represented as existing v1.3.1 functionality. Exact style values and source references are pending approved historical examples. Full detail: [Report Design System](26_REPORT_DESIGN_SYSTEM_AND_TEMPLATE_FIDELITY.md).
