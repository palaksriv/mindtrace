# Changelog - publication-readiness release

## Security and governance
* Counsellor self-registration now requires an invite code (`MINDTRACE_COUNSELLOR_INVITE_CODE`); empty disables it.
* `/api/admin/wipe` is disabled unless `MINDTRACE_ALLOW_DATA_WIPE=true`, and it now also clears reviews and consent records.
* **Server-side consent record** (`consent_records`, versioned notice). Telemetry is rejected without a granted record, and after a session is completed. The front end posts the record when a session starts.
* Front end pins the MediaPipe WASM runtime (1.0.1) and uses the versioned model path instead of `@latest`.

## Analytics
* All weights and thresholds moved into an immutable `AnalyticsConfig` so they can be calibrated and tested.
* `data_quality` block (status `ok`/`sparse`/`no_telemetry`, duration, effective sampling rate).
* Sessions with no telemetry now report level `UNAVAILABLE` with an explicit signal, instead of `LOW`; sparse sessions get a caution signal and a counsellor-overview cue.
* `blink_rate_per_minute` computed from timestamps; `center_both_percent` (previously expected by the UI but never produced).

## Research tooling
* `app/services/psychometrics.py`: Cronbach's alpha, Spearman-Brown, Pearson, test-retest, bootstrap CI.
* `scripts/export_pilot_data.py`: pseudonymised, consent-filtered CSV export.
* `scripts/reliability_report.py`: per-trait alpha, Spearman-Brown, test-retest and convergent validity (BFI-10).
* `scripts/purge_telemetry.py`: retention enforcement (`--dry-run` supported).
* `docs/PILOT_PROTOCOL.md`, `docs/ETHICS_AND_PRIVACY.md`.

## Tests
* 6 -> 52 automated tests (analytics rules and formula, straight-lining property, consent gating, access control, counsellor workflow, registration security, retention, psychometrics, export pipeline).
* Tests now run on a throw-away SQLite database; `pytest.ini` added.
* A mutation check (removing the consent gate) is caught by the suite.

## Housekeeping
* `requirements-reference.txt` documents the optional `mediapipe` dependency of the unused server-side reference detector.

## Not changed / not verified
* Front-end changes type-check and build, but have **not** been exercised in a live browser with a webcam.
* No human-participant data exist yet; reliability and calibration require the pilot.
