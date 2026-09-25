"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import SessionLocal, create_database_tables
from app.routers.admin import router as admin_router
from app.routers.assessments import router as assessments_router
from app.routers.auth import router as auth_router
from app.routers.counsellor import router as counsellor_router
from app.routers.cv import router as cv_router
from app.routers.health import router as health_router
from app.routers.portal import router as portal_router
from app.services.assessment_catalog import ensure_default_assessment


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    health_router,
    prefix="/api",
)

app.include_router(
    auth_router,
    prefix="/api",
)

app.include_router(
    portal_router,
    prefix="/api",
)

app.include_router(
    assessments_router,
    prefix="/api",
)

app.include_router(
    cv_router,
    prefix="/api",
)

app.include_router(
    counsellor_router,
    prefix="/api",
)

app.include_router(
    admin_router,
    prefix="/api",
)


@app.on_event("startup")
def initialize_database() -> None:
    """Ensure database tables and default assessment exist."""

    create_database_tables()

    with SessionLocal() as database:
        ensure_default_assessment(database)
