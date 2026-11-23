# Direct client replies and per-query dropdowns

23 November 2026. Candidate **1.4.0-dev.6**, adding direct entry alongside the Excel exchange. No final release or professional/template approval.

## Direct-entry workflow

In Auto, open **Enter client replies directly in Otto** near Review exceptions. Every pending transaction has a **Reply category** dropdown and other open questions have **Reply option**. Choose a listed response, or **Other / type manually** and enter a **Custom category / reply** or **Client explanation**. Optional fields record documents and who answered. **Reply status** retains incomplete replies as Need more information. Enter **Replies recorded by** and click **Save client replies**. No Excel workbook is required.

Transaction reply choices include Sale, Business expense, Bank charges, Office / rent, Marketing, Software subscriptions, Professional fees, Loan, Owner funding, Refund, Transfer between own accounts, Not sure and Other / type manually. Needs reply is the unanswered placeholder. General questions offer Yes, No, Not sure, Not applicable and Other / type manually; questions asking for names or explanations cannot be answered merely Yes/No.

Replies are prefilled for editing while their query remains pending. Direct and Excel replies share answer storage, prior-answer history and workspace ZIP restoration. A saved-reply toast and last-save summary acknowledge success. General answers use the existing clarification statuses; Not sure/unknown replies and Need more information remain open. Blank entries do not clear questions.

## Accounting boundaries

A reply records facts, not a posting. Clear supported labels can propose existing categories: Sale -> Sales and services revenue, Bank charges -> Bank charges, Office / rent -> Office and rental expense, Marketing -> Advertising and marketing, Software subscriptions -> Software subscriptions, Professional fees -> Professional fees. The operator must still click **Approve and save reviewed categories**. Existing approved codes are preserved until the operator explicitly changes them.

Replies take priority over older rule/AI suggestions. Ambiguous loans, owner funding, refunds, transfers, uncertain answers and custom text do not guess a financial account. Existing transfer-pair approval remains required. A custom category records the client's wording; it does not create a chart-of-accounts entry. Saving replies does not change bank amounts/dates, journals, evidence or balances, and does not bypass missing documents, coverage or reconciliation checks. Transaction issues clear when their accounting classification is approved, not merely when a client answer is received.

`engine/client_replies.py` validates the query/source/previous-answer revision, recorder and permitted choices, then atomically records changes and prior answers. Stale, unknown, repeated and invalid queries reject without mutation. `clarification_ui.py` provides the editable query grids without adding extra navigation tabs. `auto.py` shows saved replies and source-labelled category proposals. Excel choices use a hidden list range; old workbook layouts remain readable. Uncertain Excel answers also remain Needs answer.

## Validation

Eight new synthetic tests in `tests/test_direct_replies.py` cover category-only replies without financial mutation, free-text edits/history/ZIP restoration, general-question resolution and uncertain replies remaining open, stale/invalid/missing-recorder/duplicate rejection, direct/Excel conflicts and repeat exports, ambiguous category/transfer preservation, actual direct-grid save and acknowledgement, priority over an older AI suggestion, and a separate category approval before ledger codes change. Existing five-stage Guided navigation remains unchanged.

Full local suite: **236 tests passed, no skips**, macOS arm64/Python 3.9.6. Exact-head CI is recorded in the PR. No runtime dependency, report renderer/template or financial arithmetic changes. No private client material, workbook or screenshot is committed; UI actions use synthetic fixtures only.
