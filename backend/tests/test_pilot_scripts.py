"""End-to-end check of the pilot-study export and reliability tooling."""

import csv
import random
import sys
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import make_user, start_session


def _submit(client, headers, sid, questions, rng, latent):
    shown = datetime.now(timezone.utc)
    for q in questions:
        base = latent[q["trait"]]
        raw = min(5, max(1, round(base + rng.gauss(0, 0.6))))
        # respondents answer reverse-keyed items in the opposite direction
        value = raw
        client.post(f"/api/sessions/{sid}/responses", headers=headers, json={
            "question_id": q["id"], "response": value,
            "displayed_at": shown.isoformat(), "answered_at": (shown + timedelta(seconds=3)).isoformat()})


def test_export_is_pseudonymised_consent_filtered_and_feeds_reliability(tmp_path, monkeypatch, capsys) -> None:
    rng = random.Random(7)
    with TestClient(app) as client:
        emails = []
        for i in range(14):
            h = make_user(client)
            emails.append(client.get("/api/auth/me", headers=h).json()["email"])
            for retest in range(2 if i < 6 else 1):
                sid, qs = start_session(client, h)
                consent = i != 13  # the last student never consents
                client.post(f"/api/sessions/{sid}/consent", headers=h, json={"granted": consent})
                latent = {t: rng.uniform(1.5, 4.5) for t in
                          ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]}
                _submit(client, h, sid, qs, rng, latent)
                assert client.post(f"/api/sessions/{sid}/complete", headers=h).status_code == 200

    from scripts import export_pilot_data, reliability_report

    monkeypatch.setenv("MINDTRACE_EXPORT_SALT", "a-long-random-test-salt-value")
    monkeypatch.setattr(sys, "argv", ["export", "--out", str(tmp_path)])
    export_pilot_data.main()
    out = capsys.readouterr().out
    assert "skipped" in out

    items = (tmp_path / "item_responses.csv").read_text()
    sessions_csv = (tmp_path / "session_summary.csv").read_text()
    for e in emails:
        assert e not in items and e not in sessions_csv          # no direct identifiers
    rows = list(csv.DictReader((tmp_path / "session_summary.csv").open()))
    assert rows and all(len(r["pseudonym"]) == 16 for r in rows)

    monkeypatch.setattr(sys, "argv", ["rel", "--items", str(tmp_path / "item_responses.csv"),
                                      "--sessions", str(tmp_path / "session_summary.csv")])
    reliability_report.main()
    report = capsys.readouterr().out
    for trait in ("openness", "neuroticism"):
        assert trait in report


def test_export_refuses_to_run_without_a_salt(monkeypatch, tmp_path) -> None:
    import pytest
    from scripts import export_pilot_data

    monkeypatch.delenv("MINDTRACE_EXPORT_SALT", raising=False)
    monkeypatch.setattr(sys, "argv", ["export", "--out", str(tmp_path)])
    with pytest.raises(SystemExit):
        export_pilot_data.main()
