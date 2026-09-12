import base64

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.assessment import (
    BehaviorTelemetry,
    Response,
    Session as AssessmentSession,
)
from app.models.user import User
from app.services.analytics.behavior_analytics import (
    calculate_behavioral_analytics,
)
from app.services.cv.face_detector import FaceDetector


router = APIRouter(
    prefix="/cv",
    tags=["CV"],
)

detector = FaceDetector()


class FrameRequest(BaseModel):
    image: str
    session_id: int


class PreviewFrameRequest(BaseModel):
    image: str


@router.post("/preview")
def preview_frame(
    payload: PreviewFrameRequest,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Student access required",
        )

    if "," in payload.image:
        image_data = payload.image.split(",", 1)[1]
    else:
        image_data = payload.image

    try:
        image_bytes = base64.b64decode(image_data)

        np_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8,
        )

        frame = cv2.imdecode(
            np_array,
            cv2.IMREAD_COLOR,
        )

        if frame is None:
            raise ValueError("Invalid image")

        result = detector.process(frame)

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to analyze preview frame: {error}",
        ) from error

    return {
        "face_detected": result["face_detected"],
        "landmark_count": result["landmark_count"],
        "left_ear": result["left_ear"],
        "right_ear": result["right_ear"],
        "blink_detected": result["blink_detected"],
        "blink_count": result["blink_count"],
        "gaze": result["gaze"],
        "head_pose": result["head_pose"],
    }


@router.post("/analyze")
def analyze_frame(
    payload: FrameRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Student access required",
        )

    session = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.id == payload.session_id,
            AssessmentSession.student_id == current_user.id,
        )
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment session not found",
        )

    if "," in payload.image:
        image_data = payload.image.split(",", 1)[1]
    else:
        image_data = payload.image

    try:
        image_bytes = base64.b64decode(image_data)

        np_array = np.frombuffer(
            image_bytes,
            dtype=np.uint8,
        )

        frame = cv2.imdecode(
            np_array,
            cv2.IMREAD_COLOR,
        )

        if frame is None:
            raise ValueError("Invalid image")

        print(
            "FRAME:",
            frame.shape,
            "MIN:",
            frame.min(),
            "MAX:",
            frame.max(),
        )

        result = detector.process(frame)

        print(
            "CV RESULT:",
            result["face_detected"],
            result["landmark_count"],
        )

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Unable to analyze frame: {error}",
        ) from error

    telemetry = BehaviorTelemetry(
        session_id=session.id,
        face_detected=result["face_detected"],
        landmark_count=result["landmark_count"],
        left_ear=result["left_ear"],
        right_ear=result["right_ear"],
        blink_detected=result["blink_detected"],
        blink_count=result["blink_count"],
        gaze_horizontal=result["gaze"]["horizontal"],
        gaze_vertical=result["gaze"]["vertical"],
        gaze_direction=result["gaze"]["direction"],
        head_yaw=result["head_pose"]["yaw"],
        head_pitch=result["head_pose"]["pitch"],
        head_roll=result["head_pose"]["roll"],
    )

    db.add(telemetry)
    db.commit()

    return {
        "face_detected": result["face_detected"],
        "landmark_count": result["landmark_count"],
        "left_ear": result["left_ear"],
        "right_ear": result["right_ear"],
        "blink_detected": result["blink_detected"],
        "blink_count": result["blink_count"],
        "gaze": result["gaze"],
        "head_pose": result["head_pose"],
    }


@router.get("/analytics/{session_id}")
def get_behavioral_analytics(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != "student":
        raise HTTPException(
            status_code=403,
        detail="Student access required",
        )

    session = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.id == session_id,
            AssessmentSession.student_id == current_user.id,
        )
        .first()
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Assessment session not found",
        )

    telemetry = (
        db.query(BehaviorTelemetry)
        .filter(
            BehaviorTelemetry.session_id == session_id,
        )
        .order_by(
            BehaviorTelemetry.recorded_at.asc(),
        )
        .all()
    )

    responses = (
        db.query(Response)
        .filter(
            Response.session_id == session_id,
        )
        .order_by(
            Response.answered_at.asc(),
        )
        .all()
    )

    return calculate_behavioral_analytics(
        telemetry,
        responses,
    )