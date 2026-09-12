# MindTrace

**Multimodal Behavioral Analytics for Psychometric Student Counselling**

MindTrace is a final-year Computer Science project that combines **psychometric assessment** with **observable computer-vision-based behavioural telemetry** to provide counsellors with a broader view of student assessment sessions.

The system presents self-reported personality-related assessment results alongside non-diagnostic behavioural signals such as facial presence, eye aspect ratio, blinking, gaze direction, and head movement.

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
