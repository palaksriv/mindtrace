"""Counsellor dashboard and student history endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DbSession, joinedload

from app.auth.dependencies import require_role
from app.dependencies import get_db
from app.models.assessment import (
    BehaviorTelemetry,
    CounsellorReview,
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


class ReviewUpdate(BaseModel):
    status: str = Field(pattern="^(routine|review|follow_up)$")
    notes: str = Field(max_length=5000)


@router.get("/sessions/{session_id}/review")
def get_review(session_id: int, counsellor: User = Depends(require_role(UserRole.COUNSELLOR)), database: DbSession = Depends(get_db)):
    review = database.scalar(select(CounsellorReview).where(CounsellorReview.session_id == session_id))
    return {"status": review.status if review else "routine", "notes": review.notes if review else "", "updated_at": review.updated_at if review else None}


@router.put("/sessions/{session_id}/review")
def save_review(session_id: int, payload: ReviewUpdate, counsellor: User = Depends(require_role(UserRole.COUNSELLOR)), database: DbSession = Depends(get_db)):
    if database.get(Session, session_id) is None:
        raise HTTPException(status_code=404, detail="Assessment session not found")
    review = database.scalar(select(CounsellorReview).where(CounsellorReview.session_id == session_id))
    if review is None:
        review = CounsellorReview(session_id=session_id, counsellor_id=counsellor.id, status=payload.status, notes=payload.notes)
        database.add(review)
    else:
        review.status, review.notes, review.counsellor_id = payload.status, payload.notes, counsellor.id
    database.commit(); database.refresh(review)
    return {"status": review.status, "notes": review.notes, "updated_at": review.updated_at}


@router.get("/overview")
def counsellor_overview(
    counsellor: User = Depends(require_role(UserRole.COUNSELLOR)),
    database: DbSession = Depends(get_db),
):
    """Caseload summary with non-diagnostic review cues."""
    students = database.scalars(select(User).where(User.role == UserRole.STUDENT).order_by(User.name)).all()
    items = []
    for student in students:
        sessions = database.scalars(select(Session).where(Session.student_id == student.id, Session.status == SessionStatus.COMPLETED).order_by(Session.completed_at.desc())).all()
        latest = sessions[0] if sessions else None
        cues: list[str] = []
        analytics = None
        if latest:
            telemetry = database.scalars(select(BehaviorTelemetry).where(BehaviorTelemetry.session_id == latest.id)).all()
            responses = database.scalars(select(Response).options(joinedload(Response.question)).where(Response.session_id == latest.id)).all()
            analytics = calculate_behavioral_analytics(telemetry, responses)
            if analytics["sample_count"] == 0:
                cues.append("No camera telemetry captured")
            elif analytics["data_quality"]["status"] == "sparse":
                cues.append("Very few camera samples captured")
            elif analytics["face_presence_percent"] < 80:
                cues.append("Inconsistent face presence")
            if analytics["behavioral_deviation"]["level"] == "HIGH":
                cues.append("Review observable session variation")
        items.append({
            "id": student.id, "name": student.name, "email": student.email,
            "completed_assessments": len(sessions),
            "latest_session_id": latest.id if latest else None,
            "latest_completed_at": latest.completed_at if latest else None,
            "review_cues": cues,
            "telemetry_samples": analytics["sample_count"] if analytics else 0,
        })
    return items


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


@router.get("/students/{student_id}/trends")
def get_student_trends(student_id: int, counsellor: User = Depends(require_role(UserRole.COUNSELLOR)), database: DbSession = Depends(get_db)):
    """Comparable summaries for a student's own completed sessions."""
    sessions = database.scalars(select(Session).where(Session.student_id == student_id, Session.status == SessionStatus.COMPLETED).order_by(Session.completed_at.asc())).all()
    result = []
    for item in sessions:
        responses = database.scalars(select(Response).options(joinedload(Response.question)).where(Response.session_id == item.id)).all()
        telemetry = database.scalars(select(BehaviorTelemetry).where(BehaviorTelemetry.session_id == item.id)).all()
        analytics = calculate_behavioral_analytics(telemetry, responses)
        result.append({"session_id": item.id, "completed_at": item.completed_at, "trait_scores": calculate_trait_scores(responses), "average_latency_ms": analytics["response_latency"]["average_latency_ms"], "sample_count": analytics["sample_count"], "face_presence_percent": analytics["face_presence_percent"]})
    return result


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
