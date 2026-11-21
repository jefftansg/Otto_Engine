# Otto v1.4.0 — local Auto preview

Date: 21 November 2026. Candidate for review; M0 and professional/template acceptance are still open.

- Default upload-first Auto workspace with contextual company/date confirmation after intake. Guided and Advanced remain available against the same package.
- Local document inventory, SHA-256 identities, source field excerpts, company conflict checks, account grouping, monthly coverage, opening evidence and latest closing balances. Demonstration markers exclude files from bank evidence; this is not authenticity certification.
- Exact duplicates are excluded. Source periods outside the year can corroborate opening balances but cannot count as in-year coverage or post in-year transactions.
- Reviewed one-account full-period import into an empty bank ledger. Amount/balance/coverage mismatches and retries are blocked; existing accounting records are preserved.
- OCBC text transaction proposals use printed running balances plus withdrawal/deposit totals as independent checks. Human review is still required. Read-only local validation of 11 user-supplied statements produced 122 proposals, without adding client material to the repository or posting it to books.
- Consolidated persistent exceptions, answers, progress, source rechecks and linked detailed editors. Local category suggestions require explicit save. Optional untrusted AI JSON proposals require an exact ledger revision, valid categories and matching source references; no AI service is connected and no cloud processing occurs.
- Provisional report bundles use one frozen ledger snapshot, shared renderers, explicit readiness labels, per-file hashes and layout metadata. Reference-derived compact/standard typography and blank director signatory boxes are available. Historical Arial/Liberation Sans are substituted with Helvetica in PDF; exact visual fidelity and template-owner approval are pending.
- Version 1.4.0 is visible in header/sidebar/launcher. Guided Documents green now says **Uploaded files reviewed**, not complete-year clearance.

## Verification and limits

See `docs/27_OTTO_AUTO_IMPLEMENTATION.md` for exact test and render evidence. Synthetic scenarios cover rejected/stale approvals without mutation, duplicate retries and restore, coverage gaps, fictional evidence, cross-company records, report totals and source provenance. No real client files, signatures or account data are committed.

This release does not implement OCR, direct/on-device LLM inference, multi-account posting/consolidation, arbitrary template import, DOCX export, professional sign-off or final/authorised output. Reference-derived layouts are review candidates, not approved replicas. Native Excel, broad manual/mobile/keyboard UAT and the usability benchmark remain pending. No accounting recognition/measurement, tax, audit or filing policy changes are made.
