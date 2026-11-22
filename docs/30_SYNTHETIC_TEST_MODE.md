# Synthetic Test Mode for Otto Auto (development candidate)

Date: 2026-11-22. Status: code candidate, **not released or approved for clients**.
Scope: local fixture extraction/reconciliation tests only. Does not change ACRA or bank authenticity requirements for production.

## Why the previous pack was blocked
Otto Auto deliberately excludes sources with the words `fictional`, `synthetic`, `demonstration` or `demo` from real bank coverage. The Otto v3 test PDFs correctly identify themselves as synthetic. They also name a fictional `OTTO QA TEST FINANCIAL INSTITUTION`, which the normal bank detector does not recognise. Renaming PDFs or removing disclaimers is **not** an acceptable solution.

## Test procedure

1. Run the **fix/synthetic-fixture-test-mode** branch locally, separately from your production client workspace. This depends on the unmerged **development/multi-bank-sgd** branch.
2. Click **Start a new company**. Before entering any real client data, expand **Developer testing — use fictional sample documents** in the sidebar and choose **Enable Synthetic Test Mode**.
3. The sidebar and Auto page must show a persistent **SYNTHETIC TEST MODE** warning.
4. Upload the original labelled company profile and 12 monthly statement PDFs from `Otto_Parser_Compatible_Demo_Test_Pack_v3.zip`. Do **not** remove or alter their synthetic markings.
5. Confirm company, UEN and FY; review the proposed account groups, exact coverage and transaction rows. Test-only confirmations verify fixture consistency, not real bank evidence.
6. Check the extracted totals against the supplied independent control workbook. Any unsupported layout, duplicate, mismatch or missing accounting entry should still raise an exception.
7. Download provisional reports. PDFs must show **SYNTHETIC TEST ONLY / NOT FOR CLIENT USE**; Excel contains a **SYNTHETIC TEST ONLY** worksheet. Neither is a director-approved or client-ready statement.
8. Start a completely separate blank company to work with genuine client documents. There is no in-place switch from synthetic to live mode.

## Controls / exclusions

- Normal mode still rejects fictional/demo bank evidence.
- Test mode accepts **only clearly labelled** synthetic bank and profile fixtures; unmarked bank/profile sources must not silently mix into a test workspace.
- The fictional Otto QA institution is recognised **only** for test-mode parsing; it is never represented as DBS, OCBC, UOB or a genuine financial institution.
- Workspaces persist the test flag. Changing identity or test flag invalidates previous analysis/approval revisions.
- Synthetic group/account reviews carry their test status, and synthetic evidence is labelled, not "Reviewed" as an authentic bank statement.
- A synthetic report can never become marked ready/authorised as a genuine report.
- Full accounting and professional compliance gates remain unchanged, with separate unresolved QA.
- No guarantee that every PDF table can be mapped; manual review may still be necessary.
- Real ACRA Business Profiles, genuine bank evidence, actual signed accounts and filings are **never** replaced by fixture documents.

## Proposed acceptance cases (not yet claimed passed)

`tests/test_synthetic_fixture_mode.py` verifies normal-mode rejection, explicit opt-in, synthetic bank coverage and proposal mapping, unmarked-source exclusion, source-revision invalidation, fictional institution detection, ZIP persistence, provisional report labels, PDF signature and Excel test worksheet.

Run:
```bash
python -m unittest tests/test_synthetic_fixture_mode.py -v
python -m unittest discover -s tests -v
```

Then perform local Mac/browser testing with the **actual v3 PDF pack**, plus a full numerical/reconciliation and visual output audit before offering any release.
