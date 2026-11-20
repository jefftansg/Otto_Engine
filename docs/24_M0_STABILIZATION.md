# M0 stabilization record — Otto v1.3.1

Date: 20 November 2026 (Singapore). Scope: an engineering baseline for local bookkeeping and draft UFS preparation. This record does not certify UFS, audit exemption, filing compliance or commercial readiness.

## Relationship to the baseline audit

The [M0 baseline audit](milestones/M0_BASELINE_AUDIT_2026-11-20.md) defines the acceptance gates and remains in progress, not signed off. This document supplements its initial evidence with separately requested engineering changes and checks. It does not close professional UFS, independent golden-ledger, Finder/keyboard/mobile or Product-acceptance gates. Newer main-branch professional-partner and audit-handoff documentation is preserved as planned scope, with AGENTS.md's preparation/review/audit boundaries retained.

## Source and release identity

`scripts/build_release.py` builds from committed `HEAD`, not the working directory. Each release contains `SOURCE_MANIFEST.json` with its exact commit, version, file sizes and SHA-256 hashes; a sibling `.zip.sha256` file identifies the archive. The source-only ZIP excludes local environments, untracked files and saved client data. Launcher executable permissions are preserved. Two builds from the same commit are compared for byte identity during release verification. Prior release documentation remains historical evidence.

## Verified local matrix

| Check | Environment / evidence | Result |
| --- | --- | --- |
| Full regression suite | macOS 14.6 arm64, Python 3.9.6, Streamlit 1.50.0; existing installation | 95 passed; 0 failures/errors/skips |
| Clean dependency installation and suite | Temporary copy, newly created .venv, constraints-m0.txt | 95 passed; all installed versions match pins; pip check clean |
| First launcher start | Actual START_ON_MAC.command on isolated port 8513 | Healthy Streamlit endpoint after dependency installation |
| Offline relaunch | PIP_NO_INDEX=1, same environment and dependency fingerprint | Healthy endpoint; no dependency reinstall |
| Busy port | Start a second copy against a live test server | Clear failure before installation; original server stays healthy |
| Immediate restart | Stopped server leaves recently closed connections | Initial preflight failure found and fixed with SO_REUSEADDR; restart and active-listener rejection retested |
| Legacy saved workspace | Fictional sample_company files from commit 838565d in tests/fixtures/workspace-v1.2.4.zip | Restore, tracker initialization and ZIP round-trip preserve all tables and generated accounting results |
| Company-first UI | In-app browser against isolated port 8512; synthetic ACRA fixture | Company selected first; optional PDF accepted; field population requires explicit action |
| UI warning cleanup | Full AppTest suite after width-argument migration | No use_container_width deprecation messages |
| Shell syntax | zsh -n START_ON_MAC.command | Passed |

Dependency pins describe the tested environment. The declared Python range is 3.9–3.12; CI exercises Linux 3.9/3.12 and macOS 3.12. Actual CI outcomes are visible on PR #13 and must not be inferred from local success. There is no claim of a fresh physical Mac/Finder double-click or a network-disconnected computer test; offline testing disabled package-index access after dependencies were installed.

## Open acceptance and known limitations

| Item | Owner | Status / boundary |
| --- | --- | --- |
| Real company/date confirmation and professional UFS review | User/preparer | Manual acceptance remains. Automatic approval review blocked clicking the browser's records/director attestation. Synthetic AppTest covers the form without claiming real verification. |
| Keyboard-only and narrow-screen operation | Otto maintainer / user | Not yet manually verified. Native tabs include readable status text and symbols. |
| Other historical client ZIPs | User/preparer | One baseline synthetic schema fixture is verified; no claim about every historical archive or real client layout. |
| Wider bank layouts and complete UFS disclosures | User/preparer | Existing known limitations remain in the requirements register; draft labels and existing import/report gates remain. |
| Dependency updates and licence/security review | Otto maintainer | Pins are engineering reproducibility evidence, not an independent licence or vulnerability audit. Refresh pins only after rerunning the relevant matrix. |
| Additional services | Product owner | Corporate-secretarial, audit services/automated audit assessment, tax filing and ACRA/XBRL submission remain future scope. |

## Reproduction

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -m unittest discover -s tests -v
zsh -n START_ON_MAC.command
python3 scripts/build_release.py
```

Use a free port for a separate smoke-test session: `OTTO_PORT=8513 ./START_ON_MAC.command`. Save any real workspace ZIP before stopping its running process. The launcher never kills another application.
