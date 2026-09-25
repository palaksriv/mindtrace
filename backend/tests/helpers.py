"""Small helpers shared by the test modules."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

PASSWORD = "A secure test password 2026!"
INVITE_CODE = "test-invite-code"


def make_user(client: TestClient, role: str = "student") -> dict[str, str]:
    """Register a user (with the invite code for counsellors) and return auth headers."""
    email = f"{uuid4().hex}@example.com"
    payload = {"name": "Test User", "email": email, "password": PASSWORD, "role": role}
    if role == "counsellor":
        payload["invite_code"] = INVITE_CODE
    assert client.post("/api/auth/register", json=payload).status_code == 201
    token = client.post("/api/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def start_session(client: TestClient, headers: dict[str, str]) -> tuple[int, list[dict]]:
    assessment_id = client.get("/api/assessments", headers=headers).json()[0]["id"]
    detail = client.get(f"/api/assessments/{assessment_id}", headers=headers).json()
    session_id = client.post("/api/sessions", headers=headers, json={"assessment_id": assessment_id}).json()["id"]
    return session_id, detail["questions"]


def answer_all(client: TestClient, headers: dict[str, str], session_id: int, questions: list[dict], value: int = 4) -> None:
    shown = datetime.now(timezone.utc)
    for q in questions:
        r = client.post(
            f"/api/sessions/{session_id}/responses",
            headers=headers,
            json={
                "question_id": q["id"],
                "response": value,
                "displayed_at": shown.isoformat(),
                "answered_at": (shown + timedelta(seconds=2)).isoformat(),
            },
        )
        assert r.status_code == 200


def telemetry(session_id: int, **overrides) -> dict:
    body = {
        "session_id": session_id,
        "face_detected": True,
        "landmark_count": 478,
        "left_ear": 0.62,
        "right_ear": 0.61,
        "blink_detected": False,
        "blink_count": 0,
        "gaze": {"horizontal": 0.0, "vertical": 0.0, "direction": "center-center"},
        "head_pose": {"yaw": 0.0, "pitch": 0.0, "roll": 0.0},
    }
    body.update(overrides)
    return body
