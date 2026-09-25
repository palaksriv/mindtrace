# Ethics and privacy notes

This document summarises how MindTrace handles data and what still needs institutional decisions. It is engineering documentation, **not legal advice**; confirm obligations (for example under India's Digital Personal Data Protection Act, 2023) with your institution's data-protection officer.

## Data inventory

| Data | Where produced | Stored? | Notes |
|------|----------------|---------|-------|
| Raw webcam frames | Browser | **Never** | Converted to landmarks in the browser (WebAssembly) and discarded |
| Derived telemetry (face found, EAR, blink flag, gaze proxy, head angles) | Browser | Yes, `behavior_telemetry` | One row about every 500 ms; deleted by the retention job |
| Questionnaire answers + display/answer timestamps | Browser | Yes, `responses` | Latency derived server-side |
| Consent record (granted, notice version, timestamp) | Browser -> API | Yes, `consent_records` | Telemetry is rejected (HTTP 403) without a granted record |
| Account data (name, e-mail, Argon2 hash, role) | Registration | Yes, `users` | |
| Counsellor review (status, notes) | Counsellor | Yes, `counsellor_reviews` | |

## Safeguards implemented

* On-device inference; only derived numbers leave the browser.
* Explicit consent checkbox **and** a server-side consent record; the API refuses telemetry otherwise, refuses telemetry after completion, and refuses cross-student writes.
* Role-based access; counsellor accounts require an invite code (`MINDTRACE_COUNSELLOR_INVITE_CODE`); the destructive wipe endpoint is disabled unless `MINDTRACE_ALLOW_DATA_WIPE=true`.
* Argon2 password hashing, expiring JWTs, generic login errors.
* Research exports are pseudonymised (salted HMAC), consent-filtered and contain no names or e-mails.
* Retention tooling: `python -m scripts.purge_telemetry --older-than-days N`.
* Non-diagnostic framing in every report; missing data is shown as `UNAVAILABLE`, never as a calm session.

## Known limitations (be transparent about these)

* Gaze and head pose in the browser are geometric proxies for head orientation, not calibrated estimates.
* Fairness across skin tone, glasses, head coverings, disability and neurodivergence has **not** been evaluated (pilot RQ6).
* SQLite, a single shared HS256 secret and no rate limiting are prototype-grade; use institutional identity, a managed database, secret rotation and audit logging for any real deployment.
* Counsellors can currently view every student's completed sessions; scope this to an assigned caseload before deployment.
* The landmark model and WASM runtime are fetched from public CDNs at run time (now version-pinned). Self-host them if the network path itself is a privacy concern.
* Retention periods and notice wording are placeholders that your institution must set.
