# Audit exemption eligibility

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Needs review
- Owner: Compliance
- Related requirements: OTTO-COMP-001
- Sources/evidence: ACRA Audit exemptions and February 2026 public consultation; SSO primary text access pending

## Purpose and scope

Specify a reviewable assessment for s205C and the Thirteenth Schedule with three outcomes.

## As-is implementation (evidence-backed)

The application warns that audit exemption requires review. It lacks group, headcount, historical criteria and decision fields.

## To-be requirements

Each assessed year passes the size test if at least two criteria are met: revenue ≤ SGD 10 million, assets ≤ SGD 10 million, and full-time employees at financial year end ≤ 50. Use standards-based annual figures. Record the year-end, evidence source, raw values and measurement basis. Determine private-company status throughout the relevant current year and assess the group separately including foreign members using consolidated figures and the applicable headcount. Group membership follows accounting standards. Consolidation filing relief alone does not remove this assessment.

| Condition | Assessment |
| --- | --- |
| Current-year private status fails | Not eligible under s205C. Check separate dormancy route if relevant. |
| First FY of newly incorporated company | Use first-year size results. |
| Second FY, first year did not qualify | Apply size test to second year. |
| Second FY, first year qualified | Apply continuity provisions and confirm private status. |
| Established, entering qualification | Apply the test to each of the two financial years immediately preceding the current FY. |
| Previously qualified | Continue unless private status ceases during current FY or both immediately preceding years fail the size test. Group continuity is separately assessed. |
| Part of group | Company and small group must qualify. Verify first-year consolidation or change of group using Schedule paras 7–9 and group perimeter under para 12(a). |
| Material evidence absent | Requires verification if outcome cannot be determined from known facts. Ask for missing headcount, consolidated FS or dates. |
| Substantiated pass on applicable tests | Eligible subject to review of applicable statutory provisions and notices requiring audit. |

Dormant-company audit relief under s205B is assessed separately and can apply to companies other than private companies. Assess s201A preparation relief and filing independently. Retain any shareholder audit request for legal review. Indexed SSO text for s205B(6), applied by s205C(2), shows a route for qualifying members at the 5% threshold (issued shares, a class of shares, or membership, with statutory exclusions) by written notice during the FY and at least one month before year-end. Review the full provisions and Registrar powers before concluding. Capture decision, preparer, reviewer, date, authority version, and cited statements/declarations. Apply current rules for periods starting on or after 1 July 2015 according to ACRA guidance. The February 2026 review proposes exploring higher financial thresholds and subsidiary relief. No enactment was verified in the reviewed material.

## Acceptance criteria / verification

Fictional examples: newly incorporated Bright Sample Pte. Ltd. has SGD 10 million revenue, SGD 9 million assets and 55 employees, so first-year size passes exactly two. If first year fails and second year has the same passing numbers, reassess second year. In an established entrant case, two passing prior years qualify and a prior year with one passing criterion fails entry. A subsidiary with passing individual numbers and an established group failing applicable tests is Not eligible. If only revenue passes, assets fail and employees are unknown, mark Requires verification. A qualified company may withstand one failing prior year but loses status on two consecutive failures or loss of private status. Verify precise group transitions with primary text.

## Risks, limitations and open questions

ACRA guidance supports the headline and transition logic. Verify Schedule wording, group reorganisation cases, applicable headcount definition/timing and shareholder requests before implementing rules or determining actual eligibility.

## Related documents

- [Singapore Compliance](12_SINGAPORE_COMPLIANCE.md)
- [Accounting Framework Eligibility](14_ACCOUNTING_FRAMEWORK_ELIGIBILITY.md)
- [Regulatory Sources And Versioning](16_REGULATORY_SOURCES_AND_VERSIONING.md)
- [Test Strategy](18_TEST_STRATEGY.md)
