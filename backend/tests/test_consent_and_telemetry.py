"""Consent gating, telemetry ingestion and access control for the CV endpoints."""

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import answer_all, make_user, start_session, telemetry


def test_telemetry_is_rejected_until_consent_is_recorded() -> None:
    with TestClient(app) as client:
        h = make_user(client)
        sid, _ = start_session(client, h)
        r = client.post("/api/cv/telemetry", headers=h, json=telemetry(sid))
        assert r.status_code == 403
        assert "consent" in r.json()["detail"].lower()


def test_declined_consent_still_blocks_telemetry() -> None:
    with TestClient(app) as client:
        h = make_user(client)
        sid, _ = start_session(client, h)
        assert client.post(f"/api/sessions/{sid}/consent", headers=h, json={"granted": False}).status_code == 200
        assert client.post("/api/cv/telemetry", headers=h, json=telemetry(sid)).status_code == 403


def test_consent_record_is_versioned_and_telemetry_accepted_afterwards() -> None:
    with TestClient(app) as client:
        h = make_user(client)
        sid, _ = start_session(client, h)
        c = client.post(f"/api/sessions/{sid}/consent", headers=h, json={"granted": True})
        assert c.status_code == 200
        body = c.json()
        assert body["granted"] is True and body["notice_version"] and body["recorded_at"]
        assert client.post("/api/cv/telemetry", headers=h, json=telemetry(sid)).json() == {"recorded": True}


def test_student_cannot_write_telemetry_or_consent_for_another_students_session() -> None:
    with TestClient(app) as client:
        owner, other = make_user(client), make_user(client)
        sid, _ = start_session(client, owner)
        assert client.post(f"/api/sessions/{sid}/consent", headers=other, json={"granted": True}).status_code == 404
        assert client.post("/api/cv/telemetry", headers=other, json=telemetry(sid)).status_code == 404


def test_counsellor_cannot_post_telemetry() -> None:
    with TestClient(app) as client:
        student, counsellor = make_user(client), make_user(client, "counsellor")
        sid, _ = start_session(client, student)
        assert client.post("/api/cv/telemetry", headers=counsellor, json=telemetry(sid)).status_code == 403


def test_out_of_range_telemetry_is_rejected_by_validation() -> None:
    with TestClient(app) as client:
        h = make_user(client)
        sid, _ = start_session(client, h)
        client.post(f"/api/sessions/{sid}/consent", headers=h, json={"granted": True})
        bad = telemetry(sid, head_pose={"yaw": 500, "pitch": 0, "roll": 0})
        assert client.post("/api/cv/telemetry", headers=h, json=bad).status_code == 422


def test_telemetry_after_completion_is_rejected() -> None:
    with TestClient(app) as client:
        h = make_user(client)
        sid, qs = start_session(client, h)
        client.post(f"/api/sessions/{sid}/consent", headers=h, json={"granted": True})
        answer_all(client, h, sid, qs)
        assert client.post(f"/api/sessions/{sid}/complete", headers=h).status_code == 200
        assert client.post("/api/cv/telemetry", headers=h, json=telemetry(sid)).status_code == 409
