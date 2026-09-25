"""Schemas for assessment delivery, response recording, and scoring."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.assessment import SessionStatus, Trait


class AssessmentSummary(BaseModel):
    id: int
    title: str
    description: str
    question_count: int


class QuestionResponse(BaseModel):
    id: int
    question_text: str
    trait: Trait
    order: int

    model_config = ConfigDict(from_attributes=True)


class AssessmentDetail(BaseModel):
    id: int
    title: str
    description: str
    questions: list[QuestionResponse]


class CreateSessionRequest(BaseModel):
    assessment_id: int


class ConsentRequest(BaseModel):
    granted: bool


class ConsentResponse(BaseModel):
    session_id: int
    granted: bool
    notice_version: str
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionResponse(BaseModel):
    id: int
    assessment_id: int
    status: SessionStatus
    started_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubmitResponseRequest(BaseModel):
    question_id: int
    response: int = Field(ge=1, le=5)
    displayed_at: datetime
    answered_at: datetime


class StoredResponse(BaseModel):
    id: int
    question_id: int
    response: int
    displayed_at: datetime
    answered_at: datetime
    latency_ms: int

    model_config = ConfigDict(from_attributes=True)


class AssessmentResults(BaseModel):
    session_id: int
    status: SessionStatus
    completed_at: datetime
    trait_scores: dict[str, float]
