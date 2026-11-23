# Otto Financial Report Engine v1.4.0-dev.6 — Quick Start

This is the Auto + multi-bank development candidate based on merged PR #21 with a separate Bizfile routing fix, not a final release. It supersedes the candidate previously labelled 1.3.1. Historical stable v1.3.1 files remain unchanged.

1. Save your existing workspace ZIP before stopping its Terminal with Control+C.
2. Extract the new source ZIP into its own **Otto_Engine_v1.4.0-dev.6** folder. Do not overwrite the older folder.
3. Open **START_ON_MAC.command** in this new folder. Keep Terminal open and visit http://localhost:8501. Python 3.9–3.12 is required; first start installs pinned dependencies.
4. Check that the sidebar, page header and startup message show **1.4.0-dev.6**.
5. If port 8501 is occupied and you want a separate session, open Terminal in the new folder and run `OTTO_PORT=8507 ./START_ON_MAC.command`, then visit http://localhost:8507.

Auto opens by default. The sidebar shows progress, current stage and next action above the drop box. Upload original bank documents, confirm company identity and reporting dates, then review each account's identity, coverage and balances. Approvals never happen silently. Restore saved accounting through the separate ZIP control; re-upload originals to recheck source coverage.

To remove session sources, expand **Remove uploaded files**, select files under **Select uploaded files to remove**, and click **Remove selected uploads**. Original disk files and recorded accounting/evidence remain; missing sources require recheck.

Keep all output provisional/draft. Local extraction and suggestions have no connected cloud AI provider. Owner, accounting and master-template acceptance remain open; this candidate does not merge the separate routing-fix PR or authorise statements. See docs/29, docs/30 and docs/31 for exact scope and validation.

Company profiles/Bizfiles are reviewed for company particulars. Their bank/account/currency columns show **Not applicable**; they do not establish bank coverage.

## Bank review without repeated evidence entry

For uploaded originals, Otto records statement filenames and fingerprints automatically. Enter your reviewer name, check the account details/balances and approve; **Review note (optional for uploaded statements)** can be left blank. Transaction imports also record their uploaded source references automatically after your explicit review.

For missing originals or manually entered transaction rows, provide a note identifying what you reviewed. Incomplete work can be retained with **Save review notes and continue** and **Save my work (ZIP)**. This saves preparation notes without approving the account or posting anything.

OCBC daily-detail exports may contain transactions posted after the selected monthly export end. These are accepted with their original posting dates when printed counts, totals and running balances reconcile. Confirmed financial-year cutoffs still apply; earlier-than-export-start, impossible/future dates and potential repeated transactions across files still need review. Do not redate the source files.

## Send and receive client clarifications in Excel

1. In Auto, open **Client clarifications - Excel export and import** near Review exceptions.
2. Click **Prepare clarification workbook**, then **Download client clarification workbook**. Save your workspace ZIP after preparing the workbook so its matching export record is retained.
3. Send the Excel file to your client yourself. They fill the green cells on **Transactions** and **Other questions**. A short explanation of the business purpose is enough to start; money type, document reference and responder name help your review. They do not need accounting codes.
4. Upload the returned file under **Import completed clarification workbook**. Otto previews the replies. Enter **Replies reviewed by**, tick the review confirmation, then click **Approve and save clarification replies**.
5. Transaction explanations appear in **Client reply** beside the category editor. Choose and approve accounting categories separately. General answers are saved to their original questions. No transactions, amounts, dates, transfers or journals are changed by answer import.

Blank answers stay open. Sorted rows and partial replies are supported; keep grey source cells, headings and all query rows unchanged. If financial facts or company/reporting dates change, prepare a new workbook. Category choices may continue while waiting for replies. A returned workbook cannot overwrite newer answers already recorded in Otto. Original documents are referenced, not embedded; collect attachments separately.

The same controls are also available in the single-account Guided questions panel. Detailed multi-bank Guided/Advanced views share the saved answers and ledger; use Auto for the Excel exchange.

## Enter replies directly in Otto

In Auto, open **Enter client replies directly in Otto** near Review exceptions. Each pending transaction has a **Reply category** dropdown; other questions have **Reply option**. Choose a listed response, or **Other / type manually** and fill **Custom category / reply** or **Client explanation**. Document and responder fields are optional context. Enter **Replies recorded by** and click **Save client replies**. This saves the explanations without an Excel round trip.

General Yes/No answers can clear the matching clarification question. **Not sure** keeps it open. Names and open-ended questions need a typed explanation. For transactions, clear reply categories such as Bank charges or Sale appear as proposals in **Review transaction categories**; use **Approve and save reviewed categories** to apply them. A reply alone does not change ledger codes, create a transfer or resolve missing documents/balance mismatches. A custom reply does not automatically create a new accounting account. Excel import/export remains available.
