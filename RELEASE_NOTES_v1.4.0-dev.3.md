# Otto Financial Report Engine v1.4.0-dev.3

23 November 2026. Development follow-up including the proposed Bizfile routing fix. No final release or financial/template approval.

Uploaded originals automatically supply filenames and SHA-256 references for explicit bank-account and source-transaction approval. Free-text review notes are optional for these source-backed approvals. Missing-original/manual-review cases still require a written evidence note; reviewer identity and financial checks remain required. Rejection messages identify the failed condition. Save review notes and continue retains unapproved preparation notes in workspace ZIPs.

Posting-date/export-period exceptions now show the actual date and period. Failed extraction no longer produces two secondary empty-row/movement warnings for the same cause. Original dates, balances and accounting policy are unchanged; no automatic backdating or missing-row assumptions. See docs/33_SOURCE_REVIEW_USABILITY.md for exact validation and limits.
