# Otto Financial Report Engine v1.4.0-dev.1

23 November 2026. Development identifier authorised by the user to distinguish the current Auto/multi-bank candidate from historical v1.3.1. Draft PR #21 remains unmerged. This is not a final release, template sign-off or accounting approval.

The sidebar, page header, Mac startup message and source ZIP/folder use **1.4.0-dev.1** from one committed `VERSION` file. The source packager preserves the prerelease suffix and embeds the version and source commit in `SOURCE_MANIFEST.json`. Future candidate builds increment the `dev` counter; final release promotion requires separate acceptance.

This build includes local upload-first Auto, reviewed multi-bank SGD identification/coverage/transfers, provisional PDF/Excel output, header-only client identity, the supported OCBC daily-statement profile, sidebar uploader and progress/current/next, setup acknowledgement and session upload removal. Exact behaviours and remaining acceptance gates: docs/28 through docs/31.

No accounting, extraction, posting, dependency, workspace schema or report-template behaviour changes in this numbering update. Historical release notes are retained. Full regression and archive-manifest validation accompany the candidate; CI results are recorded in PR #21.
