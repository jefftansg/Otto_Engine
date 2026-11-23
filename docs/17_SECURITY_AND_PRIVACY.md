# Security and privacy

- Product: Otto Financial Report Engine
- Document version: 1.0
- Last updated: 2026-11-20
- Status: Needs review
- Owner: Engineering
- Related requirements: OTTO-SEC-001, OTTO-SEC-002
- Sources/evidence: START_ON_MAC.command, app.py:31–138, engine/core.py:100–125, engine/importers.py:16–124, PDPC S9

## Purpose and scope

Protect confidential books, director and employee details, bank data and distributed outputs throughout the local workflow and any future commercial service.

## As-is implementation (evidence-backed)

Launcher binds loopback and disables Streamlit usage telemetry. Streamlit session holds package and uploaded bytes, and cached parsing uses the app cache. Restore reads allowlisted filenames in memory, rejects duplicates and caps each accepted member at 5,000,000 bytes. Upload limits live in the importer. Downloaded ZIP, PDF, CSV and XLSX can be opened independently. ZIP contains editable records and source evidence metadata while originals are retained separately. Application-managed encryption, identity, retention and audit history were not observed. First launch can fetch Python dependencies.

## To-be requirements

- Identify purpose, permission/consent where applicable, business contact, access/correction process and controller/processor responsibilities. Minimise director identifiers, avoid credentials and real client records in fixtures, and document notification and transfer requirements.
- Use protected user accounts and approved encrypted disk or volume, encrypt backups and control sharing recipients. Adopt documented retention by record category and legal duty. Delete approved data and expired copies, including downloads, temporary data, caches and backup expiry. Verify recovery periodically.
- Record who accessed or exported each client record in any future hosted workflow. Authorise every document and export request by tenant and role. Define DPO and breach reporting responsibilities and verify applicable PDPA timelines and conditions using authoritative guidance.
- Review ZIP expansion and cumulative limits, parser failures, resource caps, spreadsheet formula injection, output masking, dependency updates and lock/reproducibility practices. Consider signed release artifacts and credential-free offline operation after setup.

## Acceptance criteria / verification

Test malformed, duplicate and oversized ZIPs and malformed uploads without replacing prior data. Verify isolation across two clients and sessions, correct recovery from encrypted backups, retention/deletion controls, formula-safe export and recipient selection. Review network traffic and logs for confidential data.

## Risks, limitations and open questions

Local scope reduces exposure while confidentiality still depends on machine, file access, storage and sharing. Cache lifetime, authorised backup location and legal retention schedule require owner review.

## Related documents

- [System Architecture](03_SYSTEM_ARCHITECTURE.md)
- [Data Model](04_DATA_MODEL.md)
- [Regulatory Sources And Versioning](16_REGULATORY_SOURCES_AND_VERSIONING.md)
- [Test Strategy](18_TEST_STRATEGY.md)

## Planned Otto Auto privacy controls (21 November 2026)

Document-first intake and any external AI processor require explicit data handling design: consent, provider selection, minimisation, per-client isolation, retention/deletion, audit trail, restricted log content and protection against prompt injection in uploaded files. Provider and hosted architecture remain undecided; do not infer current documents are sent externally. See [Otto Auto specification](25_AI_FIRST_AUTO_EXPERIENCE.md).

## Unreleased combined Auto controls

Auto uses local extraction/rules and does not connect an AI provider. Optional external proposal JSON is source/revision validated and needs human approval; the engine does not transmit the request itself. Switching client via new/restore/demo clears staged AI proposals and cached report bundles; uploader keys isolate contexts. Source originals are not embedded in workspaces or committed. Financial export snapshots retain hashes/review metadata and no automatic authorisation. [Verification](29_AUTO_MULTI_BANK_INTEGRATION.md).


### Local clarification workbooks

The client workbook deliberately includes the selected unresolved bank transactions and questions for the user to share manually. No sending connector or cloud processing is invoked. Source files are not embedded. Returned workbooks are matched to the saved workspace/request and validated before explicit reviewer approval; formulas, macros/external links and excessive/corrupt content are rejected. Client responses cannot directly change financial rows or classifications. Request/answer history is retained in the workspace ZIP. See docs/35.
