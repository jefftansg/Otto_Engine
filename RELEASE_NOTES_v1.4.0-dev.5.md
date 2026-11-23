# Otto Financial Report Engine v1.4.0-dev.5

23 November 2026. Development candidate adding client clarification workbook export, response preview and reviewer-approved answer import. No final release or financial/template approval.

Export uncategorised transactions and outstanding client questions into a formatted Excel workbook with green input cells, plain-language money-type/status lists, dates/amounts and source descriptions. Returned replies match stable query IDs and the exported workspace/source snapshot. Sorting and partial replies are supported. Validate source cells, company/FY, current financial facts and prior answers; reject unknown/duplicate IDs, changed source facts, stale/conflicting answers, formulas, macros/external links and oversized/malformed input.

Explicit review saves answers and audit history only. Transaction explanations appear beside category review; accounting codes, transfers, ledger rows and journals are never changed automatically. Unanswered items remain open, identical imports are idempotent and workspace ZIPs retain the export/reply history. Existing monthly-posting, profile-routing and simpler source-review fixes remain. See docs/35_CLIENT_CLARIFICATION_WORKBOOK.md and the current Quick Start.
