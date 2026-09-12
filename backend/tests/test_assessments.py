"""End-to-end tests for Day 3 assessment flow."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def student_headers(client: TestClient) -> dict[str, str]:
    email = f"{uuid4().hex}@example.com"
    client.post("/api/auth/register", json={"name": "Assessment Student", "email": email, "password": "Secure testing password 2026!", "role": "student"})
    token = client.post("/api/auth/login", json={"email": email, "password": "Secure testing password 2026!"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_student_can_complete_assessment_and_receive_scores() -> None:
    with TestClient(app) as client:
        headers = student_headers(client)
        assessments = client.get("/api/assessments", headers=headers).json()
        assert len(assessments) == 1
        assert assessments[0]["question_count"] == 20
        detail = client.get(f"/api/assessments/{assessments[0]['id']}", headers=headers).json()
        session_id = client.post("/api/sessions", headers=headers, json={"assessment_id": detail["id"]}).json()["id"]
        displayed_at = datetime.now(timezone.utc)
        for question in detail["questions"]:
            answered_at = displayed_at + timedelta(seconds=2)
            stored = client.post(f"/api/sessions/{session_id}/responses", headers=headers, json={"question_id": question["id"], "response": 4, "displayed_at": displayed_at.isoformat(), "answered_at": answered_at.isoformat()})
            assert stored.status_code == 200
            assert stored.json()["latency_ms"] == 2000
        completed = client.post(f"/api/sessions/{session_id}/complete", headers=headers)
        assert completed.status_code == 200
        scores = completed.json()["trait_scores"]
        assert set(scores) == {"openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"}
        assert all(0 <= score <= 100 for score in scores.values())
        assert client.get(f"/api/sessions/{session_id}/results", headers=headers).status_code == 200


def test_incomplete_assessment_cannot_be_completed() -> None:
    with TestClient(app) as client:
        headers = student_headers(client)
        assessment_id = client.get("/api/assessments", headers=headers).json()[0]["id"]
        session_id = client.post("/api/sessions", headers=headers, json={"assessment_id": assessment_id}).json()["id"]
        response = client.post(f"/api/sessions/{session_id}/complete", headers=headers)
        assert response.status_code == 422
