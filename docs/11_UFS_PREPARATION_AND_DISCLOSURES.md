# UFS preparation and disclosures

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Needs review
- Owner: Accounting
- Related requirements: OTTO-UFS-001, OTTO-UFS-002, OTTO-COMP-002
- Sources/evidence: engine/reports.py:194–277, guided.py:510–516, app.py:579

## Purpose and scope

Control private-company draft preparation and the evidence required before issue.

## As-is implementation (evidence-backed)

Company UI guards UFS for Private limited company. The renderer and CLI demo route can build company-form output without the UI entity guard. Position and income use current inputs and a fixed COA. Equity is a simplified roll-forward. Cash uses ledger/counter-account classification. Directors' placeholders, accounting policies, going concern, review warnings and notes exist. Prior-profit handling does not supply complete comparative columns or disclosures. Flags for framework, disclosures and director review raise warnings.

## To-be requirements

Confirm entity type and reporting dates, applicable standard edition, audit decision and prior statements before preparing company forms. For first-year reports verify period dates, opening balances and whether comparatives are applicable. Later periods require prior audited or approved figures as applicable and explanation of restatements or policy changes. For sole proprietors use an adapted management package with owner's capital/drawings and entity-appropriate disclosures.

| Review item | Evidence to obtain before issue |
| --- | --- |
| Going concern | Signed assessment, forecasts, cash runway, financing availability and relevant subsequent developments. Escalate material uncertainty. |
| Related parties | Reviewed party list, director transactions and balances, terms, guarantees and disclosures applicable to the framework. |
| Revenue, assets and estimates | Contracts, recognition policy, impairment and depreciation working papers with approved judgments. |
| Equity and directors | Register and minutes supporting capital, distributions, nominations, signature authority and dates. |
| Tax | Reviewed supplied journals and applicable current/deferred disclosures. Tax computation is outside Otto's service. |
| Other conditional notes | Commitments, contingencies, subsequent events, geographic/segment or other disclosures where applicable. Record rationale for each omission. |

Separate preparation, in-review and authorised snapshots with named approvals. Keep directors’ assertions, solvency, going concern, tax treatment, comparatives and approval dates open until supported. Review statutory signature requirements under s201(16) and the Twelfth Schedule before issue. Indexed SSO text identifies the two-director rule. Confirm the treatment where the company has a sole director, and any relief or special circumstances, against the complete current Act.

## Acceptance criteria / verification

Missing required notes or comparatives create review blockers for authorisation. Submission readiness requires independent duty/eligibility checks. Confirm PDF generated for sole proprietor through normal UI cannot contain company directors' statement. Verify the signatory placeholders are blank until authorised.

## Risks, limitations and open questions

The current renderer gives illustrative disclosures and review text. Entity- and framework-specific coverage, policy selection and disclosure completeness require Accounting approval.

## Related documents

- [Report Specifications](10_REPORT_SPECIFICATIONS.md)
- [Singapore Compliance](12_SINGAPORE_COMPLIANCE.md)
- [Accounting Framework Eligibility](14_ACCOUNTING_FRAMEWORK_ELIGIBILITY.md)
- [Open Questions](23_OPEN_QUESTIONS.md)
