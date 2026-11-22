# Otto Financial Report Engine v1.4.0-dev.1 — Quick Start

This is the Auto + multi-bank development candidate in draft PR #21, not a final release. It supersedes the candidate previously labelled 1.3.1. Historical stable v1.3.1 files remain unchanged.

1. Save your existing workspace ZIP before stopping its Terminal with Control+C.
2. Extract the new source ZIP into its own **Otto_Engine_v1.4.0-dev.1** folder. Do not overwrite the older folder.
3. Open **START_ON_MAC.command** in this new folder. Keep Terminal open and visit http://localhost:8501. Python 3.9–3.12 is required; first start installs pinned dependencies.
4. Check that the sidebar, page header and startup message show **1.4.0-dev.1**.
5. If port 8501 is occupied and you want a separate session, open Terminal in the new folder and run `OTTO_PORT=8507 ./START_ON_MAC.command`, then visit http://localhost:8507.

Auto opens by default. The sidebar shows progress, current stage and next action above the drop box. Upload original bank documents, confirm company identity and reporting dates, then review each account's identity, coverage and balances. Approvals never happen silently. Restore saved accounting through the separate ZIP control; re-upload originals to recheck source coverage.

To remove session sources, expand **Remove uploaded files**, select files under **Select uploaded files to remove**, and click **Remove selected uploads**. Original disk files and recorded accounting/evidence remain; missing sources require recheck.

Keep all output provisional/draft. Local extraction and suggestions have no connected cloud AI provider. Owner, accounting and master-template acceptance remain open; this version change does not merge PR #21 or authorise statements. See docs/29, docs/30 and docs/31 for exact scope and validation.
