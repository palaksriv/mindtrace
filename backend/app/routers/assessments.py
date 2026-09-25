"""Student assessment and session endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DbSession, joinedload

from app.auth.dependencies import require_role
from app.config import get_settings
from app.dependencies import get_db
from app.models.assessment import Assessment, ConsentRecord, Question, Response, Session, SessionStatus
from app.models.user import User, UserRole
from app.schemas.assessment import (
    AssessmentDetail, AssessmentResults, AssessmentSummary, ConsentRequest, ConsentResponse,
    CreateSessionRequest, SessionResponse,
    StoredResponse, SubmitResponseRequest,
)
from app.services.scoring import calculate_trait_scores

router = APIRouter(tags=["assessments"])


def owned_session(session_id: int, student: User, database: DbSession) -> Session:
    item = database.scalar(
        select(Session).where(Session.id == session_id, Session.student_id == student.id)
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Assessment session not found")
    return item


@router.get("/assessments", response_model=list[AssessmentSummary])
def list_assessments(student: User = Depends(require_role(UserRole.STUDENT)), database: DbSession = Depends(get_db)) -> list[AssessmentSummary]:
    assessments = database.scalars(select(Assessment).order_by(Assessment.id)).all()
    return [AssessmentSummary(id=item.id, title=item.title, description=item.description, question_count=len(item.questions)) for item in assessments]


@router.get("/assessments/{assessment_id}", response_model=AssessmentDetail)
def get_assessment(assessment_id: int, student: User = Depends(require_role(UserRole.STUDENT)), database: DbSession = Depends(get_db)) -> Assessment:
    assessment = database.scalar(select(Assessment).where(Assessment.id == assessment_id))
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(payload: CreateSessionRequest, student: User = Depends(require_role(UserRole.STUDENT)), database: DbSession = Depends(get_db)) -> Session:
    if database.get(Assessment, payload.assessment_id) is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    item = Session(student_id=student.id, assessment_id=payload.assessment_id)
    database.add(item)
    database.commit()
    database.refresh(item)
    return item


@router.post("/sessions/{session_id}/consent", response_model=ConsentResponse)
def record_consent(session_id: int, payload: ConsentRequest, student: User = Depends(require_role(UserRole.STUDENT)), database: DbSession = Depends(get_db)) -> ConsentRecord:
    """Store an auditable webcam-consent record before any telemetry is accepted."""
    item = owned_session(session_id, student, database)
    if item.status == SessionStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="This assessment session is already complete")
    record = database.scalar(select(ConsentRecord).where(ConsentRecord.session_id == item.id))
    version = get_settings().consent_notice_version
    if record is None:
        record = ConsentRecord(session_id=item.id, granted=payload.granted, notice_version=version)
        database.add(record)
    else:
        record.granted, record.notice_version = payload.granted, version
        record.recorded_at = datetime.now(timezone.utc)
    database.commit()
    database.refresh(record)
    return record


@router.post("/sessions/{session_id}/responses", response_model=StoredResponse)
def submit_response(session_id: int, payload: SubmitResponseRequest, student: User = Depends(require_role(UserRole.STUDENT)), database: DbSession = Depends(get_db)) -> Response:
    item = owned_session(session_id, student, database)
    if item.status == SessionStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="This assessment session is already complete")
    question = database.scalar(select(Question).where(Question.id == payload.question_id, Question.assessment_id == item.assessment_id))
    if question is None:
        raise HTTPException(status_code=400, detail="Question does not belong to this assessment")
    displayed_at = payload.displayed_at.astimezone(timezone.utc)
    answered_at = payload.answered_at.astimezone(timezone.utc)
    if answered_at < displayed_at:
        raise HTTPException(status_code=422, detail="answered_at must not be before displayed_at")
    latency_ms = int((answered_at - displayed_at).total_seconds() * 1000)
    response = database.scalar(select(Response).where(Response.session_id == item.id, Response.question_id == question.id))
    if response is None:
        response = Response(session_id=item.id, question_id=question.id, response=payload.response, displayed_at=displayed_at, answered_at=answered_at, latency_ms=latency_ms)
        database.add(response)
    else:
        response.response, response.displayed_at, response.answered_at, response.latency_ms = payload.response, displayed_at, answered_at, latency_ms
    database.commit()
    database.refresh(response)
    return response


@router.post("/sessions/{session_id}/complete", response_model=AssessmentResults)
def complete_session(session_id: int, student: User = Depends(require_role(UserRole.STUDENT)), database: DbSession = Depends(get_db)) -> AssessmentResults:
    item = owned_session(session_id, student, database)
    if item.status == SessionStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="This assessment session is already complete")
    questions = database.scalars(select(Question).where(Question.assessment_id == item.assessment_id)).all()
    responses = database.scalars(select(Response).options(joinedload(Response.question)).where(Response.session_id == item.id)).all()
    if len(responses) != len(questions):
        raise HTTPException(status_code=422, detail="Every question must be answered before completion")
    item.status, item.completed_at = SessionStatus.COMPLETED, datetime.now(timezone.utc)
    database.commit()
    return AssessmentResults(session_id=item.id, status=item.status, completed_at=item.completed_at, trait_scores=calculate_trait_scores(responses))


@router.get("/sessions/{session_id}/results", response_model=AssessmentResults)
def get_results(session_id: int, student: User = Depends(require_role(UserRole.STUDENT)), database: DbSession = Depends(get_db)) -> AssessmentResults:
    item = owned_session(session_id, student, database)
    if item.status != SessionStatus.COMPLETED or item.completed_at is None:
        raise HTTPException(status_code=409, detail="Assessment session is not complete")
    responses = database.scalars(select(Response).options(joinedload(Response.question)).where(Response.session_id == item.id)).all()
    return AssessmentResults(session_id=item.id, status=item.status, completed_at=item.completed_at, trait_scores=calculate_trait_scores(responses))
