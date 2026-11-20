# Otto Financial Report Engine — v1.3.1

20 November 2026. Prepared for review in PR #13; this file does not indicate a deployed release.

## Changes from v1.3.0

- Company is now the first/default tab: **Company → Documents → Bank → Other records → Reports**.
- Begin with manual company identity and financial-year setup, or upload an optional ACRA Business Profile directly under Company. Extracted details are applied only by an explicit user action; financial-year dates must still be confirmed.
- Keep company setup above the issue tracker, then continue to general accounting documents. Company clears when its name, UEN and dates are confirmed; further UFS information remains tracked in the issue list.
- Reorder navigation, colours, sidebar instructions, company issue routes and missing-source recheck routes consistently. Documents retain all file review/delete controls.
- Focus current services on **bookkeeping and draft unaudited financial statement (UFS) preparation for SMEs**. Corporate-secretarial workflows, audit services/automated audit-exemption assessment, tax filing and ACRA/XBRL submission remain future scope. The optional ACRA audit-exemption link is informational, with no new assessment workflow.
- Display **Engine version 1.3.1** prominently in the app and sidebar; update launcher, current Quick Start and documentation. Preserve prior release notes.

## M0 stabilization

- Check runtime, source files and port availability before installing dependencies. Give a clear recovery message on port conflict, keep existing sessions running, and support an explicit `OTTO_PORT` for separate sessions. Permit immediate restart while old connections finish closing.
- Pin the verified dependency graph in `constraints-m0.txt`, include constraints in the install fingerprint, check environment consistency and preserve cached/offline launches. Declared Python range: 3.9–3.12.
- Replace deprecated Streamlit width arguments; repeated width-deprecation messages no longer fill Terminal.
- Extend CI to Linux/Python 3.9 and 3.12, and macOS/Python 3.12. Individual CI outcomes are available in the PR checks; local results do not certify unrun platforms.
- Add a legacy v1.2.4 synthetic workspace fixture and reproducible committed-source ZIP packaging with per-file SHA-256 inventory and archive checksum sidecar.

## Compatibility and verification

Existing accounting, import approval, reconciliation, issue history, ZIP restore and report-download rules remain. Company confirmation or an upload does not post a transaction. No framework, audit or filing eligibility is inferred from SME status.

Local verification: **95 passing tests**, zero failures/errors/skips on macOS 14.6 arm64 / Python 3.9.6 / Streamlit 1.50.0, including a clean installation. Fresh launch, offline relaunch, exact pinned versions, occupied-port refusal and legacy workspace/report preservation passed. Additional validation is recorded in the [test strategy](docs/18_TEST_STRATEGY.md). [Quick Start](QUICK_START_v1.3.1.md) describes the current sequence; [v1.3.0 release notes](RELEASE_NOTES_v1.3.0.md) remain available as history.
