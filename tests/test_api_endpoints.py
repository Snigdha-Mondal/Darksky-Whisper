"""Integration tests for DarkSky Whisper FastAPI endpoints."""

from fastapi.testclient import TestClient
import pytest

from backend.app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    """Verify system health endpoint returns operational statuses."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "Skyfield" in data["ephemeris_engine"]
    assert "TabPFN" in data["seeing_engine"]
    assert "Gemma-2" in data["reasoning_engine"]


def test_sky_coordinates_endpoint():
    """Verify celestial ephemeris calculation API endpoint."""
    resp = client.get("/api/sky", params={"latitude": 37.7749, "longitude": -122.4194, "heading": 90.0})
    assert resp.status_code == 200
    data = resp.json()
    assert "all_visible_bodies" in data
    assert data["total_visible_count"] > 0
    assert "sun_altitude_deg" in data


def test_seeing_forecast_endpoint():
    """Verify atmospheric seeing forecaster endpoint."""
    resp = client.get("/api/forecast", params={"latitude": 41.6631, "longitude": -77.8236})
    assert resp.status_code == 200
    data = resp.json()
    assert 0.0 <= data["current_seeing_score"] <= 10.0
    assert "peak_observation_window" in data
    assert len(data["hourly_forecast"]) > 0


def test_whisper_json_endpoint():
    """Verify spoken conversational reasoning endpoint returns zero markdown and <= 45 words."""
    payload = {
        "latitude": 41.6631,
        "longitude": -77.8236,
        "heading": 90.0,
        "query_text": "What is that bright orange star rising in the east?",
    }
    resp = client.post("/api/whisper/json", data=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "spoken_answer" in data
    assert data["word_count"] <= 45
    # Verify zero markdown syntax
    assert not any(c in data["spoken_answer"] for c in ["*", "#", "_", "`", "[", "]"])


def test_whisper_audio_endpoint():
    """Verify audio whisper endpoint returns audio bytes and custom metadata headers."""
    payload = {
        "latitude": 41.6631,
        "longitude": -77.8236,
        "heading": 90.0,
        "query_text": "Is Saturn visible tonight?",
    }
    resp = client.post("/api/whisper", data=payload)
    assert resp.status_code == 200
    assert resp.headers["content-type"] in ["audio/mpeg", "audio/wav"]
    assert "X-Spoken-Answer" in resp.headers
    assert "X-Seeing-Score" in resp.headers
    assert len(resp.content) > 100
