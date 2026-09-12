"""Protected development administration endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import require_role
from app.dependencies import get_db
from app.models.assessment import BehaviorTelemetry, Response, Session
from app.models.user import User, UserRole

router = APIRouter(
    prefix="/admin",
    tags=["administration"],
)


@router.post("/wipe")
def wipe_test_data(
    counsellor: User = Depends(require_role(UserRole.COUNSELLOR)),
    database: DbSession = Depends(get_db),
) -> dict[str, str | int]:
    """Delete assessment test history while preserving users and definitions."""

    telemetry_count = database.query(BehaviorTelemetry).delete(
        synchronize_session=False
    )
    response_count = database.query(Response).delete(
        synchronize_session=False
    )
    session_count = database.query(Session).delete(
        synchronize_session=False
    )

    database.commit()

    return {
        "message": "Test assessment data cleared successfully.",
        "sessions_deleted": session_count,
        "responses_deleted": response_count,
        "telemetry_deleted": telemetry_count,
    }
