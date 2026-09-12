# Setup

## Prerequisites

- Python 3.11 or newer
- Node.js 20 or newer

## Backend

From the repository root in PowerShell:

```powershell
cd backend
Copy-Item ..\.env.example ..\.env
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be at `http://localhost:8000`; its health endpoint is `http://localhost:8000/api/health`.

Before running in any shared environment, replace `MINDTRACE_JWT_SECRET` in `.env` with a unique, random value of at least 32 characters.

## Demo accounts

After starting the backend environment, create local demo accounts with:

```powershell
cd backend
python -m scripts.seed_demo_users
```

- Student: `student@example.com` / `StudentDemo2026!`
- Counsellor: `counsellor@example.com` / `CounsellorDemo2026!`

These credentials are only for local development; do not deploy them.

## Frontend

In a second terminal:

```powershell
cd frontend
pnpm install
pnpm run dev
```

Open the URL Vite prints (normally `http://localhost:5173`). The page makes a request to the backend health endpoint. To use a different backend URL, set `VITE_API_URL` before starting Vite.

## Test

```powershell
cd backend
pytest
```
