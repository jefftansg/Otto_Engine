# Auto progress, setup acknowledgement and upload removal

22 November 2026. Unreleased follow-up on PR #21. Version remains 1.3.1; no merge or professional/template authorisation.

The Auto sidebar now places a compact **Progress · n/5 stages** panel between the engine version and upload drop box. It shows completed/current/pending markers, **Now**, **Next**, and expandable **Stage details**. The sidebar scrolls independently of the main review page, so users can keep progress and uploads visible while reviewing long inventories. This is preparation progress, not financial approval.

1. **Upload documents**: source uploads are present in this session.
2. **Confirm company**: company name, UEN and valid reporting dates are explicitly confirmed.
3. **Review bank accounts**: current originals match approved identities, coverage and balances for every registered account. Legacy single-account balance checks are retained.
4. **Reconcile records**: the bank-source checks pass and the deterministic ledger has no blocking errors. Remaining disclosure/checklist review is still handled through the exception list.
5. **Generate draft reports**: a package exists for the current frozen report revision. It remains provisional/draft, subject to its outstanding issues and template approval.

Removing a source or changing records can roll progress back. ZIP restoration preserves accounting and review history but does not restore original PDFs; originals must be re-uploaded for current-source clearance. A stale report package never clears the final stage.

**Confirm setup** now displays a persistent company/date confirmation plus a saved toast. For a blank bank-upload workspace, it automatically opens account review by creating an empty account registry only. It does not approve accounts, import transactions or create opening journals. Reconfirming unchanged legacy setup preserves its balance confirmation; changed identity/dates require recheck. Existing populated books still reject a UEN change.

Below the upload drop box, expand **Remove uploaded files**, choose **Select uploaded files to remove**, then click **Remove selected uploads**. Same-named files are distinguished by source identity. This removes session uploads; originals on disk, recorded accounting rows, evidence and account approval history remain. Removed sources cannot silently reappear from the old uploader selection. The last-file removal acknowledgement stays visible. Cached report bundles and AI suggestions are cleared, and missing current sources require review again. The controls are available before company setup and the initial account gate.

## Validation

Pinned local environment: macOS arm64, Python 3.9.6. `PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v`: **196 tests passed, no skips** (189 existing plus seven new). `tests/test_auto_progress.py` covers read-only stage calculation, reviewed-account reconciliation, current bundle completion, missing-source/broken-ledger rollback, actual setup submission and automatic transition without posting, rejected unverified/missing identity, sidebar removal before setup, last-file acknowledgement, same-name source isolation, preservation of accounting/history, cached proposal invalidation and unchanged legacy confirmation.

An isolated empty-client browser preview checks sidebar placement and visibility. Financial attestations and removal actions are tested only with synthetic AppTest fixtures. No user session, client source, posted record, release version, accounting rule, dependency or regulatory determination is changed by this UI work.
