# Otto Report Design System and Template Fidelity

- Date: 21 November 2026
- Priority: P0 — before broad Otto Auto UX rollout
- Status: Approved product requirement, implementation and visual acceptance PENDING
- Applies to: Management Accounts (MA), Unaudited Financial Statements (UFS), schedules and user-selected exports
- Product: Otto Financial Report Engine

## Problem

Reports previously assembled with ChatGPT from bookkeeping and UFS templates had a desirable, coherent professional layout. Otto's existing PDF generator is based on generic PDF tables and style choices and must not be treated as a replacement for an approved professional reference template. Correct totals and successful PDF generation alone do not demonstrate acceptable visual quality.

## Non-negotiable product principle

**Template-first, data-driven, deterministic reporting.** The user selects an approved Master MA Template and Master UFS Template (either supplied documents or approved built-in masters); Otto extracts accounting data and populates named fields/table regions while retaining approved typography, page geometry, heading hierarchy, table design, whitespace and pagination. The template is the visual source of truth; the ledger is the numeric source of truth. Neither an LLM nor a general PDF layout algorithm may improvise the visual design for each client.

Until the existing historical reference files are obtained and approved, the exact font family, point sizes, margins, page count and graphic treatments are **TBD**. Do not assert visual equivalence with historical reports. The baseline is the actual user-approved original report, not Otto's current demo output.

## Requirements

| ID | Priority | State | Testable criterion |
| --- | --- | --- | --- |
| OTTO-DES-001 | P0 | Planned / reference blocked | Import or designate the approved MA/UFS master layouts and immutable template revisions. Explicit template IDs and version metadata are recorded on each report. |
| OTTO-DES-002 | P0 | Planned | Define typography tokens: approved font family and embedded/substitute font rules, heading/subheading/body/table/footer sizes, weights, line height, indentation, paragraph spacing and colours. No per-run random variation. |
| OTTO-DES-003 | P0 | Planned | Specify A4 page orientation and margins for each document, header/footer positions, page numbering, section start positions, whitespace and page breaks; support distinct MA/UFS designs. |
| OTTO-DES-004 | P0 | Planned | Consistent financial tables: column widths, numeric decimal/right alignment, dates, SGD and comparative years, negative values, zeros/dashes, subtotal/total rules, row padding and repeated headers. Avoid clipped/overlapping text and orphan headings. |
| OTTO-DES-005 | P0 | Planned | Map named source fields from the frozen deterministic accounting snapshot to exact template regions and disclosure structures. Never alter financial amounts for cosmetic fit or invent unavailable comparatives. |
| OTTO-DES-006 | P0 | Planned | Preserve page composition in PDF and editable DOCX, with print-safe typography, acceptable page breaks and font fallbacks. DOCX export is future functionality, not supported by current v1.3.1 evidence. |
| OTTO-DES-007 | P0 | Planned | Golden-master visual regression for each approved template with rendered-page comparisons at fixed DPI and semantic checks for every title, total, note, page number, cut-off and missing section. |
| OTTO-DES-008 | P0 | Planned | Template owner sign-off before release. Changes to fonts, sizes, spacing, page count, alignment or section order must be reviewed and versioned. |
| OTTO-DES-009 | P0 | Planned | Auto and Advanced produce identical output for the same template version, frozen ledger snapshot, inputs and reporting settings. |

## Template format policy

Prefer a controlled DOCX template with named placeholders/content controls (for editable Word output) and a deterministic PDF renderer for distribution, or a canonical structured layout schema if high-fidelity DOCX and PDF cannot share a layout engine. PDF-only historical references are useful for approval/visual comparison but are not inherently editable source templates. Evaluate actual supplied references before choosing the implementation route. Do not promise lossless arbitrary PDF/DOCX import.

## Visual design specification (values provisional until approval)

- Typography: one professional primary family and fixed substitutes; no unlicensed bundled font files. Define title, section heading, body, table, note and footer tokens from the approved master.
- Consistency: same company identity position, date/period style, section title spacing and financial tables across all outputs.
- Numeric presentation: aligned decimals, correct negative convention and SGD units, consistent precision and comparative columns.
- Pagination: widow/orphan protection, keep headers with following table, repeat table headers, no truncation, deterministic page numbering and readable notes.
- Visual hierarchy: no decorative UI-style cards in statutory reports; restrained rules and whitespace; distinguish MA from UFS only where the approved masters require it.
- Statements: UFS section sequence and mandatory disclosures are controlled by approved reporting framework and responsible reviewer, not by template cosmetics.
- Evidence: report snapshot SHA/template revision and a QA record are linked to each export.

## Acceptance workflow

1. Obtain redacted originals of the *previously accepted* Management Accounts and UFS, including editable Word/Excel versions when available; capture approval and use rights.
2. Inventory every font, point size, paragraph style, line spacing, margin, header/footer, page break, table width, cell rule and number format from the source.
3. Create a signed-off style guide and two canonical master templates.
4. Map ledger/disclosure fields to the templates without rewriting their appearance.
5. Render synthetic scenarios: short and long company names, varied ledger lengths, no revenue, negative values, multi-page notes, previous-year comparatives, director balances and missing disclosures.
6. Compare rendered pages against golden masters and inspect PDF/DOCX manually. Pixel-diff thresholds should accommodate only justified rendering differences; text geometry, line wrapping, section order and page count receive separate pass/fail checks.
7. Require product-owner visual approval and accounting review before publishing a format as approved.

## Explicit release gate

Reports may be labelled **accounting-validated draft** when arithmetic checks pass. They may not be labelled **template-approved** until visual golden-master and owner review pass. An overall approved release must pass both independent gates. A PDF file that merely opens successfully is not sufficient.

## Known baseline and gaps

Repository v1.3.1 uses ReportLab and XlsxWriter with bundled demonstrations. Existing documentation cites a 12-page A4 landscape MA and 5-page A4 portrait UFS; neither is a user-approved golden master. Prior Inner Mirror reports were not found in the reviewed GitHub reference inventory; OTTO-REP-002 is blocked awaiting those reference files. No claim of exact historic-template reproduction is supported at present.

## Related

- [Report specifications](10_REPORT_SPECIFICATIONS.md)
- [PRD](02_PRODUCT_REQUIREMENTS_PRD.md)
- [Test strategy](18_TEST_STRATEGY.md)
- [Roadmap](19_DEVELOPMENT_ROADMAP.md)
- [Otto Auto proposal](25_AI_FIRST_AUTO_EXPERIENCE.md)
