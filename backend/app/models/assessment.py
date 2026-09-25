"""Assessment, question, session, and response data models."""

from datetime import datetime, timezone
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, Column, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Trait(StrEnum):
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"


class SessionStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    questions: Mapped[list["Question"]] = relationship(back_populates="assessment", order_by="Question.order")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    trait: Mapped[Trait] = mapped_column(Enum(Trait), nullable=False)
    reverse_scored: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    assessment: Mapped[Assessment] = relationship(back_populates="questions")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.IN_PROGRESS, nullable=False)
    assessment: Mapped[Assessment] = relationship()
    responses: Mapped[list["Response"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Response(Base):
    __tablename__ = "responses"
    __table_args__ = (UniqueConstraint("session_id", "question_id", name="uq_response_per_question"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), nullable=False)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), nullable=False)
    response: Mapped[int] = mapped_column(Integer, nullable=False)
    displayed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    session: Mapped[Session] = relationship(back_populates="responses")
    question: Mapped[Question] = relationship()
class BehaviorTelemetry(Base):
    __tablename__ = "behavior_telemetry"

    id: Mapped[int] = mapped_column(primary_key=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("sessions.id"),
        nullable=False,
        index=True,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    face_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    landmark_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    left_ear: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    right_ear: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    blink_detected: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    blink_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    gaze_horizontal: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    gaze_vertical: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    gaze_direction: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unknown",
    )

    head_yaw: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    head_pitch: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )

    head_roll: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
    )


class ConsentRecord(Base):
    """Auditable record that a student agreed to webcam telemetry for one session."""
    __tablename__ = "consent_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), unique=True, nullable=False, index=True)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    notice_version: Mapped[str] = mapped_column(String(40), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CounsellorReview(Base):
    """A counsellor-owned workflow note for one completed session."""
    __tablename__ = "counsellor_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), unique=True, nullable=False, index=True)
    counsellor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="routine")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
