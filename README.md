# MindTrace

**Multimodal Behavioral Analytics for Psychometric Student Counselling**

MindTrace is a final-year Computer Science project that combines **psychometric assessment** with **observable computer-vision-based behavioural telemetry** to provide counsellors with a broader view of student assessment sessions.

The system presents self-reported personality-related assessment results alongside non-diagnostic behavioural signals such as facial presence, eye aspect ratio, blinking, gaze direction (a head-orientation proxy in the browser client), and head movement.

> **Important:** MindTrace is an academic decision-support prototype. Its behavioural analytics are observational and non-diagnostic. They must not be used to diagnose mental-health conditions or infer a student's true emotional or psychological state.

---

## Features

### Student

- Student registration and secure JWT authentication
- Student portal
- Psychometric assessment interface
- 20-item Big Five-style assessment
- 1–5 Likert-scale responses
- Automatic assessment scoring
- Assessment session tracking
- Webcam-based behavioural telemetry during assessment
- Student results page
- Assessment history

### Counsellor

- Secure counsellor authentication
- Counsellor dashboard
- Student assessment history
- Completed assessment reports
- Psychometric trait scores
- Behavioural analytics
- Session timing information
- CV sample statistics
- Protected test-data cleanup

### Computer Vision

During an assessment, the system processes webcam frames to extract observable behavioural signals.

The CV pipeline includes:

- Face detection
- Facial landmark detection
- Face presence tracking
- Eye Aspect Ratio (EAR)
- Blink detection
- Horizontal gaze estimation
- Vertical gaze estimation
- Head yaw
- Head pitch
- Head roll
- Movement analysis
- Behavioural deviation analysis

Raw webcam video is not stored.

Browser-side landmark analysis keeps raw webcam frames on the student's device.
Only derived, non-diagnostic telemetry is sent to the API.

## Research-readiness features

* Server-side, versioned **consent records**; the API rejects telemetry without a granted record.
* Counsellor accounts require an **invite code**; data wipe is **off by default**.
* Analytics thresholds live in `AnalyticsConfig` (uncalibrated design choices - see `docs/PILOT_PROTOCOL.md`).
* Missing camera data is reported as `UNAVAILABLE`, not as a calm session.
* Pilot-study tooling: pseudonymised export, reliability report (alpha, test-retest, BFI-10 agreement), retention purge.
* 52 automated tests: `cd backend && pytest`.

See `docs/ETHICS_AND_PRIVACY.md` for the data inventory and known limitations, and `docs/CHANGELOG.md` for what changed.

## Run locally

### Prerequisites

- Python 3.12
- Node.js 20 or newer

### 1. Configure the environment

```bash
cp .env.example .env
```

Set `MINDTRACE_JWT_SECRET` in `.env` to a unique value with at least 32 characters. To allow counsellor self-registration set `MINDTRACE_COUNSELLOR_INVITE_CODE`; otherwise create counsellors with the seed script.

### 2. Start the backend

```bash
cd backend
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

### 3. Seed demo accounts (optional)

In another terminal:

```bash
cd backend
.venv/bin/python -m scripts.seed_demo_users
```

- Student: `student@example.com` / `StudentDemo2026!`
- Counsellor: `counsellor@example.com` / `CounsellorDemo2026!`

These credentials are for local demonstration only.

### Run the tests and the pilot tooling

```bash
cd backend
.venv/bin/python -m pytest                       # 52 tests, throw-away database
export MINDTRACE_EXPORT_SALT="<random secret>"
.venv/bin/python -m scripts.export_pilot_data --out exports
.venv/bin/python -m scripts.reliability_report --items exports/item_responses.csv --sessions exports/session_summary.csv
.venv/bin/python -m scripts.purge_telemetry --older-than-days 30 --dry-run
```

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

The first time webcam analysis is enabled, the browser downloads the MediaPipe model. An internet connection is required for that initial download.

## Ethical use

MindTrace is an academic counselling decision-support prototype. It must not be used to diagnose mental-health conditions, infer emotion, make automated student-risk decisions, or replace a qualified counsellor's judgment.

---

## System Architecture

```text
                    ┌──────────────────────┐
                    │      Student         │
                    │   /   Counsellor     │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ React + TypeScript   │
                    │       + Vite         │
                    └──────────┬───────────┘
                               │
                         REST API / JSON
                               │
                               ▼
                    ┌──────────────────────┐
                    │       FastAPI        │
                    │      Backend         │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        ┌──────────┐    ┌────────────┐   ┌─────────────┐
        │ Auth &   │    │ Assessment │   │ Computer    │
        │ RBAC     │    │ & Scoring  │   │ Vision      │
        └──────────┘    └────────────┘   └─────────────┘
              │                │                │
              └────────────────┼────────────────┘
                               ▼
                    ┌──────────────────────┐
                    │ SQLAlchemy + SQLite │
                    └──────────────────────┘
