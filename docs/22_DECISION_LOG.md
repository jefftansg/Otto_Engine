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

## Decision 011 — persistent issue handling and native stage tabs

20 November 2026; Engineering; implemented at the user's request. Show every generated issue with an action and lifecycle, retain notes and cleared history in the optional workspace `issue_register`, and reopen recurring conditions. Permit manual Open/In progress only; no manual accounting-clear override. Preserve source-dependent findings as Needs recheck when original bank files are unavailable. Use native tabs with accessible colour/text statuses. Streamlit 1.50 retains tab selection across reruns, so explicit navigation changes an invisible tab-label identity suffix to apply the requested default; ordinary reruns preserve the selected tab. Place developer controls in a separate toolbar strip above branding.

Evidence: `engine/issue_tracker.py`, `engine/stages.py`, `engine/attention.py`, `guided.py`, `app.py`, `tests/test_issue_tracker.py`, `tests/test_stages.py`; 86 passing tests plus local browser verification. Issue history is client-supplied workspace metadata, not a tamper-proof audit log or authorised certification. No accounting-policy or deployment change.

## Decision 012 — engine version v1.3.0

20 November 2026; Engineering; implemented at the user's request. Identify the feature update as v1.3.0. Display a prominent Engine version 1.3.0 badge below the product title and repeat it in bold in the sidebar; align the Mac launcher and current README/Quick Start/release notes. Retain historical v1.2.4 release and audit evidence. No accounting or regulatory-policy change. Verification: 86 passing tests and local browser confirmation of both labels.

## Decision 013 — Company-first setup and current service scope

20 November 2026; implemented at the user's request in v1.3.1. Place Company first/default, allow optional ACRA PDF or manual details, confirm the financial year before general accounting intake, then Documents/Bank/Other records/Reports. Keep the setup form ahead of issue triage. Reorder status and issue routing consistently. Initial Company clearance is the basic identity/date gate; later UFS particulars remain tracked. Target the user's bookkeeping and draft UFS offering now; defer corporate-secretarial workflows, audit services/automated audit-exemption assessment, tax filing and ACRA/XBRL submission to future scope. No new regulatory assessment, automatic entry, accounting-policy change or report-gate relaxation is authorised.

## Decision 014 — M0 stabilization baseline

20 November 2026; implemented under the user's explicit M0 request. Fail early on unsupported runtime, incomplete source or unavailable port; preserve running sessions and offer an explicit alternate port. Pin the actually verified dependency graph, fingerprint both dependency inputs, and check installed consistency. Match address reuse so just-stopped instances can restart. Replace deprecated UI width arguments without changing layout intent. Build releases from committed Git source only, with deterministic metadata, executable launcher permissions, per-file SHA-256 manifest and archive checksum. Preserve bookkeeping rules and the limited service scope. Evidence: 100 passing tests in existing/clean Mac environments, legacy workspace equality, clean/offline launch and occupied-port recovery; residual acceptance is in the M0 record.

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

## Decision 015 — separate uploads from saved extraction history

21 November 2026. User-authorized obsolete-file removal distinguishes in-memory uploads from statement summaries persisted in company.json. Remove only selected summaries; retain accounting and evidence provenance and invalidate bank balance confirmation. Previously exported ZIPs remain immutable. No accounting recognition or measurement policy changed.

## OCBC extraction fix — 21 November 2026

Decision 016 — support explicit OCBC summary labels. User-authorized parser repair recognises B/F and C/F with existing conservative amount selection. Unprefixed dates are accepted only as complete OCBC statement headings; differing heading periods remain unresolved. Use synthetic fixtures and keep client bank statements out of version control.

## Decision 017 — Otto Auto product direction (21 November 2026)

Approved product direction, implementation planned: improve on the current cumbersome Guided setup using default document-first intake, evidence-driven automatic preparation, exception-only questions, and report generation; preserve Advanced and one ledger. AI may propose but not post, invent source evidence, override reconciliations or authorise reports. The v1.3.1 Company-first interface remains the implemented baseline. New requirements OTTO-AUTO-001–008 and proposed tests follow. See [Otto Auto specification](25_AI_FIRST_AUTO_EXPERIENCE.md).

## Decision 018 — report consistency outranks workflow polish (21 November 2026)

Product priority clarified: matching the previously approved financial-report layouts, font sizes, whitespace, table formatting and pagination is more important than merely reducing data-entry steps. Choose template-first generation with an immutable approved style/version; require independent numeric and visual acceptance. No claim of exact match until historical examples received and owner signs off. Preserve current v1.3.1 baseline. See [Report Design System](26_REPORT_DESIGN_SYSTEM_AND_TEMPLATE_FIDELITY.md).

## Decision 017 — local Auto preview and reference-derived layouts

User authorized Otto Auto implementation on 21 November 2026, selected local processing and supplied report references. Implement a local upload-first candidate, preserving the shared Decimal ledger and explicit approvals. No provider/data transmission is configured. Add versioned typography profiles and blank signature regions without copying client figures, disclosures or signatures. Exact master-template fidelity and owner/professional approval remain independent release gates. Keep existing sessions intact during pilot launch.
