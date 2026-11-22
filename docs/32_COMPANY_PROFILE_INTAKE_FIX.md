# Company profiles in mixed bank intake

23 November 2026. Development build **1.4.0-dev.2**, based on merged PR #21. Proposed separately; no final release, template approval or financial attestation.

## Defect and correction

The Auto document inventory recognised a Bizfile as a company profile, but the subsequent shared bank-intake inventory passed every uploaded document to bank identification. That second table incorrectly displayed missing bank/account/currency/balance errors for a non-bank document.

`engine.bank_intake.analyse_documents` now recognises extracted company-profile particulars before bank identification. Profiles are labelled **Company profile / Review proposed company fields**. `bank_intake_ui.render_intake` explicitly displays document type and **Not applicable** for bank/account/currency on non-bank rows. Supporting records are retained for manual mapping. These documents never enter bank groups or change account coverage/revision hashes.

Company-name/UEN conflicts still request company review. Duplicates and unreadable files retain their original safeguards. Recognised bank sources still pass the existing strict bank/account/currency/balance/coverage checks, including unsupported-bank rejection. Analysis does not confirm setup, approve documents, import transactions or rename the company. Existing records, evidence and source history are retained.

This is an intake-routing/UI correction, not a new regulatory requirement. No accounting rules, ledger arithmetic, report templates, dependencies or sharing settings change. The code does not verify a supplied profile's authenticity or current official status.

## Validation

Five new synthetic regressions in `tests/test_bank_document_routing.py` cover profile classification/provenance without mutation, unchanged bank groups/revisions for mixed batches, mismatched/duplicate/unreadable profiles, supporting records versus unsupported bank sources, and actual Auto bank-table rendering with Not applicable values and retained accounting. Full suite: **201 tests passed, no skips**, macOS arm64/Python 3.9.6; exact-head CI is recorded in the pull request.

Read-only local re-analysis of the supplied profile returns Company profile, Review proposed company fields, no bank-identity errors and zero bank groups. No private document, extracted identifier, financial value or client screenshot is committed. UI regression uses synthetic files only.
