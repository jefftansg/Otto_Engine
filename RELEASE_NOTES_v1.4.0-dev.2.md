# Otto Financial Report Engine v1.4.0-dev.2

23 November 2026. Development follow-up to merged PR #21. This fix is proposed separately; no final release or financial/template authorisation.

Company profiles/Bizfiles are routed to company-field review before bank identification. The mixed bank-intake inventory labels document type and shows bank/account/currency as Not applicable for profiles and supporting documents. Company-name/UEN mismatch still requires review. Duplicate and unreadable documents retain their checks. Recognised bank sources still require supported bank identity, account identity, currency, balances and coverage. Non-bank documents never join bank groups or alter bank coverage/revision hashes; no setup fields or transactions are silently changed.

Validation and exact evidence: docs/32_COMPANY_PROFILE_INTAKE_FIX.md. Current build version is 1.4.0-dev.2; historic version files are retained.
