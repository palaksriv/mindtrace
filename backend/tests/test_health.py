"""Tests for the Day 1 operational endpoint."""

from fastapi.testclient import TestClient

from app.main import app

def test_health_endpoint_reports_api_and_database_status() -> None:
    with TestClient(app) as client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "MindTrace API"}
