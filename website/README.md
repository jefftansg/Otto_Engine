# Otto marketing website

A responsive static marketing/preview website for the Otto Financial Report Engine.

## Run locally

From the repository root:

```bash
python3 -m http.server 8000
```

Open **http://localhost:8000/website/**. The page loads the approved logo and mascot from `../assets/` and uses no paid APIs, account system or tracker.

## Publishing

The site is a static three-file HTML/CSS/JS application. For a production static host, copy `website/index.html`, `website/styles.css`, `website/script.js` to the host root; create an `assets/` directory containing `assets/otto_icon.png` and `assets/otto_mascot.png` from the repository and change the three HTML relative paths from `../assets/` to `assets/`. Alternatively configure GitHub Pages to publish from the repository root and visit the `/website/` route. **No deployment or DNS is configured by this PR.**

## Positioning and scope

- Development-stage product; M0 stabilisation in progress.
- Present current Guided/Advanced workspaces, text-based PDF/CSV/Excel intake, single SGD bank ledger, clarification and draft Management Accounts/UFS; do not claim a certified, launched accounting system.
- Clearly distinguish planned multi-bank support, audited-exemption assessment, external accountant review and client-authorised audit-ready export.
- Separate contracted accountant preparation review from a formal assurance/compilation engagement and independent statutory audit.
- Corporate tax/GST, IRAS, ACRA/XBRL filing, audit reports and professional certifications are out of scope.
- No invented prices, client logos, testimonials, contact email, registrations or live portal links.

The embedded workflow illustration is fictional and marked as such.

## Pre-launch checklist

- Confirm approved website domain and official contact channel; add privacy notice before any lead-capture form.
- Check branding/SEO and accessibility on iPhone, Android, Chrome, Safari and keyboard-only.
- Confirm service availability, engagement terms, pricing and professional involvement before converting development-preview language into commercial promises.
- Verify Singapore regulatory copy on each legal/compliance update and maintain alignment with `docs/19_DEVELOPMENT_ROADMAP.md`.
