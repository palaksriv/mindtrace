"""Counsellor accounts must not be self-provisionable."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from tests.helpers import PASSWORD, make_user


def _payload(role: str, **extra) -> dict:
    return {"name": "Someone", "email": f"{uuid4().hex}@example.com", "password": PASSWORD, "role": role, **extra}


def test_counsellor_registration_without_invite_is_forbidden() -> None:
    with TestClient(app) as client:
        assert client.post("/api/auth/register", json=_payload("counsellor")).status_code == 403


def test_counsellor_registration_with_wrong_invite_is_forbidden() -> None:
    with TestClient(app) as client:
        r = client.post("/api/auth/register", json=_payload("counsellor", invite_code="guess"))
        assert r.status_code == 403


def test_counsellor_registration_with_valid_invite_succeeds() -> None:
    with TestClient(app) as client:
        r = client.post("/api/auth/register", json=_payload("counsellor", invite_code="test-invite-code"))
        assert r.status_code == 201 and r.json()["role"] == "counsellor"


def test_student_registration_needs_no_invite() -> None:
    with TestClient(app) as client:
        assert client.post("/api/auth/register", json=_payload("student")).status_code == 201


def test_data_wipe_is_disabled_by_default() -> None:
    with TestClient(app) as client:
        headers = make_user(client, "counsellor")
        assert client.post("/api/admin/wipe", headers=headers).status_code == 403
