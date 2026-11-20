# Singapore compliance

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Needs review
- Owner: Compliance
- Related requirements: OTTO-COMP-001, OTTO-COMP-002, OTTO-COMP-003, OTTO-UFS-002
- Sources/evidence: ACRA director duties, standards and filing pages in source register

## Purpose and scope

Capture three independent decisions by company and reporting period, with reviewer and evidence.

## As-is implementation (evidence-backed)

The core validates framework label and internal accounts. It records confirmation flags and renders draft caveats. No statutory eligibility computation, authority lookup, submission workflow or approved statement issuance was observed.

## To-be requirements

| Decision | Authority and outcome | Evidence |
| --- | --- | --- |
| Audit exemption | Companies Act s205C and Thirteenth Schedule small-company/group test, or separate qualifying provision such as s205B | Corporate status, periods, financials, headcounts, group assessment, shareholder notices and reviewer. |
| Accounting framework | Prescribed applicable framework and effective edition for the financial period | Framework eligibility record, policy basis, public accountability, group and comparative considerations. |
| Preparation and filing | s199 proper accounting records, s201 statements/director duties and applicable s201A dormant relief. Filing class and exemptions assessed separately. | Evidence of dormancy/solvency if relevant, authorised PDF, filing classification and preparer handoff. |

Keep accounting records sufficient to explain transactions and financial position and enable true and fair statements. Directors review and authorise issue and remain accountable when preparation is outsourced. Confirm prescribed signature and timing duties against primary provisions. Hand filing, audit, tax and secretarial matters to the responsible professional. Escalate uncertain group perimeter, solvency, unsupported frameworks, contested audit rights, comparatives and missing statutory evidence.

## Outsourcing and independent audit boundary

ACRA guidance allows companies to outsource bookkeeping and financial-statement preparation while company **directors retain their statutory duties and accountability**. Otto's provider may engage an external accountant by contract, subject to competence, clear engagement scope, confidentiality, client authority, record access and professional liability.

A company that needs or elects an audit must arrange proper engagement/appointment of an **ACRA-registered public accountant through an appropriate registered accounting entity**, subject to applicable legal provisions. The auditor independently performs procedures under **Singapore Standards on Auditing** and issues the opinion. Otto performs neither auditor functions nor audit certification.

Do not conflate:
- preparer's ordinary financial reporting quality review (non-assurance);
- separately commissioned **SSRS 4410 compilation** (no assurance);
- formal **SSRE review engagement** (limited assurance where applicable);
- **SSA financial statement audit** (reasonable assurance and independent auditor's report).

Auditor independence, including any potential self-review threat when the same firm prepares and audits accounts, must be judged by the appointed professional under relevant Singapore ethics rules. Otto can recommend separate providers but must not pronounce independence or registration valid without evidence.

**Official references to verify at implementation/release time:**
- [ACRA — Financial reporting duties for directors](https://www.acra.gov.sg/manage/companies/legal-requirements-common-offences/preparing-financial-statements/financial-reporting-duties-for-directors/)
- [ACRA — Public accountant eligibility](https://www.acra.gov.sg/register/public-accountant/requirements-eligibility/)
- [ISCA — Singapore Standards on Auditing](https://www.isca.org.sg/standards-guidance/audit-assurance/standards-and-guidance/singapore-standards-on-auditing-%28ssas%29)
- [ISCA — Singapore Standards on Related Services](https://www.isca.org.sg/standards-guidance/audit-assurance/standards-and-guidance/singapore-standards-on-related-services-%28ssrss%29)

These statements describe planned service handoffs, not implemented integration, professional assurance or regulator endorsement.

## Acceptance criteria / verification

Demonstrate independently that audit exemption, accounting-framework eligibility and filing relief can differ for the same entity. Record reasons and dated authority for decisions. Confirm a preparation draft cannot be marked audited or filed.

## Risks, limitations and open questions

ACRA guidance and indexed SSO passages were reviewed. Direct retrieval of full current statutory sections failed. Obtain primary provision and professional review for unusual fact patterns and authorisation.

## Related documents

- [Audit Exemption Eligibility](13_AUDIT_EXEMPTION_ELIGIBILITY.md)
- [Accounting Framework Eligibility](14_ACCOUNTING_FRAMEWORK_ELIGIBILITY.md)
- [Acra Filing Scope And Xbrl](15_ACRA_FILING_SCOPE_AND_XBRL.md)
- [Regulatory Sources And Versioning](16_REGULATORY_SOURCES_AND_VERSIONING.md)
