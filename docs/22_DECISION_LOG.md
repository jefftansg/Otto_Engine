# Decision log

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Draft
- Owner: Product
- Related requirements: OTTO-BASE-001, OTTO-UX-001, OTTO-ACCT-001, OTTO-COMP-002, OTTO-SEC-001
- Sources/evidence: README.md, START_ON_MAC.command, app.py, engine/core.py, master documentation scope

## Purpose and scope

Record decisions and unresolved alternatives with owners and dates where known.

## As-is implementation (evidence-backed)

| ADR | State and date | Owner | Decision, rationale and alternatives |
| --- | --- | --- | --- |
| 001 | Approved for documentation phase, 20 Nov 2026 baseline | Product | Documentation-only audit. Application change and deployment require separate authorisation. |
| 002 | Observed baseline, adoption date unknown | Engineering | Loopback local workflow with ZIP portability limits service dependencies. Hosted multi-client operation is deferred pending controls. |
| 003 | Observed baseline, adoption date unknown | Product | Guided default with shared Advanced workspace. A separate ledger per mode would risk divergence. |
| 004 | Superseded in current branding, v1.2.4 | Product | Historical SME Financial Report Engine name remains in archived notes. Current source/launcher identify Otto. |
| 005 | Proposed, 20 Nov 2026 | Accounting | Immutable journal and approved reversals support reproducibility. Current derived ledger is simpler but loses immutable posting history. |
| 006 | Proposed, 20 Nov 2026 | Compliance | Independent, evidence-linked regulatory decisions. A single eligibility flag cannot represent distinct obligations. |
| 007 | Unresolved, 20 Nov 2026 | Product and Accounting | Keep materially incomplete Advanced drafts available for reviewers or introduce a controlled review-only distribution step. Evaluate diagnostic usefulness and risk of accidental circulation. |

## Decision 008 — user-controlled upload review (20 November 2026)

Owner: Engineering. State: Implemented locally at the user's request to delete uploads and review duplicate/non-relevant documents before deciding to retain or delete.

Use stable filename/content identities for session file selections and content hashes for exact-duplicate detection. Keep renamed copies visible for decisions, but propose identical bank content once. Label overlap and unclear relevance conservatively. Record retention for the current reason set in session memory. Deletion affects session uploads and cache only; preserve saved evidence and historical provenance, invalidate bank balance confirmation when a statement is removed, and keep existing accounting import gates. No accounting-policy or deployment decision is included.

Evidence: `engine/intake_review.py`, `guided._delete_uploads`, `guided._upload_deletion_controls`, `tests/test_intake_review.py`, `tests/test_upload_deletion.py`; 73 passing tests including AppTest. Limitation: retention decisions are session-only, and detection does not establish semantic duplicates across unrelated layouts or prove that supporting evidence is irrelevant.

## Decision 009 — lean outsourced accountant and independent auditor model (20 November 2026)

**Owner:** Product. **Business-scope decision:** operate Otto as a bookkeeping, management accounts and draft UFS preparation service without initially employing a full-time accountant or auditor. A contracted appropriately qualified Singapore financial reporting accountant may perform optional per-client quality review; the client company separately appoints an independent ACRA-registered auditor if statutory or voluntary audit is required. Directors remain responsible for financial statements. The accounting review alone does not confer assurance. **Implementation status:** Planned; no v1.2.4 feature change.

**Alternatives:** hire in-house professionals (not chosen initial model); same firm prepares and audits (may create ethical self-review restrictions and requires the proposed auditor's own independence assessment). **Consequences:** OTTO-SVC-001/002, OTTO-UFS-003 and documented responsibilities, confidentiality and contractual terms.

## Decision 010 — audit-ready evidence is not an audit (20 November 2026)

**Owner:** Product / Accounting. **Business-scope decision:** planned read-only, versioned, consent-controlled audit-handoff ZIP with statements, books, reconciliations, source evidence, adjustments and exceptions. An independent auditor performs all procedures and issues any auditor's report; Otto never generates, signs or implies an audit opinion. **Implementation status:** Planned; OTTO-AUD-001/002.

## To-be requirements

Record owner, date, state, decision, rationale, alternatives, consequences, validation evidence and successor ADR. Preserve old decisions when superseded. Require affected teams to sign architecture/accounting/compliance decisions before implementation.

## Acceptance criteria / verification

For any approved ADR, trace consequences to requirement IDs, tests and release notes. Check approvals and references before an ADR changes a gate or ledger policy.

## Risks, limitations and open questions

Observed decisions describe source behaviour. Original approval identities and dates are unknown unless listed. See open questions for scope and control decisions.

## Related documents

- [Product Vision](01_PRODUCT_VISION.md)
- [System Architecture](03_SYSTEM_ARCHITECTURE.md)
- [Development Roadmap](19_DEVELOPMENT_ROADMAP.md)
- [Open Questions](23_OPEN_QUESTIONS.md)
