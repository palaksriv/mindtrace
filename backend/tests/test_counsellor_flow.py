"""Counsellor endpoints: role control, reports, cues and review workflow."""

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import answer_all, make_user, start_session, telemetry


def _complete_session(client, headers, with_telemetry: int = 0) -> int:
    sid, qs = start_session(client, headers)
    client.post(f"/api/sessions/{sid}/consent", headers=headers, json={"granted": True})
    for _ in range(with_telemetry):
        assert client.post("/api/cv/telemetry", headers=headers, json=telemetry(sid)).status_code == 200
    answer_all(client, headers, sid, qs)
    assert client.post(f"/api/sessions/{sid}/complete", headers=headers).status_code == 200
    return sid


def test_students_cannot_reach_counsellor_endpoints() -> None:
    with TestClient(app) as client:
        student = make_user(client)
        for path in ("/api/counsellor/overview", "/api/counsellor/students", "/api/counsellor/sessions/1"):
            assert client.get(path, headers=student).status_code == 403


def test_unauthenticated_requests_are_rejected() -> None:
    with TestClient(app) as client:
        assert client.get("/api/counsellor/overview").status_code == 401


def test_session_report_contains_scores_and_analytics_with_data_quality() -> None:
    with TestClient(app) as client:
        student, counsellor = make_user(client), make_user(client, "counsellor")
        sid = _complete_session(client, student, with_telemetry=3)
        r = client.get(f"/api/counsellor/sessions/{sid}", headers=counsellor)
        assert r.status_code == 200
        body = r.json()
        assert set(body["results"]["trait_scores"]) == {"openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"}
        a = body["analytics"]
        assert a["sample_count"] == 3
        assert a["data_quality"]["status"] == "sparse"
        assert any("Very few" in s for s in a["behavioral_deviation"]["signals"])


def test_session_without_telemetry_is_reported_as_unavailable_not_calm() -> None:
    with TestClient(app) as client:
        student, counsellor = make_user(client), make_user(client, "counsellor")
        sid = _complete_session(client, student, with_telemetry=0)
        a = client.get(f"/api/counsellor/sessions/{sid}", headers=counsellor).json()["analytics"]
        assert a["data_quality"]["status"] == "no_telemetry"
        assert a["behavioral_deviation"]["level"] == "UNAVAILABLE"
        overview = client.get("/api/counsellor/overview", headers=counsellor).json()
        mine = [i for i in overview if i["latest_session_id"] == sid][0]
        assert "No camera telemetry captured" in mine["review_cues"]


def test_incomplete_session_report_is_refused() -> None:
    with TestClient(app) as client:
        student, counsellor = make_user(client), make_user(client, "counsellor")
        sid, _ = start_session(client, student)
        assert client.get(f"/api/counsellor/sessions/{sid}", headers=counsellor).status_code == 409


def test_review_workflow_saves_and_validates_status() -> None:
    with TestClient(app) as client:
        student, counsellor = make_user(client), make_user(client, "counsellor")
        sid = _complete_session(client, student)
        assert client.get(f"/api/counsellor/sessions/{sid}/review", headers=counsellor).json()["status"] == "routine"
        ok = client.put(f"/api/counsellor/sessions/{sid}/review", headers=counsellor, json={"status": "follow_up", "notes": "Discuss pacing."})
        assert ok.status_code == 200 and ok.json()["status"] == "follow_up"
        assert client.get(f"/api/counsellor/sessions/{sid}/review", headers=counsellor).json()["notes"] == "Discuss pacing."
        bad = client.put(f"/api/counsellor/sessions/{sid}/review", headers=counsellor, json={"status": "urgent", "notes": ""})
        assert bad.status_code == 422


def test_trends_list_completed_sessions_in_order() -> None:
    with TestClient(app) as client:
        student, counsellor = make_user(client), make_user(client, "counsellor")
        me = client.get("/api/auth/me", headers=student).json()["id"]
        first, second = _complete_session(client, student), _complete_session(client, student)
        trends = client.get(f"/api/counsellor/students/{me}/trends", headers=counsellor).json()
        assert [t["session_id"] for t in trends] == [first, second]
