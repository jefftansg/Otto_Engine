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
