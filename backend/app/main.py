"""FastAPI Orchestrator for DarkSky Whisper.

Coordinates offline orbital mechanics (Skyfield), atmospheric seeing regression (TabPFN),
spoken reasoning (Gemma-2), and voice synthesis streaming (ElevenLabs).
"""

from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from backend.app import __version__
from backend.app.config import settings
from backend.app.schemas.forecast_schema import SeeingForecastResponse
from backend.app.schemas.sky_schema import ObserverLocation, SkyFieldResponse
from backend.app.services.gemma_agent import gemma_agent
from backend.app.services.sky_engine import sky_engine
from backend.app.services.stt_engine import stt_engine
from backend.app.services.tabpfn_engine import tabpfn_engine
from backend.app.services.voice_engine import voice_engine
from backend.app.telemetry.sentry_tracer import sentry_tracer

# Initialize Sentry Agent Tracing if configured
sentry_tracer.setup()

app = FastAPI(
    title="DarkSky Whisper API",
    description="Eyes-free astronomical observatory guide powered by Gemma-2, TabPFN, and Skyfield.",
    version=__version__,
)

# CORS Middleware for PWA mobile client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Spoken-Answer", "X-Seeing-Score", "X-Visible-Count", "X-User-Transcript"],
)


@app.middleware("http")
async def add_no_cache_header(request, call_next):
    """Ensure mobile browsers never serve stale PWA assets or scripts."""
    response = await call_next(request)
    path = request.url.path
    if path == "/" or path.startswith("/src/") or path.startswith("/public/"):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@app.get("/api/health")
