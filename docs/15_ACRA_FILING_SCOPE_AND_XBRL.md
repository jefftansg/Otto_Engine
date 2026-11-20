# ACRA filing scope and XBRL

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Needs review
- Owner: Compliance
- Related requirements: OTTO-COMP-003
- Sources/evidence: ACRA Filing requirements and exemptions, October 2026 taxonomy section

## Purpose and scope

Describe preparation handoff and external filing classifications.

## As-is implementation (evidence-backed)

Otto creates PDFs and XLSX workpapers. No Bizfile, XBRL export, taxonomy validation or submission path was observed.

## To-be requirements

| Case | ACRA guidance |
| --- | --- |
| Dormant relevant company | Preparation and filing relief when all s201A conditions apply. Review dormancy, listing/subsidiary exclusions and applicable SGD 500,000 asset test. |
| Solvent exempt private company | Filing relief with optional voluntary filing. Establish EPC status under the Act and solvency. ACRA states the annual return includes a solvency declaration. |
| Smaller and non-publicly accountable required filer | Simplified XBRL plus authorised PDF. Current FY revenue and assets each ≤ SGD 500,000 with ACRA definitions, consolidation and translation provisions. |
| Applicable banking, finance or insurance company | Relevant XBRL FSH variant plus authorised PDF. |
| Company limited by guarantee or authorised alternative standards | Authorised PDF in ACRA's listed classes. Check approval scope. |
| Other required filer | Full XBRL subject to applicable classification, exceptions and approval. |

Record company classification, that year's applicable taxonomy (ACRA Taxonomy 2026 from 19 October 2026 per filing guidance), authorised financial statement reference and handoff to appointed filer. Taxonomy definitions, filing validation/business rules and copyright/licensing require separate review prior to software reuse. Annual returns, XBRL preparation/submission, IRAS and GST are outside Otto's service.

## Acceptance criteria / verification

Review a solvent EPC, a dormant relevant company, a smaller required filer and a full XBRL class. Ensure audit exemption does not determine the filing path and draft exports are labelled as preparation documents.

## Risks, limitations and open questions

Special filing classes, alternative standards, regulated entities, shareholder limits and statutory declaration details need current authority and reviewer evidence.

## Related documents

- [Ufs Preparation And Disclosures](11_UFS_PREPARATION_AND_DISCLOSURES.md)
- [Singapore Compliance](12_SINGAPORE_COMPLIANCE.md)
- [Audit Exemption Eligibility](13_AUDIT_EXEMPTION_ELIGIBILITY.md)
- [Regulatory Sources And Versioning](16_REGULATORY_SOURCES_AND_VERSIONING.md)
