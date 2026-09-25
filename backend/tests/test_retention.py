"""Telemetry retention: old camera-derived rows are purged, answers are kept."""

import sys
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models.assessment import BehaviorTelemetry, Response, Session
from tests.helpers import answer_all, make_user, start_session, telemetry


def test_purge_removes_only_old_telemetry(monkeypatch, capsys) -> None:
    with TestClient(app) as client:
        h = make_user(client)
        sid, qs = start_session(client, h)
        client.post(f"/api/sessions/{sid}/consent", headers=h, json={"granted": True})
        for _ in range(4):
            client.post("/api/cv/telemetry", headers=h, json=telemetry(sid))
        answer_all(client, h, sid, qs)
        client.post(f"/api/sessions/{sid}/complete", headers=h)

    from scripts import purge_telemetry

    # Recently completed: nothing is purged.
    monkeypatch.setattr(sys, "argv", ["purge", "--older-than-days", "30"])
    purge_telemetry.main()
    with SessionLocal() as db:
        assert db.query(BehaviorTelemetry).filter_by(session_id=sid).count() == 4

    # Age the session, then dry-run (no change) and real run.
    with SessionLocal() as db:
        db.get(Session, sid).completed_at = datetime.now(timezone.utc) - timedelta(days=45)
        db.commit()
    monkeypatch.setattr(sys, "argv", ["purge", "--older-than-days", "30", "--dry-run"])
    purge_telemetry.main()
    assert "Would delete 4" in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["purge", "--older-than-days", "30"])
    purge_telemetry.main()
    with SessionLocal() as db:
        assert db.query(BehaviorTelemetry).filter_by(session_id=sid).count() == 0
        assert db.query(Response).filter_by(session_id=sid).count() == 20  # answers retained
