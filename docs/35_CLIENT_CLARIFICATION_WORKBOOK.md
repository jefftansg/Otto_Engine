# Client clarification workbook round trip

23 November 2026. Development candidate **1.4.0-dev.5**. Local Excel export and reviewer-approved answer import; no sending service, cloud AI, final release or financial/template approval.

## User workflow

In Auto's Review exceptions area, open **Client clarifications - Excel export and import**, click **Prepare clarification workbook**, then **Download client clarification workbook**. Save the workspace ZIP after preparation: it retains the matching export record. Send the downloaded file to the client separately. The same controls are available in single-account Guided's question panel; detailed multi-bank views share the records and use Auto for this exchange.

The client fills green answer cells in **Transactions** and **Other questions**. Transaction prompts show dates, the account label, original description and SGD receipts/payments, followed by explanation, optional plain-language money type, document reference, responder and response status. General questions show the question and requested information. Blank replies stay open; partial replies and sorting complete query rows are supported. Client accounting codes are not requested. Original source documents are not embedded; collect referenced attachments separately.

Upload the returned workbook under **Import completed clarification workbook**. Otto previews the original transaction/question context next to the replies. Enter **Replies reviewed by**, confirm review and click **Approve and save clarification replies**. The client explanations then appear in **Client reply** beside the category editor. Category selection/approval remains separate, including source-bound internal-transfer controls.

## Matching and approval boundaries

`engine/clarification_workbook.py` registers each explicitly prepared request under a random export ID in the workspace configuration. It saves immutable source cells, question IDs, company/FY context, financial source revision and prior answers. Hidden query IDs travel with sorted workbook rows; the hidden metadata sheet contains the export ID only. Replies must match the correct saved workspace and original request.

The reader validates company/period, source dates/descriptions/amounts/account/source identity, headings, unique known query IDs, unchanged source cells and prior answers. Deleted query rows, duplicate/foreign IDs, changed source facts, conflicting answers already updated in Otto, formulas, macro/external-link packages and malformed/oversized workbooks are rejected before mutation. Workbook limits are 10 MB compressed, 50 MB expanded, 20,000 queries and 5,000 characters per reply field. Source descriptions are limited to 750 characters in the client view; the full original source descriptions remain unchanged in the ledger and are included in the financial source-revision check.

Source matching excludes accounting category codes, so preparer category review may continue while the client answers. Source-row changes or reorderings, transfers and company/reporting-period changes require a fresh request. Existing replies can be re-imported without duplicate history; later partial replies can add newly answered rows without resaving unchanged replies. A different answer cannot overwrite a newer saved answer without a fresh matching request.

Approval records answers, reviewer/timestamp, export link and prior-answer audit history in configuration. It never edits bank rows, amounts, dates, categories, transfers, journals or evidence records. Transaction explanations alone do not clear uncategorised-transaction checks. General question answers follow the existing clarification-answer statuses; partial/Needs answer items stay outstanding. Saving answers does not verify attachments or change company fields automatically. Workspace ZIPs preserve pending requests and answer history.

`clarification_ui.py` provides the preparation/download, preview and explicit-review controls. `auto.py` exposes client replies as read-only category-review context and renders issue-detail currency text literally instead of accidentally treating dollar signs as Markdown maths. Switching company clears the cached download; request lookup also prevents displaying another workspace's file.

## Validation and limits

Fourteen new synthetic tests in `tests/test_clarification_workbook.py` cover typed dates/amounts and dropdowns, blank export, sorted/partial returns, company/period/source mismatch rejection, immutable-source/duplicate/deleted-row/header/formula rejection without mutation, reviewer confirmation, plain-text formula-like source data, manual answer conflicts, category progress while waiting, duplicate imports, later partial replies, invalid types/statuses, transfer exclusions, malformed/oversized/macro/external-link rejection, ZIP restoration and actual Auto preparation/preview/approval/category-context rendering. Full local suite: **228 tests passed, no skips**, macOS arm64/Python 3.9.6. Exact-head CI is recorded in the PR.

Both client-facing sheets were rendered and visually checked with a synthetic workbook using the bundled spreadsheet runtime. Blank editable cells, readable source/answer columns, frozen headers, date/currency formats, filters and dropdown validation were inspected. Round trips use the pinned runtime's installed XLSX writer/reader, consistent with Otto's existing application exports; no runtime dependency is added. Native Microsoft Excel editing/printing was not automated. No private ledger, client workbook or attachment is committed, and no message/file was sent to any recipient.
