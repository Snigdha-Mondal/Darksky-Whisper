"""Live verification script for DarkSky Whisper End-to-End Reasoning & Audio Pipeline."""

from datetime import datetime, timezone
from pathlib import Path
import sys
from fastapi.testclient import TestClient

# Ensure UTF-8 stdout on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.main import app

client = TestClient(app)


def main():
    print("=" * 80)
    print("🌌 DarkSky Whisper — End-to-End Spoken Reasoning & Audio Pipeline Verification")
    print("=" * 80)

    # Simulated observer lying on a blanket at Cherry Springs State Park
    # Coordinates: Lat 41.6631° N, Lon 77.8236° W | Compass Heading: East (90 deg)
    payload = {
        "latitude": 41.6631,
        "longitude": -77.8236,
        "elevation_m": 700.0,
        "heading": 90.0,
        "query_text": "What is that bright amber beacon rising in the east right now?",
    }

    print(f"Observer Location: Cherry Springs State Park (Lat {payload['latitude']}° N, Lon {abs(payload['longitude'])}° W)")
    print(f"Heading: Due East ({payload['heading']}°)")
    print(f"Spoken User Query: \"{payload['query_text']}\"")
    print("-" * 80)

    # 1. Test JSON reasoning endpoint
    json_resp = client.post("/api/whisper/json", data=payload)
    if json_resp.status_code != 200:
        print(f"❌ Error: {json_resp.text}")
        return

    data = json_resp.json()
    print("🧠 Conversational Reasoning Output (Gemma-2):")
    print(f"  \"{data['spoken_answer']}\"")
    print("-" * 80)
    print(f"📏 Spoken Word Count: {data['word_count']} words (Target: 35-45 words)")
    print(f"✨ Zero-Markdown Status: {'✅ 100% Audio Compliant (0 markdown tokens)' if not any(c in data['spoken_answer'] for c in ['*', '#', '_', '`']) else '❌ Markdown detected'}")
    print(f"🌟 Seeing Quality Index: {data['seeing_score']:.1f} / 10.0 ({data['antoniadi']})")
    print(f"💧 Dew Risk: {data['dew_risk'].upper()}")
    print(f"🔭 Bodies In Field of View: {', '.join(data['in_view_bodies'])}")

    # 2. Test Audio Streaming endpoint
    print("-" * 80)
    print("🎙️ Testing Voice Audio Streaming Endpoint (/api/whisper)...")
    audio_resp = client.post("/api/whisper", data=payload)
    assert audio_resp.status_code == 200
    media_type = audio_resp.headers.get("content-type")
    audio_size = len(audio_resp.content)
    print(f"🔊 Audio Stream Format: {media_type}")
    print(f"📦 Audio Payload Size: {audio_size:,} bytes")
    print(f"🏷️  Response Header 'X-Seeing-Score': {audio_resp.headers.get('X-Seeing-Score')}")
    print(f"🏷️  Response Header 'X-Visible-Count': {audio_resp.headers.get('X-Visible-Count')}")

    print("\n" + "=" * 80)
    print("✅ End-to-End Spoken Reasoning & Audio Pipeline verified successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
