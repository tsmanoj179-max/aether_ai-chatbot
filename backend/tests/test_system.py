import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_system_heartbeat_get():
    response = client.get("/api/v1/system/heartbeat")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
    assert "timestamp" in data
    assert "uptime_seconds" in data

def test_system_heartbeat_post():
    response = client.post("/api/v1/system/heartbeat", json={"action": "ping"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"

def test_system_shutdown_graceful():
    response = client.post("/api/v1/system/shutdown", json={"immediate": False})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending_shutdown"
    assert "grace_period_seconds" in data

    # Follow up with heartbeat to ensure cancel works
    hb = client.post("/api/v1/system/heartbeat")
    assert hb.status_code == 200
