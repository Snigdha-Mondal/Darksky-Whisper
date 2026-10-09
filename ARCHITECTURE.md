# ARCHITECTURE.md — DarkSky Whisper System Architecture

> **Purpose**: Defines the technical components, communication pipelines, division of computational labor, and locked design choices for DarkSky Whisper.

---

## 1. High-Level Architecture Diagram

```text
┌────────────────────────────────────────────────────────┐
│               Outdoor Stargazer on Blanket             │
└───────────────────────────┬────────────────────────────┘
                            │ Spoken query ("What is rising in the east?")
                            v
┌────────────────────────────────────────────────────────┐
│             Mobile PWA Client (Face-Down)              │
│  - Single tap anywhere to record / tap to stop        │
│  - Web Audio API capturing audio/webm                  │
│  - Geolocation (Lat/Lon) + DeviceOrientation (Heading) │
│  - OLED red-mode canvas (#1a0505)                      │
│  - Glanceable peripheral status aura                   │
└───────────────────────────┬────────────────────────────┘
                            │ HTTP POST /api/whisper (Audio Blob + Coords)
                            v
┌────────────────────────────────────────────────────────┐
│             FastAPI Backend Orchestrator               │
│  - Containerized deployment on Render                  │
│  - Sentry Agent Tracing span instrumentation           │
└────────┬───────────────────┬───────────────────┬───────┘
         │                   │                   │
         v                   v                   v
┌──────────────────┐ ┌─────────────────┐ ┌───────────────┐
│ Faster-Whisper   │ │ Skyfield Engine │ │ TabPFN Engine │
│ Speech-to-Text   │ │ NASA JPL DE421  │ │ Atmospheric   │
│ STT Audio Engine │ │ Offline Alt/Az  │ │ Seeing Model  │
└────────┬─────────┘ └───────┬─────────┘ └───────┬───────┘
         │ Transcript        │ Visible Bodies    │ Seeing Score
         └─────────────┬─────┴───────────────────┘
                       v
         ┌───────────────────────────────┐
         │ Gemma-2 Reasoning Engine      │
         │ - Tinker Fine-Tuned           │
         │ - Strict 35-word prose        │
         │ - Zero markdown formatting    │
         └─────────────┬─────────────────┘
                       │ Spoken response text
                       v
         ┌───────────────────────────────┐
         │ ElevenLabs Voice Engine       │
         │ - Low-pitch calm narrator     │
         │ - Fallback local WAV synth    │
         └─────────────┬─────────────────┘
                       │ Audio stream response (audio/mpeg)
                       v
┌────────────────────────────────────────────────────────┐
│        Mobile Phone Speaker (Mic Forcibly Muted)       │
└────────────────────────────────────────────────────────┘
```

---

## 2. Division of Labor

We strictly separate mathematical calculation, tabular statistical inference, and natural language synthesis:

| Domain | Responsible Engine | Why This Engine? |
|---|---|---|
| **Orbital Mechanics** | **Skyfield (DE421)** | Deterministic ephemeris math. LLMs cannot compute sub-arcminute planetary coordinates without hallucination. |
| **Atmospheric Physics** | **TabPFN (Prior Labs)** | Non-linear atmospheric boundary turbulence, shear, and dew prediction from raw hourly CSV telemetry without manual retraining. |
| **Conversational Lore** | **Gemma-2** | Natural language synthesis, translating coordinates into spatial guidance (*"Look 30 degrees up in the east"*). |
| **Audio Formatting** | **Tinker Fine-Tuning** | Strips markdown, asterisks, and preamble at the weight level, reducing TTFT by >60% and ensuring 100% TTS compliance. |
| **Acoustic Delivery** | **ElevenLabs** | Campfire-style audio narration allowing the user's phone to remain face-down on the grass. |
| **Agent Observability** | **Sentry** | End-to-end trace spans recording performance across all subsystem boundaries. |

---

## 3. Component Breakdown

### 3.1 Backend Service Layer (`backend/app/services/`)

