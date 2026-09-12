"""SQLAlchemy database setup for the Day 1 SQLite connection."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()
engine_options: dict[str, object] = {}
if settings.database_url.startswith("sqlite"):
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(settings.database_url, **engine_options)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Base(DeclarativeBase):
    """Base class reserved for ORM models added in later milestones."""


def verify_database_connection() -> None:
    """Run a lightweight query to confirm the configured database is reachable."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def create_database_tables() -> None:
    """Create the currently defined ORM tables during application startup."""
    from app import models  # noqa: F401  # Ensure model metadata is registered.

    Base.metadata.create_all(bind=engine)
