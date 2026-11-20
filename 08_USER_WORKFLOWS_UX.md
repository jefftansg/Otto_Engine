# User workflows and UX

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Draft
- Owner: Product
- Related requirements: OTTO-UX-001, OTTO-UX-002, OTTO-CO-001, OTTO-QA-001
- Sources/evidence: app.py:31–168, guided.py:21–516, engine/attention.py

## Purpose and scope

Give non-accountants an upload-first journey and preparers direct access to detailed reviews.

## As-is implementation (evidence-backed)

| Stage | Action and feedback |
| --- | --- |
| Upload | Start empty, restore ZIP, load bundled demo or upload PDF/Excel/CSV. Show parsing status and evidence registration. |
| Company | Propose fields, confirm name/UEN and reporting dates. |
| Bank | Review continuity and balances, preview candidate rows, confirm import, assign categories or route for opening balance support. |
| Other records | Review checklist and clarification responses, route claims, invoices and journals to Advanced. |
| Reports | See readiness, blocking errors and warnings, save package and download available drafts. |

`engine/attention.py` builds stage and Advanced page routes. Both modes share `st.session_state.pkg`. Advanced exposes company/period setup, intake, bank/claims/journals, AR/evidence, ledger/TB and checks. Save ZIP before starting another client or closing the session. Demo can be loaded from the sidebar or by using the fictional Guided uploads.

## To-be requirements

Show each stage as empty, in review, action required or ready. Display short issue messages, next action, provenance and return destination. Use keyboard-operable controls with visible focus, error descriptions independent of colour and readable progress. Offer undo via staged changes/reversals and prompt before replacing unsaved work. Advanced adds controlled COA, payables, permissions and period actions. Use plain questions such as “Who paid this bill?” and “Which statement shows the first day of your reporting period?”

## Acceptance criteria / verification

In a Chrome and Safari Mac session load a blank workspace, complete fictional intake, route an unmatched claim to Advanced and return, compare entries before/after navigation, and restore ZIP in a fresh session. Test keyboard order, empty/material error states, cancelling actions and corrective undo.

## Risks, limitations and open questions

Routing has backend checks. Mac rendering, accessibility and unsaved-change recovery need live verification.

## Related documents

- [Document Extraction](06_DOCUMENT_EXTRACTION.md)
- [Clarification Engine](09_CLARIFICATION_ENGINE.md)
- [Report Specifications](10_REPORT_SPECIFICATIONS.md)
- [Test Strategy](18_TEST_STRATEGY.md)