- **`sky_engine.py`**:
  - Uses `skyfield.api` with the NASA JPL DE421 ephemeris file.
  - Given `(lat, lon, utc_now, heading)`:
    - Calculates exact Altitude and Azimuth for Moon, Sun, 8 planets, major navigation stars, and constellations.
    - Filters out objects below horizon ($\text{Altitude} \le 0^\circ$).
    - Isolates objects within observer's directional field of view ($\text{Azimuth} \pm 45^\circ$).
- **`tabpfn_engine.py`**:
  - Fetches or ingests hourly meteorological CSV (Open-Meteo).
  - Normalizes boundary layer variables: cloud layers (low/mid/high), relative humidity, dew-point depression, wind speeds at 10m & 100m, surface pressure.
  - Generates Seeing Quality Index (`0.0` to `10.0`) and Dew Risk Flag (`LOW`, `MODERATE`, `HIGH`).
- **`gemma_agent.py`**:
  - Injects observer context, visible bodies, and seeing scores into a hardened zero-markdown prompt.
  - Executes local Gemma-2 (or API adapter) returning clean 35–45 word spoken text.
- **`voice_engine.py`**:
  - Converts text to speech using ElevenLabs API with an observatory narrator voice.
  - Includes local offline TTS fallback (e.g. `pyttsx3` or pre-synthesized WAV) when offline in wilderness parks.
- **`stt_engine.py`**:
  - Ingests audio blobs via `faster-whisper` (or local fallback) and transcribes spoken user query.

### 3.2 Telemetry & Observability (`backend/app/telemetry/`)

- **`sentry_tracer.py`**:
  - Wraps each pipeline stage in custom Sentry spans:
    - `span("tabpfn_seeing_prediction")`
    - `span("skyfield_ephemeris_calculation")`
    - `span("whisper_stt_transcription")`
    - `span("gemma_llm_inference")`
    - `span("elevenlabs_tts_synthesis")`
  - Records duration, input tokens, output tokens, and seeing scores.

### 3.3 Frontend Client (`frontend/`)

- **Face-Down & Screenless UX**:
  - Full-screen click/touch event listener (`document.body`).
  - MediaRecorder API captures microphone audio on first tap, completes on second tap.
  - Automatically suppresses microphone recording whenever audio response is playing through speaker.
- **Glanceable Status Aura**:
  - Minimal CSS border/radial-gradient ring visible from side/peripheral angles without illuminating the sky.
- **OLED Deep Red Safeguard**:
  - Background `#000000`, text `#1a0505` at minimum brightness to preserve retinal rhodopsin.

---

## 4. Fixed Architectural Decisions

| Decision | Selection | Rationale |
|---|---|---|
| **Programming Language** | Python 3.10+ | Scientific libraries (Skyfield, TabPFN, PyTorch) require stable Python. |
| **API Architecture** | FastAPI + Uvicorn | Async audio streaming, native Pydantic validation, OpenAPI specs. |
| **Ephemeris Source** | NASA JPL DE421 | Compact (~16MB), standard planetary ephemeris, 100% offline. |
| **Tabular Predictor** | TabPFN (Prior Labs) | Zero hyperparameter tuning required for tabular regression on atmospheric telemetry. |
| **LLM Model Family** | Google Gemma-2 | Open weights, excellent spatial reasoning, offline deployable. |
| **Speech-to-Text** | Faster-Whisper / Web Speech | Fast edge STT running locally or via lightweight endpoint. |
| **Hosting Platform** | Render (`render.yaml`) | Containerized deployment using Hacktoberfest $50 promo credit. |
| **Observability** | Sentry Agent Tracing | Real-time waterfall tracing across tabular, ephemeris, LLM, and TTS spans. |

---

## 5. Security & Privacy Guarantees

1. **Ephemeral Voice Audio**: Spoken audio received from the client is processed in memory and never written to permanent disk storage.
2. **No Hardcoded Secrets**: All tokens (ElevenLabs, Sentry, HuggingFace) are ingested strictly via environment variables.
3. **Open License**: Licensed under Apache-2.0 to support the Agent Skills Open Standard.
