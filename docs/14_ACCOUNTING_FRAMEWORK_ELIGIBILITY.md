# Accounting framework eligibility

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Needs review
- Owner: Compliance
- Related requirements: OTTO-COMP-002, OTTO-UFS-001
- Sources/evidence: ACRA Guide to accounting standards; ASC edition announcement; authoritative statement text access pending

## Purpose and scope

Choose and document the prescribed framework for the period and entity.

## As-is implementation (evidence-backed)

`core.generate` accepts the labels FRS and SFRS for Small Entities, with a manual eligibility flag. SFRS(I), edition control, effective-date selection and evidence-dependent tests are absent.

## To-be requirements

1. Identify entity type, listing or regulation and whether it has public accountability. For company statutory statements check the applicable ASC statement of applicability and prescribed standards. For sole proprietors default to scoped management reporting.
2. Establish whether SFRS(I) is required or elected where permitted, or FRS applies with any permitted choices and transition requirements. Check group reporting needs separately.
3. For SFRS for Small Entities verify the current ASC statement of applicability, lack of public accountability, general-purpose external financial statements and applicable size, history and group rules. The commonly used size baseline is two of revenue ≤ SGD 10m, assets ≤ SGD 10m and employees ≤ 50, subject to the adopted edition and transitional requirements. Obtain the source text before automating the eligibility conclusion. A small-company audit outcome supplies no framework decision.
4. Consider amended FRS 119 as an optional reduced-disclosure standard for eligible entities reporting under FRSs. Check the subsidiary route (no public accountability and qualifying parent consolidated financial statements publicly available) and the additional small-entity route (no public accountability and edition-specific size criteria). ACRA confirms early application is permitted for amended FRS 119. See S10 in the source register.

| Period begins | Standards version decision |
| --- | --- |
| 2026 or earlier | Use the applicable ASC collection for the period. For small entities use the then-applicable edition unless permitted early application is documented. |
| 1 January 2027 or later | ASC announcement specifies third edition SFRS for Small Entities and amended FRS 119 for annual reporting periods starting from this date. Confirm transition, options and specific applicability. |
| Transition or early application | Record authoritative permission and approval. Preserve comparative reconciliation and old/new mapping versions. |

## Acceptance criteria / verification

Use separately reviewed fictional cases with start dates 31 December 2026 and 1 January 2027. Show both the applied edition and reasoning. Include an audit-exempt entity with public accountability or other independently failing framework criterion and unresolved evidence case. Unsupported framework remains blocked for authorisation.

## Risks, limitations and open questions

The ASC detailed standards landing page returned HTTP 403. Exact permitted early application, group/period criteria and cross-framework transition require authoritative verification.

## Related documents

- [Ufs Preparation And Disclosures](11_UFS_PREPARATION_AND_DISCLOSURES.md)
- [Singapore Compliance](12_SINGAPORE_COMPLIANCE.md)
- [Audit Exemption Eligibility](13_AUDIT_EXEMPTION_ELIGIBILITY.md)
- [Regulatory Sources And Versioning](16_REGULATORY_SOURCES_AND_VERSIONING.md)
