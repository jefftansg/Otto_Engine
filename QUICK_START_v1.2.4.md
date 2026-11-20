# Otto Financial Report Engine v1.2.4 — Quick Start (Mac)

## Install and open

1. Quit any previously running version, including its Terminal window (only one app can use port 8501).
2. Unzip `Otto_Financial_Report_Engine_v1.2.4_Mac.zip` into a new folder.
3. Double-click `START_ON_MAC.command`. If macOS prevents it from opening, right-click, select **Open**, and confirm only if you trust the release.
4. Keep Terminal open. In Chrome or Safari, open **http://localhost:8501**.
5. Look for the **Otto** wordmark in the sidebar, the otter mascot at the top of the screen, and **Otto | Financial Report Engine** in the browser tab.

On first run, Python packages may need installing. A Streamlit email prompt can be left blank by pressing Return.

## Prepare your reports in Guided Mode

1. **Upload** an ACRA Business Profile and bank statements (PDF, Excel, CSV). You can practice with the fictional documents shipped in `example_imports/guided_demo/`.
2. **Company**: Confirm company name, UEN and reporting year dates. The engine does not infer missing financial years silently.
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

- **Nothing opens:** make sure Terminal remains open and visit `http://localhost:8501` manually.
- **Port 8501 busy:** quit previous versions and reopen Otto.
- **File cannot be read:** confirm the PDF contains selectable text; scanned PDFs are not automatically OCRed. Try exporting CSV or Excel from the bank.
- **Missing balances or unclear categories:** review the extracted data and answer the questions; Otto does not invent financial data.
- **Can't generate a final report:** use the questions and validation checks to resolve exceptions. All documents remain drafts requiring review.

No corporate tax computations, GST filing or ACRA/XBRL filing are included.
