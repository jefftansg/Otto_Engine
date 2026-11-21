# Otto Auto v1.4.0 — local implementation candidate

Date: 21 November 2026. User-authorized implementation against docs/25 and docs/26. The user selected local processing and supplied report references. This is a preview, not full PRD completion or M0/professional/template sign-off.

## Requirement evidence

| Requirement | Candidate state | Source / verification | Remaining scope |
| --- | --- | --- | --- |
| AUTO-001 upload first | Partial | `auto.render`, `engine.auto.analyse`; first-run UI has one PDF/CSV/XLS/XLSX drop zone and no setup fields; AppTest and live IAB synthetic CSV intake checked | Arbitrary template mapping and broad resource/performance evaluation |
| AUTO-002 source setup | Partial | `analyse`/`provenance`, contextual setup confirmation; source filename/hash/excerpts; company/UEN mismatch exclusion; unknown fields remain blank | Full per-field approval versions and automatic extraction of prior-year financial statements |
| AUTO-003 coverage | Partial | `coverage`, `bank_proposal`; exact duplicate exclusion, month/day coverage, overlaps, previous-period opening corroboration and continuity; fictional markers excluded | Multi-account posting/consolidation; cryptographic document authenticity is not established |
| AUTO-004 AI suggestions | Partial / provider deferred by user choice | Local rules plus `validate_proposals`: optional external AI JSON must match ledger revision, row, category, confidence and source ref. Category approval is explicit and undoable after ZIP restore | No LLM inference/on-device model/provider connection; no automatic external processing |
| AUTO-005 exception inbox | Partial | `_issues`/`_inbox` and existing `sync_issues`; persistent notes/answers, recheck on withdrawn sources, grouped classification, linked Advanced editors | Broader materiality rules and practitioner-reviewed issue completion |
| AUTO-006 reporting | Partial | `frozen_report`/`export_bundle`; immutable package copy, snapshot/layout/renderer metadata and file hashes; provisional PDF/XLSX, source and exception schedules | Final report authorisation is unavailable; full disclosure and professional approval remain external |
| AUTO-007 continuity | Partial | Shared `Package` in Auto/Guided/Advanced; legacy ZIP and existing accounting regression tests retained; source inventory and category history survive ZIP | Signed/locked periods and richer raw/staged/corrected revision management |
| AUTO-008 usability | Planned | Automated first-screen no-form check; live synthetic upload checked | Measured comparative clicks, fields, intake-to-draft time and user acceptance |
| DES-001–005 / 009 | Partial | `report_layouts` fixed IDs/tokens; shared renderer; template metadata and explicit substitution; frozen accounting values unchanged | Exact composition/format reproduction and approved immutable masters |
| DES-006–008 | Pending | Blank signature regions, A4 draft profiles and synthetic PDF render QA are implemented | Editable DOCX, owner-approved golden-master visual comparisons and sign-off |

## Conservative import boundary

Auto proposes full current-period bank imports into an empty bank ledger for one account only. Existing records block a second full-period import, including a source re-export with changed IDs. Correct/append records in Advanced review. Every import is checked again at approval; changed setup or stale proposal IDs fail without mutation. Proposed categories do not post amounts or silently classify receipts as sales.

OCBC selectable-text fallback is restricted to the transaction area between printed B/F and C/F. Each transaction must have an unambiguous date, positive printed amount and matching running-balance movement. Printed withdrawal/deposit totals and final closing balance must independently agree. Any ambiguity returns no rows for that document. These checks support review, not authenticity or completeness certification.

## Validation

- Full suite: **130 tests passed**, zero failures/errors/skips, via `PYTHONDONTWRITEBYTECODE=1 ../Otto_Engine_v1.3.1/.venv/bin/python -m unittest discover -s tests -v` on local macOS / Python 3.9.6 with existing M0-pinned dependencies. Final packaged-source rerun is recorded in the PR. CI matrix remains Ubuntu/Python 3.9 and 3.12 plus macOS/Python 3.12.
- The expanded tests found an undo-after-restore fingerprint bug; canonical CSV-field normalisation fixed it. The regression verifies stale/rejected approval, restore and undo preserve transaction amounts.
- Synthetic reports: all three layout profiles generated PDF/XLSX with unchanged accounting totals. A reference-standard MA/reference-compact UFS preview was rendered and inspected locally: **12 MA pages / 5 UFS pages**. A one-row ledger spill was corrected with fixed wide-table tokens. Page-bound checks found no text outside the page. This is technical QA, not historic-template approval or native Excel verification.
- Live IAB: version 1.4.0, Auto default, no initial setup fields, 25 MB upload limit, synthetic CSV inventory/contextual setup/exceptions and provisional state observed. No real financial attestation or posting was clicked. Native Mac/keyboard/mobile acceptance and extended batch timing remain pending.
- Read-only local check of 11 supplied bank statements: balances/dates extracted, adjacent continuity agreed, and **122 transaction proposals** cross-checked against each statement's totals. No bank data, original files, signatures or client ledger entries were committed or automatically posted. Fictional November evidence was excluded from year coverage.

## Template and privacy status

Three supplied PDF references and one workbook were inspected locally. Only reusable formatting tokens and blank signature regions enter source control. Reference financial content, claims, original signatures and font binaries are not copied. PDFs use built-in Helvetica instead of reference Arial/Liberation Sans; workbook fonts are Arial with controlled A4 print settings. Existing section composition is preserved, so exact reference fidelity is not asserted. A successful export is not owner/practitioner approval.

Processing remains local, loopback-bound, with usage statistics disabled. Original documents stay in memory for the running session and are excluded from workspace ZIPs; source filenames, hashes, excerpts, proposals and accounting/issue data in the ZIP remain sensitive client data. Optional AI review export is a local download, not a network transmission. No provider, OCR, account service, email, filing or cloud deployment was introduced.
