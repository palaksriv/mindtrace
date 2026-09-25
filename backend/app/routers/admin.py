"""Protected development administration endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete
from sqlalchemy.orm import Session as DbSession

from app.auth.dependencies import require_role
from app.config import get_settings
from app.dependencies import get_db
from app.models.assessment import (
    BehaviorTelemetry,
    ConsentRecord,
    CounsellorReview,
    Response,
    Session,
)
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
    """Delete assessment test history while preserving users and definitions.

    Disabled unless MINDTRACE_ALLOW_DATA_WIPE=true so that a production
    deployment cannot lose research data through a single request.
    """
    if not get_settings().allow_data_wipe:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Data wipe is disabled in this environment",
        )

    database.query(CounsellorReview).delete(synchronize_session=False)
    database.query(ConsentRecord).delete(synchronize_session=False)
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
