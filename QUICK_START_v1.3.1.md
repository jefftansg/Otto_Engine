# Otto Financial Report Engine v1.3.1 — Quick Start (Mac)

## Install and open

1. Quit any previously running version, including its Terminal window (only one app can use port 8501).
2. Clone the updated repository or extract its source ZIP into a new folder.
3. Double-click `START_ON_MAC.command`. If macOS prevents it from opening, right-click, select **Open**, and confirm only if you trust the release.
4. Keep Terminal open. In Chrome or Safari, open **http://localhost:8501**.
5. Confirm **Engine version 1.3.1** appears prominently under the product title and in the sidebar. Look for the **Otto** wordmark in the sidebar, the otter mascot at the top of the screen, and **Otto | Financial Report Engine** in the browser tab.

Use Python 3.9–3.12. First launch installs the pinned dependency versions; later launches reuse the environment and can run without package-index access. A Streamlit email prompt can be left blank by pressing Return.

## Current services

This release focuses on bookkeeping and preparation of draft unaudited financial statements for SMEs. Corporate-secretarial workflows, audit services/automated audit-exemption assessment, tax filing and ACRA/XBRL submission are future scope. The optional audit-exemption guidance link is informational and does not add a questionnaire or approval gate.

## Tabs and issue handling

The five sections are tabs. Green **Cleared**, amber **Needs attention**, and grey **Not started** labels update with the current checks. Select an issue in **What needs your attention?** for its full reason, next action, and a link to the relevant section. Save progress notes as Open or In progress; checks clear resolved items and retain history. Recurrence reopens an issue. Download the issue-list CSV or save a workspace ZIP to retain the tracker.

In Documents or Bank, review flagged duplicates and documents of uncertain relevance before choosing Retain or Delete. Deletion removes selected session uploads while preserving saved accounting/evidence records. Bank balances must be rechecked after removing a statement. Original source files and retention choices are not embedded in workspace ZIPs; missing sources can leave historical source issues in Needs recheck.

## Prepare your reports in Guided Mode

1. **Company**: Enter the registered company name, UEN and financial year. Optionally upload an ACRA Business Profile here, apply detected details explicitly, then confirm dates. This is the initial screen.
2. **Documents**: Add bank statements, invoices, receipts and spreadsheets for that company. Review duplicate/relevance flags and retain or delete files. The fictional documents in `example_imports/guided_demo/` are available for practice.
3. **Bank**: Check opening and closing balances, statements and extracted transactions. Review and approve proposed imported entries.
4. **Other records**: Supply director expenses, invoices and other records as necessary. Answer the generated client clarification questions.
5. **Reports**: Clear blocking issues, run validation, export draft PDF reports and Excel working papers.

**Advanced Mode** is optional for journal adjustments, detailed ledgers, claims, receivables, reconciliation and evidence. Guided and Advanced Modes share the same accounting workspace.

## Save, restore and keep source evidence

- Use **Save my work (ZIP)** in the left sidebar. The downloaded file is `Otto_Client_Workspace.zip`.
- Use **Restore a saved company** in the sidebar to reopen it later.
- Keep original uploaded PDF/CSV/Excel source documents in your own secure folder: the saved workspace ZIP does **not** store those files.
- The app is local; no cloud backup is provided.

## Troubleshooting

- **Incomplete .venv:** rename the `.venv` folder to `.venv-backup` and launch again with internet access. Keep saved workspace ZIPs separately.
- **Nothing opens:** make sure Terminal remains open and visit `http://localhost:8501` manually.
- **Port 8501 busy:** save the existing session as a workspace ZIP, stop its Terminal with Control+C, then reopen Otto. The launcher checks first and never stops another app. For a separate instance run `OTTO_PORT=8502 ./START_ON_MAC.command` and open `http://localhost:8502`.
- **File cannot be read:** confirm the PDF contains selectable text; scanned PDFs are not automatically OCRed. Try exporting CSV or Excel from the bank.
- **Missing balances or unclear categories:** review the extracted data and answer the questions; Otto does not invent financial data.
- **Can't generate a final report:** use the questions and validation checks to resolve exceptions. All documents remain drafts requiring review.

No corporate tax computations, GST filing or ACRA/XBRL filing are included.
