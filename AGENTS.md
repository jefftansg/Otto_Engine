# Otto contributor instructions

1. Inspect the archive, actual entry points, data schemas, tests and current docs first. Cite functions and test evidence for claims. Track states and gaps in the [requirements register](docs/20_REQUIREMENTS_TRACEABILITY.md). Obtain approval before implementing features, changing accounting policy or deploying.
2. Keep bookkeeping deterministic, in decimal currency units with reviewed rounding. A journal balances by design. Link approved evidence to stable source, journal, ledger and report IDs. Preserve correction/reversal and prior approval history. Optional inference stays in review until a user explicitly approves a posting.
3. Test normal Guided and Advanced entry points, older ZIPs, duplicate retries, rejection without mutation, cutoffs, reconciliation and report equality. Run `python -m unittest discover -s tests -v` with dependencies installed. Record exact results, environment, skips and UI scope. Use synthetic tests and protect real client material.
4. Keep [accounting rules](docs/05_ACCOUNTING_RULES.md), [release notes](docs/21_RELEASE_NOTES.md), [regulatory register](docs/16_REGULATORY_SOURCES_AND_VERSIONING.md) and decisions current with the change. Review effective source versions and licensing. Maintain independent audit, framework and filing determinations.
5. Protect source files, identity data, exports, backups and logs. Test restore and any access-control or tenant boundary change. Use draft labels, explicit director and reviewer approval, and evidence-backed certifications only from responsible authorised professionals.

6. Maintain a strict boundary between Otto's preparation output, contracted accountant review, formal SSRS 4410 compilation/SSRE review engagements, and independent audits under SSAs. Do not describe an accountant's quality review as assurance, issue an audit opinion, mark an Otto-generated UFS as audited, or imply that a partner is employed or engaged without evidence. Record the client's separate engagement of any auditor, auditor independence decisions by that professional, client permission before evidence sharing, and professional approval responsibilities. Treat audit-ready export, external reviewer routing and related audit-handoff status as planned unless verified in source and tests. See OTTO-SVC-001/002 and OTTO-AUD-001/002.

## Planned Otto Auto guardrails (21 November 2026)

Use docs/25_AI_FIRST_AUTO_EXPERIENCE.md as the target UX specification. Its requirements and tests remain planned. Do not claim they ship in v1.3.1. AI can propose source-linked classifications; no silent posting, invented balances, fabricated disclosures or acceptance of date-edited demo statements as authentic bank evidence. Preserve double-entry arithmetic, one shared ledger, traceability, corrections, authorised status labels and legacy ZIP compatibility. Keep source statements out of GitHub.

## Proposed Otto Auto safeguards (21 November 2026)

See docs/25_AI_FIRST_AUTO_EXPERIENCE.md. Preserve v1.3.1 release claims. Never silently post AI proposals, invent figures, treat a modified demo statement as genuine evidence, or mark incomplete reports final. Maintain a single deterministic double-entry ledger, source provenance, clear review states and legacy ZIP compatibility.

## Unreleased Auto + multi-bank candidate (22 November 2026)

The development branch selectively integrates Auto and reviewed multi-bank controls; see docs/29_AUTO_MULTI_BANK_INTEGRATION.md for tested scope and limits. Historical release claims remain 1.3.1. Preserve one ledger, transfer/source-bound category revisions, no-post-before-review, provisional frozen reports in every view, client cache isolation and existing single-account behavior. This does not approve the full PRD, master templates, accounting policy, release or GitHub merge.