def health_check():
    """Health check endpoint detailing service availability."""
    return {
        "status": "healthy",
        "version": __version__,
        "ephemeris_engine": "Skyfield NASA JPL DE421 (100% Offline)",
        "seeing_engine": "TabPFN Tabular AI + Boundary Physics",
        "reasoning_engine": f"Gemma-2 ({settings.gemma_model_id}) + Zero-Markdown Filter",
        "voice_engine": "ElevenLabs Observatory Narrator (Streamed)",
        "telemetry": "Sentry Agent Tracing (Active)" if sentry_tracer.is_active else "Local Profiling (Active)",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/forecast", response_model=SeeingForecastResponse)
def get_seeing_forecast(
    latitude: float = Query(..., ge=-90.0, le=90.0, description="Observer latitude in decimal degrees"),
    longitude: float = Query(..., ge=-180.0, le=180.0, description="Observer longitude in decimal degrees"),
):
    """Predict tonight's Seeing Quality Index (0-10), Antoniadi scale, and dew condensation risk."""
    try:
        return tabpfn_engine.get_forecast(latitude=latitude, longitude=longitude)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Seeing forecast generation failed: {str(e)}")


@app.get("/api/sky", response_model=SkyFieldResponse)
def get_visible_sky(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    elevation_m: float = Query(default=0.0),
    heading: Optional[float] = Query(default=None, ge=0.0, lt=360.0),
):
    """Calculate Altitude and Azimuth coordinates for all celestial bodies above the horizon."""
    obs = ObserverLocation(
        latitude=latitude,
        longitude=longitude,
        elevation_m=elevation_m,
        heading=heading,
    )
    return sky_engine.calculate_sky(obs)


@app.post("/api/whisper")
async def whisper_audio_endpoint(
    latitude: float = Form(..., ge=-90.0, le=90.0),
    longitude: float = Form(..., ge=-180.0, le=180.0),
    elevation_m: float = Form(default=0.0),
    heading: Optional[float] = Form(default=None),
    query_text: Optional[str] = Form(default=None),
    audio_file: Optional[UploadFile] = File(default=None),
):
    """Main audio endpoint.

    Ingests spoken audio or text from phone resting face-down in the grass,
    computes ephemeris + seeing + reasoning, and returns spoken audio stream directly.
    """
    audio_bytes = None
    if audio_file:
        audio_bytes = await audio_file.read()

    # 1. Transcribe audio to text
    with sentry_tracer.trace_span(
        op="whisper.stt_transcription",
        description="Speech-to-text audio query transcription",
        data={"has_audio_file": bool(audio_file), "query_text_override": bool(query_text)},
    ):
        transcript = stt_engine.transcribe_audio(audio_bytes=audio_bytes, query_text=query_text)

    # 2. Offline Celestial Ephemeris (Skyfield)
    observer = ObserverLocation(
        latitude=latitude,
        longitude=longitude,
        elevation_m=elevation_m,
        heading=heading,
    )
    with sentry_tracer.trace_span(
        op="skyfield.ephemeris_calculation",
        description="NASA JPL DE421 offline orbital ephemeris math",
        data={"latitude": latitude, "longitude": longitude, "heading": heading},
    ):
        sky_data = sky_engine.calculate_sky(observer)

    # 3. Atmospheric Seeing Forecaster (TabPFN)
    seeing_data = None
    with sentry_tracer.trace_span(
        op="tabpfn.seeing_prediction",
        description="TabPFN atmospheric seeing regression and dew risk",
        data={"latitude": latitude, "longitude": longitude},
    ):
        try:
            seeing_data = tabpfn_engine.get_forecast(latitude=latitude, longitude=longitude)
        except Exception:
            pass

    # 4. Spoken Astronomical Reasoning (Gemma-2)
    with sentry_tracer.trace_span(
        op="gemma.reasoning_inference",
        description="Gemma-2 35-word zero-markdown spoken reasoning",
        data={"transcript": transcript, "visible_count": sky_data.total_visible_count},
    ):
        spoken_answer = gemma_agent.answer_query(
            user_query=transcript, sky_data=sky_data, seeing_data=seeing_data
        )

    # 5. Spoken Audio Synthesis (ElevenLabs with local offline fallback)
    with sentry_tracer.trace_span(
        op="elevenlabs.tts_synthesis",
        description="ElevenLabs observatory narrator audio streaming",
        data={"voice_id": settings.elevenlabs_voice_id, "word_count": len(spoken_answer.split())},
    ):
        speech_audio, media_type = voice_engine.stream_speech(spoken_answer)

    # Record aggregate transaction metrics
    sentry_tracer.record_pipeline_metrics(
        query=transcript,
        word_count=len(spoken_answer.split()),
        seeing_score=seeing_data.current_seeing_score if seeing_data else 8.0,
        visible_count=sky_data.total_visible_count,
        duration_ms=0.0,
    )

    # Return audio stream with custom debug metadata headers
    headers = {
        "X-Spoken-Answer": quote(spoken_answer),
        "X-User-Transcript": quote(transcript),
        "X-Seeing-Score": str(seeing_data.current_seeing_score if seeing_data else 8.0),
        "X-Visible-Count": str(sky_data.total_visible_count),
    }

    return Response(content=speech_audio, media_type=media_type, headers=headers)


@app.post("/api/whisper/json")
async def whisper_json_endpoint(
    latitude: float = Form(..., ge=-90.0, le=90.0),
    longitude: float = Form(..., ge=-180.0, le=180.0),
    elevation_m: float = Form(default=0.0),
    heading: Optional[float] = Form(default=None),
    query_text: Optional[str] = Form(default=None),
    audio_file: Optional[UploadFile] = File(default=None),
):
    """JSON metadata endpoint for evaluation, benchmarks, and structured inspection."""
    audio_bytes = None
    if audio_file:
        audio_bytes = await audio_file.read()

    with sentry_tracer.trace_span(op="whisper.stt_transcription", description="STT query transcription"):
        transcript = stt_engine.transcribe_audio(audio_bytes=audio_bytes, query_text=query_text)

    observer = ObserverLocation(
        latitude=latitude,
        longitude=longitude,
        elevation_m=elevation_m,
        heading=heading,
    )
    with sentry_tracer.trace_span(op="skyfield.ephemeris_calculation", description="Ephemeris calculation"):
        sky_data = sky_engine.calculate_sky(observer)

    with sentry_tracer.trace_span(op="tabpfn.seeing_prediction", description="TabPFN seeing prediction"):
        seeing_data = tabpfn_engine.get_forecast(latitude=latitude, longitude=longitude)

    with sentry_tracer.trace_span(op="gemma.reasoning_inference", description="Gemma reasoning inference"):
        spoken_answer = gemma_agent.answer_query(
            user_query=transcript, sky_data=sky_data, seeing_data=seeing_data
        )

    return {
        "transcript": transcript,
        "spoken_answer": spoken_answer,
        "word_count": len(spoken_answer.split()),
        "seeing_score": seeing_data.current_seeing_score,
        "antoniadi": seeing_data.current_antoniadi.value,
        "dew_risk": seeing_data.current_dew_risk.value,
        "total_visible_bodies": sky_data.total_visible_count,
        "in_view_bodies": [b.name for b in sky_data.visible_bodies_in_view],
        "is_astronomical_night": sky_data.is_astronomical_night,
    }


# Static frontend files
if FRONTEND_DIR.exists():
    src_dir = FRONTEND_DIR / "src"
    public_dir = FRONTEND_DIR / "public"
    if src_dir.exists():
        app.mount("/src", StaticFiles(directory=str(src_dir)), name="src")
    if public_dir.exists():
        app.mount("/public", StaticFiles(directory=str(public_dir)), name="public")

    @app.get("/")
    def serve_frontend_root():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return health_check()
