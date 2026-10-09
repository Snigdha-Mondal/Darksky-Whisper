"""Unit tests verifying screenless mobile PWA and rhodopsin night-vision safeguard."""

from fastapi.testclient import TestClient
import pytest

from backend.app.main import app

client = TestClient(app)


def test_serve_index_html():
    """Verify root / serves the minimalist OLED red mobile interface."""
    resp = client.get("/")
    assert resp.status_code == 200
    html = resp.text
    assert "DARKSKY WHISPER" in html
    assert "statusAura" in html
    assert "OLED RED SAFEGUARD" in html
    assert "whisperAudioSink" in html


def test_serve_style_css_and_status_aura():
    """Verify style.css serves the peripheral status aura and OLED dark theme."""
    resp = client.get("/src/style.css")
    assert resp.status_code == 200
    css = resp.text
    # Verify OLED deep red color tokens
    assert "#1a0505" in css or "#000000" in css
    assert "status-aura" in css
    # Verify peripheral aura state classes
    assert "state-listening" in css
    assert "state-computing" in css
    assert "state-speaking" in css


def test_serve_app_js():
    """Verify app.js provides full-screen tap-anywhere touch state machine and mic gating."""
    resp = client.get("/src/app.js")
    assert resp.status_code == 200
    js = resp.text
    assert "DarkSkyApp" in js
    assert "setupTouchListener" in js
    assert "MediaRecorder" in js
    assert "playSpeechAudio" in js
    assert "deviceorientation" in js


def test_serve_manifest_json():
    """Verify PWA manifest is served for standalone mobile installation."""
    resp = client.get("/public/manifest.json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["display"] == "standalone"
    assert data["background_color"] == "#000000"
    assert data["theme_color"] == "#1a0505"
    assert "DarkSky" in data["name"]
