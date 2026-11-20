# Release notes

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Verified
- Owner: Engineering
- Related requirements: OTTO-BASE-001, OTTO-QA-001
- Sources/evidence: RELEASE_NOTES_v1.2.4.md, docs/previous_releases/, START_ON_MAC.command, app.py, assets/, tests/

## Purpose and scope

Record what the supplied release verifies and what shipped historical notes report.

## As-is implementation (evidence-backed)

Launcher and current release notes identify v1.2.4. Source confirms Otto page title, PNG branding assets, default Guided path, Otto ZIP download name and branded PDF code. README and [release note](../RELEASE_NOTES_v1.2.4.md) describe the branding release as based on v1.2.3. Independent historical source trees were unavailable, so the stated change history is attributed to the bundled notes.

| Release | Archive record and described focus |
| --- | --- |
| v1.1 | [Release note](previous_releases/RELEASE_NOTES_v1.1.md) for guided intake and multi-format uploads. |
| v1.2 | [Release note](previous_releases/RELEASE_NOTES_v1.2.md) for smart intake. |
| v1.2.1 | [Release note](previous_releases/RELEASE_NOTES_v1.2.1.md) for Guided Mode. |
| v1.2.2 | [Release note](previous_releases/RELEASE_NOTES_v1.2.2.md) for clarification questions. |
| v1.2.3 | [Release note](previous_releases/RELEASE_NOTES_v1.2.3.md) for attention routing and checks. |
| v1.2.4 | [Release note](../RELEASE_NOTES_v1.2.4.md) and current inspected source for branding and local drafts. |

## To-be requirements

Release update template: version/date, supported platform, scope and associated requirements, verified user-visible changes, migration/restore implications, exact verification commands/results, known gaps, authority version impacts, archive digest and reviewer approvals.

## Acceptance criteria / verification

Current unittest run recorded 52 passed. Reproduce with the command in the test strategy and verify ZIP integrity and Mac behaviour separately. Attribute historical claims to their notes unless historical artifacts are available.

## Risks, limitations and open questions

Historical test counts and differences cannot be replayed from the supplied ZIP alone. Live Mac render and older ZIP compatibility need dedicated evidence.

## Related documents

- [System Architecture](03_SYSTEM_ARCHITECTURE.md)
- [Test Strategy](18_TEST_STRATEGY.md)
- [Development Roadmap](19_DEVELOPMENT_ROADMAP.md)
- [Decision Log](22_DECISION_LOG.md)
