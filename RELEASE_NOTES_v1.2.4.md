# Otto Financial Report Engine — v1.2.4

## Changes from v1.2.3

- Product renamed **Otto Financial Report Engine** in the Mac app and browser tab.
- Added the exact original user-provided Otto logo (`assets/otto_original_logo.png`) to the application bundle.
- Derived sidebar wordmark, application mascot image and browser favicon from the original artwork without redrawing the brand.
- Applied Otto typography/color accents to the interface; Guided Mode is still the default.
- Changed the saved company workspace download to `Otto_Client_Workspace.zip` (existing v1.2.3 saved client ZIPs remain compatible).
- Updated PDF report footers and clarification questionnaire footer to identify Otto.
- Updated README and Quick Start.

## Unchanged functionality

The deterministic accounting core, ACRA document extraction, bank balance validation, invoice/claim processing, contextual questions, Guided/Advanced Mode navigation, source provenance and report generation remain as in v1.2.3.

## Verification and limits

- The 48 existing tests must continue to pass; branding checks added for image assets and product titles.
- Code syntax and ZIP integrity should be verified before release.
- Mac browser appearance must still be verified on the user's Mac; backend automated tests cannot guarantee UI rendering.
- Statements are draft outputs requiring professional review; no government certification is implied.
- The PDF/XLSX working papers remain accounting documents. Otto branding does not assert that the underlying figures or compliance were certified.
