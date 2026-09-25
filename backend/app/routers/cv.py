"""Browser-derived behavioural telemetry endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.assessment import BehaviorTelemetry, ConsentRecord, Response, Session as AssessmentSession, SessionStatus
from app.models.user import User
from app.services.analytics.behavior_analytics import calculate_behavioral_analytics

router = APIRouter(prefix="/cv", tags=["CV"])


class GazePayload(BaseModel):
    horizontal: float = Field(ge=-0.5, le=0.5)
    vertical: float = Field(ge=-0.5, le=0.5)
    direction: str = Field(max_length=50)


class HeadPosePayload(BaseModel):
    yaw: float = Field(ge=-90, le=90)
    pitch: float = Field(ge=-90, le=90)
    roll: float = Field(ge=-90, le=90)


class TelemetryRequest(BaseModel):
    session_id: int
    face_detected: bool
    landmark_count: int = Field(ge=0, le=1000)
    left_ear: float = Field(ge=0, le=10)
    right_ear: float = Field(ge=0, le=10)
    blink_detected: bool
    blink_count: int = Field(ge=0)
    gaze: GazePayload
    head_pose: HeadPosePayload


def _owned_session(session_id: int, user: User, database: Session) -> AssessmentSession:
    item = database.query(AssessmentSession).filter(
        AssessmentSession.id == session_id,
        AssessmentSession.student_id == user.id,
    ).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Assessment session not found")
    return item


@router.post("/telemetry")
def record_telemetry(payload: TelemetryRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    session = _owned_session(payload.session_id, current_user, db)
    if session.status == SessionStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="This assessment session is already complete")
    consent = db.query(ConsentRecord).filter(ConsentRecord.session_id == session.id).first()
    if consent is None or not consent.granted:
        raise HTTPException(status_code=403, detail="Webcam consent has not been recorded for this session")
    item = BehaviorTelemetry(
        session_id=payload.session_id, face_detected=payload.face_detected,
        landmark_count=payload.landmark_count, left_ear=payload.left_ear,
        right_ear=payload.right_ear, blink_detected=payload.blink_detected,
        blink_count=payload.blink_count, gaze_horizontal=payload.gaze.horizontal,
        gaze_vertical=payload.gaze.vertical, gaze_direction=payload.gaze.direction,
        head_yaw=payload.head_pose.yaw, head_pitch=payload.head_pose.pitch,
        head_roll=payload.head_pose.roll,
    )
    db.add(item)
    db.commit()
    return {"recorded": True}


@router.get("/analytics/{session_id}")
def get_behavioral_analytics(session_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.role != "student":
        raise HTTPException(status_code=403, detail="Student access required")
    _owned_session(session_id, current_user, db)
    telemetry = db.query(BehaviorTelemetry).filter(BehaviorTelemetry.session_id == session_id).order_by(BehaviorTelemetry.recorded_at.asc()).all()
    responses = db.query(Response).filter(Response.session_id == session_id).order_by(Response.answered_at.asc()).all()
    return calculate_behavioral_analytics(telemetry, responses)
