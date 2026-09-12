# MindTrace

MindTrace is a final-year-project MVP for presenting psychometric responses alongside observable, non-diagnostic behavioural telemetry for qualified counsellor review.

## Day 1 status

This foundation includes a React + TypeScript + Vite frontend styled with Tailwind, a FastAPI backend, SQLite/SQLAlchemy connectivity, CORS, secure student/counsellor JWT login, and a tested `GET /api/health` endpoint. Day 3 adds a 20-item original Big Five-style assessment, timestamped 1–5 responses, session completion, and transparent rule-based trait summaries. Webcam capture and computer-vision processing are not included yet.

## Assessment scoring

Each trait has four original project-specific prompts. A response uses a 1–5 Likert scale. Negatively keyed items are normalized with `6 - response`; each trait is then expressed as the mean normalized response on a 0–100 scale. These self-report summaries are not clinical or diagnostic findings.

## Architecture

```
React frontend -> FastAPI API -> SQLAlchemy -> SQLite
```

See [the setup guide](docs/SETUP.md) and [high-level design](docs/HLD.md).

## Privacy and scope

Future behavioural measures are intended as observable interaction signals only. They are not diagnostic measures and do not establish a mental-health condition or true emotional state. Raw webcam video will not be stored by default.
