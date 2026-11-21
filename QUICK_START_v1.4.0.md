# Otto v1.4.0 — local Auto preview

This is a review candidate. It has not received professional acceptance or final template approval. Keep a saved workspace ZIP before trying a new version.

1. Open `START_ON_MAC.command`. If a previous Otto is open, save its workspace and either stop that Terminal with Control+C or use an explicit unused `OTTO_PORT`.
2. **Auto** opens with a single upload box. Add PDF, CSV, XLS or XLSX files: at most 50 files / 100 MB total / 25 MB each. No company form is required before uploading. Text-based PDFs work best; OCR is not included.
3. Review the file inventory. Exact content duplicates are excluded from calculations. Marked fictional/demo evidence cannot establish bank coverage. Supporting records and template references are retained for manual mapping.
4. Review the proposed company name/UEN and confirm the reporting dates against records. Bank statement dates describe coverage; they do not prove the company's financial year. Unknown values stay blank.
5. Check each account's monthly coverage, source-linked opening balance and latest closing balance. Missing months, overlap, conflicting balances and company mismatches remain exceptions. Out-of-period statements may corroborate opening balances but do not contribute current-year months or transactions.
6. Review proposed transactions. Auto imports a complete, consistent, single-account period into an empty bank ledger only after explicit review. Unsupported/ambiguous rows stay blocked. Use **Workspace view → Advanced** for detailed mapping or additional records. Existing books are never replaced.
7. Review categories and explicitly save them. Suggestions are local rules, not a connected AI model. Incoming money is not automatically sales. All arithmetic remains Decimal/double entry. Optional external AI JSON proposals are validated and staged, never automatically posted; no cloud data is sent by Otto.
8. Resolve the exceptions inbox. Record evidence-backed answers and progress; notes alone do not clear live validation errors. Use the linked detailed editor for claims, journals and other accounting entries. Auto, Guided and Advanced share the same books.
9. Choose a versioned draft MA/UFS layout and generate the **provisional** PDF/XLSX package. It contains the source inventory, exceptions, frozen ledger snapshot hash, renderer/layout metadata and file hashes. Reference compact/standard layouts are derived from supplied formatting, but exact reproduction and visual sign-off remain pending. PDFs substitute Helvetica for Arial/Liberation Sans. No signatures or client amounts are copied from reference reports.
10. **Save Auto workspace ZIP** after changes. It includes accounting records, issue progress and source summaries, but not original PDFs. On restore, upload original evidence again to recheck coverage.

Use **Review or delete uploaded files** for in-memory uploads and **Remove obsolete saved statement history** for summaries from older workspaces. Recorded transactions and original disk files are retained; deleting source evidence requires balance checks again. Original ZIP backups remain unchanged.

No final/authorised, audited, tax, GST, filing or XBRL output is produced. DOCX template import/export, a connected/on-device language model, multi-account consolidation and owner-approved golden masters are not implemented.
