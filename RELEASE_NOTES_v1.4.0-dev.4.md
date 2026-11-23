# Otto Financial Report Engine v1.4.0-dev.4

23 November 2026. User-authorised monthly export/posting-date rule change. Development candidate; no final release or financial/template attestation.

Supported OCBC daily-detail statements can include transactions posted after the selected monthly export end. Preserve the actual posting dates and source references. Continue to require printed debit/credit counts and gross totals, running balances, opening/closing balances, source coverage and explicit approval. Posting after export end does not create extra coverage days. Dates before export start or after printing still require review. Financial-year cutoffs remain enforced at import; possible repeated transactions across different source files are flagged without silent deletion.

Includes the previous Bizfile routing, automatic evidence references, saved unapproved review notes and precise rejection messages. See docs/34_LATE_BANK_POSTING_DATES.md and the current Quick Start for exact scope, evidence and limits.
