# Otto Auto — AI-first document-first experience (proposed)

- Date: 21 November 2026
- State: Approved product direction; NOT implemented in v1.3.1
- Owner: Product
- Scope: Bookkeeping, Management Accounts and draft UFS for Singapore SMEs; excludes tax, GST, statutory filing, XBRL, audit and assurance.

## Product promise

**Upload your documents. Otto does the bookkeeping and prepares your financial reports. You review and approve.**

The default planned workflow is: **Upload → Auto-analyse → Review exceptions → Generate and download**. This replaces repetitive intake forms with document-first extraction and contextual questions. Existing v1.3.1 Company → Documents → Bank → Other records → Reports remains the implemented baseline. Advanced access remains available to editors and accountants sharing the exact same ledger.

## Core requirements

| ID | Status | Feature | Acceptance |
| --- | --- | --- | --- |
| OTTO-AUTO-001 | Planned | One drop zone | Accept PDF bank statements, CSV/XLS/XLSX, bookkeeping records, prior-year financial statements and MA/UFS templates as one batch without required pre-upload forms |
| OTTO-AUTO-002 | Planned | Evidence-based auto setup | Infer company/UEN/FY only when supported by actual evidence; show editable proposal, dated provenance and explicit confirmation for material uncertainty |
| OTTO-AUTO-003 | Planned | Coverage and balances | Group by company/account/period; detect missing months, duplicates, overlaps, opening B/F, closing C/F, and inconsistent continuity; out-of-year sources may support opening but do not count as current-year coverage |
| OTTO-AUTO-004 | Planned | AI classification proposals | AI suggests categories and questions with source links and confidence; never silently posts, changes dates, or invents amounts; reviewer approval is explicit |
| OTTO-AUTO-005 | Planned | Exceptions inbox | Surface consolidated missing documents, uncleared balances, transactions, claims, disclosures and material assumptions with next action and persistent review history |
| OTTO-AUTO-006 | Planned | Draft reports | Produce Management Accounts, UFS and workpapers from a single verified Decimal/double-entry ledger snapshot; label provisional/incomplete results; block final/authorised output until requirements met |
| OTTO-AUTO-007 | Planned | Advanced continuity | Preserve editor access, one ledger, reversible changes, source traceability and legacy workspace ZIP compatibility |
| OTTO-AUTO-008 | Planned | Ease-of-use evaluation | Benchmark clicks, manual fields, intake-to-draft time and exception count against current Guided release |

## User-facing states

1. Drop files: drag and drop; identify supported vs unreadable; never discard originals silently.
2. Analyse: show recognised company, proposed financial year, bank accounts, monthly evidence inventory, source-backed opening and latest closing balances.
3. Review: ask only questions that materially affect report completion; group repetitive questions; show direct link to supporting source, uncertainty and effect on report readiness.
4. Generate: preview draft MA and UFS, reconciliation schedules, source list and exception register; offer downloadable PDF/XLSX only with truthful readiness labels.
5. Advanced: optional journals, allocations, claims, ledgers, evidence, adjustments and controls.

Example: For FYE 30 Nov 2026, Dec 2025 to Oct 2026 covers 11 of 12 months. November 2025 is outside the period but may establish the 1 Dec 2025 opening bank balance. November 2026 is missing until an authentic statement or supported transaction evidence is obtained. A watermark-marked or month-edited demonstration statement must NOT count as authentic evidence. A provisional through-October report may be permitted if explicitly labelled and cutoff assumptions recorded; it cannot be approved as a complete FY report.

## Architecture and controls

Source files → parse/OCR if supported → stable hashes, account IDs and field-level provenance → optional AI proposal layer → evidence and exception review → explicit posting approval → deterministic Decimal journal and double-entry engine → reconciliations/cutoff → frozen report snapshot → draft PDF/XLSX. AI output is untrusted suggested input; the deterministic layer owns accounting arithmetic and validation. Retain distinct raw, staged, approved, corrected and report versions. Reject duplicate posting, cross-company mixing, false cutoff and unsupported opening counterparts. Preserve client privacy, consent controls, safe retention and restore.

## Test criteria (planned; NOT executed)

- TEST-OTTO-AUTO-001: unordered uploads lead to document inventory with no mandatory setup form.
- TEST-OTTO-AUTO-002: inferred FY and opening balance have exact source provenance; absent fields remain unknown.
- TEST-OTTO-AUTO-003: 11/12 months flags November gap; duplicates/overlaps ignored; previous-year month excluded.
- TEST-OTTO-AUTO-004: AI classification cannot post before approval or override double-entry validation.
- TEST-OTTO-AUTO-005: exceptions persist after ZIP round-trip and re-open when evidence is withdrawn.
- TEST-OTTO-AUTO-006: PDF/XLSX totals tie to same ledger revision; incomplete FY cannot be labelled final.
- TEST-OTTO-AUTO-007: Auto and Advanced share books; restore prior workspaces without loss.
- TEST-OTTO-AUTO-008: usability benchmark beats or matches prior conversational workflow.
- TEST-OTTO-AUTO-009: modified/demo bank statement cannot satisfy official bank evidence.

## Delivery sequence

After outstanding M0 acceptance: (1) upload-first UX prototype; (2) source inventory, coverage and deduplication; (3) optional AI interpretation with human approval; (4) consolidated issue resolution and deterministic reporting; (5) synthetic test automation, Mac/browser pilot and accountant sign-off. No claim that these features ship in current v1.3.1.

## Open design questions

Decide AI provider/on-device processing and consent; OCR scope; exact reporting materiality/authorization gates; user template mapping; maximum batch sizes; measurable UX acceptance targets. Preserve existing regulatory and professional-review boundaries.
