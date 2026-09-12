from fastapi import APIRouter, Depends

from app.auth.dependencies import require_role
from app.models.user import User, UserRole


router = APIRouter(
    prefix="/portal",
    tags=["portal"],
)


@router.get("/student")
def student_portal(
    user: User = Depends(require_role(UserRole.STUDENT)),
) -> dict[str, str]:
    return {
        "message": (
            f"Welcome, {user.name}. "
            "Complete your psychometric assessments "
            "and review your results."
        )
    }


@router.get("/counsellor")
def counsellor_portal(
    user: User = Depends(require_role(UserRole.COUNSELLOR)),
) -> dict[str, str]:
    return {
        "message": (
            f"Welcome, {user.name}. "
            "Review student assessments and "
            "behavioural analytics."
        )
    }
