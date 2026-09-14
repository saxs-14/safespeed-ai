import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_dashboard_summary_shape():
    r = client.get("/api/dashboard/summary")
    assert r.status_code == 200
    body = r.json()
    for key in ["total_vehicles", "average_speed_kmh", "max_speed_kmh", "speeding_count", "total_sessions"]:
        assert key in body


def test_events_list_returns_array():
    r = client.get("/api/events")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_analyze_demo_requires_demo_video_present():
    r = client.post("/api/analyze/demo", data={"speed_limit_kmh": 60, "pixels_per_meter": 8})
    assert r.status_code in (200, 404)
    if r.status_code == 200:
        body = r.json()
        assert "id" in body
        assert body["status"] == "completed"
