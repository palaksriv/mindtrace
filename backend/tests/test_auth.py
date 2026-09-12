"""Authentication and role-control tests."""

from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def register(client: TestClient, role: str) -> tuple[dict[str, object], str]:
    email = f"{uuid4().hex}@example.com"
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": email,
            "password": "A secure test password 2026!",
            "role": role,
        },
    )
    assert response.status_code == 201
    return response.json(), email


def login(client: TestClient, email: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "A secure test password 2026!"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_login_me_and_student_role_route() -> None:
    with TestClient(app) as client:
        user, email = register(client, "student")
        token = login(client, email)
        headers = {"Authorization": f"Bearer {token}"}

        me = client.get("/api/auth/me", headers=headers)
        assert me.status_code == 200
        assert me.json()["id"] == user["id"]
        assert me.json()["role"] == "student"

        assert client.get("/api/portal/student", headers=headers).status_code == 200
        assert client.get("/api/portal/counsellor", headers=headers).status_code == 403


def test_invalid_credentials_fail_safely() -> None:
    with TestClient(app) as client:
        _, email = register(client, "counsellor")
        response = client.post("/api/auth/login", json={"email": email, "password": "wrong"})

        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"


def test_missing_token_is_rejected() -> None:
    with TestClient(app) as client:
        assert client.get("/api/auth/me").status_code == 401
