# Document extraction

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Draft
- Owner: Engineering
- Related requirements: OTTO-DOC-001, OTTO-BANK-001, OTTO-BANK-002, OTTO-BANK-003
- Sources/evidence: engine/importers.py:16–279, engine/autofill.py:135–217, guided.py:50

## Purpose and scope

Define usable evidence, proposal validation and recovery from unsupported layouts.

## As-is implementation (evidence-backed)

PDF supports text and detected tables via pdfplumber, limited to the first 80 pages and 250,000 text characters. XLSX uses stored cell values, XLS uses xlrd and CSV tries common delimiters. Limits include 25 MiB input, 20,000 cleaned rows and 65 columns. Preview can choose table and header row and map date, description, reference and deposit/withdrawal or signed amount/direction. Advanced imports also map claim, invoice and journal records. Scan-only documents receive a note and can be kept as evidence. OCR is absent.

Upload SHA-256 handles exact repeats. Row signature checks bank date, description, reference and deposit/withdrawal string values. Guided can propose text PDF and table bank records, compare statement arithmetic, verify complete contiguous single-account coverage, and require confirmations before import. Labelled account, period and balances are heuristic observations, with a masked displayed account. Arbitrary bank layouts and currency detection lack demonstrated coverage.

## To-be requirements

Capture original hash, filename, page/sheet, row or label location, raw and normalised value, parser version, confidence and reviewer status. Surface limits and rejected rows. Ask for an export or document replacement when parsing is incomplete. Validate currency, original statement dates and balance identity for each account, including opening/closing cutoffs. Distinguish exact repeats, suspect overlaps and confirmed distinct same-value records. Approved classifications require an explicit action even if optional AI proposes them.

## Acceptance criteria / verification

Check two continuous statements, missing first or last coverage, missing internal month, gap/overlap, mismatched balance, scan with no text, same-day equal genuine entries, malformed CSV, and mixed wide sheets. Verify no import on preview or ambiguity. Review an unsupported file without losing previously approved rows.

## Risks, limitations and open questions

Truncation and line-wrapping can lose context. Hash and row strings do not provide durable transaction identity across different export formats. Reviewed samples are synthetic and narrow.

## Related documents

- [Acra Company Profile](07_ACRA_COMPANY_PROFILE.md)
- [User Workflows Ux](08_USER_WORKFLOWS_UX.md)
- [Security And Privacy](17_SECURITY_AND_PRIVACY.md)
- [Test Strategy](18_TEST_STRATEGY.md)

## Proposed document-first extraction (21 November 2026)

Accept unordered mixed bank statements and books, prior-year financial statements and templates in one batch. Create evidence inventory by entity, account, period and type; cite field-level extracted balances and dates; detect missing months, overlap and duplicate content; distinguish scan-only files and mock/demo-modified statements from valid bank evidence. Never infer nonexistent period statements from filenames. Current extractor remains unchanged. See [Otto Auto proposal](25_AI_FIRST_AUTO_EXPERIENCE.md).

## Planned Otto Auto intake (21 November 2026)

Accept unordered bank statements, prior-year accounts, bookkeeping files and templates in one batch. Identify account, company, dates, opening/closing balances and monthly gaps with field-level source provenance. Detect overlaps, duplicates, inaccessible scans and altered demonstration statements; do not use the latter as genuine evidence. Current extraction implementation is unchanged. See [Otto Auto specification](25_AI_FIRST_AUTO_EXPERIENCE.md).
