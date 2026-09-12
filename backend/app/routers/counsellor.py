"""Counsellor dashboard and student history endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession, joinedload

from app.auth.dependencies import require_role
from app.dependencies import get_db
from app.models.assessment import (
    BehaviorTelemetry,
    Response,
    Session,
    SessionStatus,
)
from app.models.user import User, UserRole
from app.services.analytics.behavior_analytics import (
    calculate_behavioral_analytics,
)
from app.services.scoring import calculate_trait_scores


router = APIRouter(
    prefix="/counsellor",
    tags=["counsellor"],
)


@router.get("/students")
def list_students(
    counsellor: User = Depends(
        require_role(UserRole.COUNSELLOR)
    ),
    database: DbSession = Depends(get_db),
):
    """Return all student accounts for the counsellor dashboard."""

    students = database.scalars(
        select(User)
        .where(User.role == UserRole.STUDENT)
        .order_by(User.name)
    ).all()

    result = []

    for student in students:
        sessions = database.scalars(
            select(Session)
            .where(Session.student_id == student.id)
            .order_by(Session.started_at.desc())
        ).all()

        completed_sessions = [
            item
            for item in sessions
            if item.status == SessionStatus.COMPLETED
        ]

        last_session = sessions[0] if sessions else None

        result.append(
            {
                "id": student.id,
                "name": student.name,
                "email": student.email,
                "created_at": student.created_at,
                "assessment_count": len(sessions),
                "completed_assessment_count": len(
                    completed_sessions
                ),
                "last_assessment_at": (
                    last_session.started_at
                    if last_session is not None
                    else None
                ),
            }
        )

    return result


@router.get("/students/{student_id}")
def get_student(
    student_id: int,
    counsellor: User = Depends(
        require_role(UserRole.COUNSELLOR)
    ),
    database: DbSession = Depends(get_db),
):
    """Return one student's profile and assessment history."""

    student = database.scalar(
        select(User).where(
            User.id == student_id,
            User.role == UserRole.STUDENT,
        )
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    sessions = database.scalars(
        select(Session)
        .options(joinedload(Session.assessment))
        .where(Session.student_id == student.id)
        .order_by(Session.started_at.desc())
    ).all()

    history = []

    for session in sessions:
        response_count = database.scalar(
            select(func.count(Response.id)).where(
                Response.session_id == session.id
            )
        )

        history.append(
            {
                "id": session.id,
                "assessment_id": session.assessment_id,
                "assessment_title": session.assessment.title,
                "status": session.status,
                "started_at": session.started_at,
                "completed_at": session.completed_at,
                "response_count": response_count or 0,
            }
        )

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
            "created_at": student.created_at,
        },
        "sessions": history,
    }


@router.get("/sessions/{session_id}")
def get_session_detail(
    session_id: int,
    counsellor: User = Depends(
        require_role(UserRole.COUNSELLOR)
    ),
    database: DbSession = Depends(get_db),
):
    """Return complete results and analytics for a student session."""

    session = database.scalar(
        select(Session)
        .options(joinedload(Session.assessment))
        .where(Session.id == session_id)
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment session not found",
        )

    student = database.scalar(
        select(User).where(User.id == session.student_id)
    )

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found",
        )

    if session.status != SessionStatus.COMPLETED:
        raise HTTPException(
            status_code=409,
            detail="Assessment session is not complete",
        )

    responses = database.scalars(
        select(Response)
        .options(joinedload(Response.question))
        .where(Response.session_id == session.id)
        .order_by(Response.answered_at.asc())
    ).all()

    telemetry = database.scalars(
        select(BehaviorTelemetry)
        .where(
            BehaviorTelemetry.session_id == session.id
        )
        .order_by(
            BehaviorTelemetry.recorded_at.asc()
        )
    ).all()

    analytics = calculate_behavioral_analytics(
        telemetry,
        responses,
    )

    return {
        "student": {
            "id": student.id,
            "name": student.name,
            "email": student.email,
        },
        "session": {
            "id": session.id,
            "assessment_id": session.assessment_id,
            "assessment_title": session.assessment.title,
            "status": session.status,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
        },
        "results": {
            "session_id": session.id,
            "trait_scores": calculate_trait_scores(
                responses
            ),
        },
        "analytics": analytics,
    }