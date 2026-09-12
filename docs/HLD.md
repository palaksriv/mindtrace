# MindTrace high-level design

## Day 1 foundation

The application is split into a React single-page frontend and a FastAPI backend. The frontend uses a centralized Axios client to call the API. The backend owns application configuration, CORS policy, API routers, and SQLAlchemy database access.

```
Browser (React + TypeScript + Tailwind)
             | HTTP
FastAPI (/api routes, CORS, Pydantic schemas)
             | SQLAlchemy ORM
          SQLite
```

`app.main` composes the service. `app.config` centralizes environment-based settings, `app.database` creates the SQLAlchemy engine and verifies connectivity, and routers isolate endpoint functionality. Domain models and assessment/CV services will be added only in their scheduled later milestones.
