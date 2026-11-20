# Otto Financial Report Engine — v1.3.0

20 November 2026. Prepared for review in PR #13; this file does not indicate a published GitHub Release or deployment.

## Changes from v1.2.4

- Prominent **Engine version 1.3.0** badge under the product title, repeated in the sidebar. Mac launcher and current documentation use the same version.
- Review duplicate uploads and documents of uncertain relevance, then retain or delete selected files. No automatic deletion. Preserve saved transactions, company information and evidence; require bank balances to be checked again after statement removal.
- Five native tabs with green/Cleared, amber/Needs attention and grey/Not started labels, including symbols and status text. Issue actions and Continue controls open their destination tab.
- Complete issue list with reasons, next actions, Open/In progress notes, automatic clearance, cleared history and reopening of recurring issues. Save history in the workspace ZIP or export CSV. Missing source documents leave historical bank-source issues in Needs recheck.
- List individual clarification questions without the previous extraction/uncategorised caps, and show every grouped validation detail.
- Reserve a separate top strip for Streamlit developer controls so they do not overlap the Otto logo.

## Compatibility and verification

- Requires Streamlit 1.50 or later. The Mac launcher installs changed requirements automatically.
- Older workspace ZIPs remain readable; the optional issue register is initialized on first Guided use. Original source documents are still not included in saved ZIPs. Retention choices remain session-only.
- Posting, rounding, reconciliation and existing report-download rules are unchanged. Stage colours, issue notes and questionnaire answers are not accounting approval or professional certification.
- Validation: 86 tests passed, 0 failures, 0 errors, 0 skips on macOS arm64 / Python 3.9.6 / Streamlit 1.50.0 using `python -m unittest discover -s tests -v`.
- Local browser checks cover native tabs, issue routing, status colours, header clearance and version visibility. Keyboard-only, narrow-screen and every historical release archive remain unverified. Existing Streamlit width-deprecation warnings remain.

See [Quick Start](QUICK_START_v1.3.0.md) and [test strategy](docs/18_TEST_STRATEGY.md). The original [v1.2.4 release note](RELEASE_NOTES_v1.2.4.md) remains available as history.
