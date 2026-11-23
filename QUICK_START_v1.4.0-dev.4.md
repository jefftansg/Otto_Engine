# Otto Financial Report Engine v1.4.0-dev.4 — Quick Start

This is the Auto + multi-bank development candidate based on merged PR #21 with a separate Bizfile routing fix, not a final release. It supersedes the candidate previously labelled 1.3.1. Historical stable v1.3.1 files remain unchanged.

1. Save your existing workspace ZIP before stopping its Terminal with Control+C.
2. Extract the new source ZIP into its own **Otto_Engine_v1.4.0-dev.4** folder. Do not overwrite the older folder.
3. Open **START_ON_MAC.command** in this new folder. Keep Terminal open and visit http://localhost:8501. Python 3.9–3.12 is required; first start installs pinned dependencies.
4. Check that the sidebar, page header and startup message show **1.4.0-dev.4**.
5. If port 8501 is occupied and you want a separate session, open Terminal in the new folder and run `OTTO_PORT=8507 ./START_ON_MAC.command`, then visit http://localhost:8507.

Auto opens by default. The sidebar shows progress, current stage and next action above the drop box. Upload original bank documents, confirm company identity and reporting dates, then review each account's identity, coverage and balances. Approvals never happen silently. Restore saved accounting through the separate ZIP control; re-upload originals to recheck source coverage.

To remove session sources, expand **Remove uploaded files**, select files under **Select uploaded files to remove**, and click **Remove selected uploads**. Original disk files and recorded accounting/evidence remain; missing sources require recheck.

Keep all output provisional/draft. Local extraction and suggestions have no connected cloud AI provider. Owner, accounting and master-template acceptance remain open; this candidate does not merge the separate routing-fix PR or authorise statements. See docs/29, docs/30 and docs/31 for exact scope and validation.

Company profiles/Bizfiles are reviewed for company particulars. Their bank/account/currency columns show **Not applicable**; they do not establish bank coverage.

## Bank review without repeated evidence entry

For uploaded originals, Otto records statement filenames and fingerprints automatically. Enter your reviewer name, check the account details/balances and approve; **Review note (optional for uploaded statements)** can be left blank. Transaction imports also record their uploaded source references automatically after your explicit review.

For missing originals or manually entered transaction rows, provide a note identifying what you reviewed. Incomplete work can be retained with **Save review notes and continue** and **Save my work (ZIP)**. This saves preparation notes without approving the account or posting anything.

OCBC daily-detail exports may contain transactions posted after the selected monthly export end. These are accepted with their original posting dates when printed counts, totals and running balances reconcile. Confirmed financial-year cutoffs still apply; earlier-than-export-start, impossible/future dates and potential repeated transactions across files still need review. Do not redate the source files.
