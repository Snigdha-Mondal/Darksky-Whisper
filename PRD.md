# PRD.md — DarkSky Whisper Product Requirements Document

> **Vision**: DarkSky Whisper is the screenless observatory companion for open-sky exploration. When stargazing, looking at a smartphone screen bleaches retinal rhodopsin and ruins night vision for 30 minutes. DarkSky Whisper turns the screen completely off: resting face-down in the grass, it listens to spoken questions, calculates offline celestial mechanics, predicts atmospheric turbulence via tabular AI, and whispers guidance through the phone speaker.

---

## 1. Problem Statement

1. **Rhodopsin Destruction**: Human scotopic (night) vision depends on rhodopsin, which requires 20–30 minutes in pitch darkness to regenerate. A single glance at a typical smartphone screen resets night adaptation instantly.
2. **Screens Instead of the Cosmos**: Astronomy apps force users to look through a glowing glass rectangle at 3D virtual graphics, converting an awe-inspiring celestial outdoor experience into a screen simulation.
3. **Wilderness Connectivity Deadzones**: High-altitude trails and designated Dark Sky Parks have zero cellular reception. Cloud-tethered LLMs timeout and fail.
4. **Blindness to Atmospheric Turbulence**: Weather apps report "clear skies," but optical astronomical seeing depends on micro-turbulence across atmospheric boundaries, dew-point depression, and upper-level shear. Generic LLMs hallucinate these physics.

---

## 2. Target Personas

### 2.1 Casual Backyard Stargazers & Families
- **Behavior**: Spreading a blanket on lawns, rooftops, or campsites.
- **Pain Point**: Want to know what bright stars and planets are visible without passing a phone around or blinding everyone with screens.
- **Key Delight**: Shared speakerphone audio that whispers answers to everyone on the blanket.

### 2.2 Amateur Astronomers & Astrophotographers
- **Behavior**: Setting up telescopes, binoculars, or tripod mounts.
- **Pain Point**: Hands are occupied with focus dials and equatorial mounts; lens dew ruins sessions if unwarned.
- **Key Delight**: Seeing quality scores (0–10) and dew-point depression alerts before opening optics.

### 2.3 Wilderness Backpackers & Campers
- **Behavior**: Deep in backcountry parks with no cellular signal.
- **Pain Point**: Offline functionality is a mandatory prerequisite.
- **Key Delight**: Ephemeris and voice guidance functioning 100% offline.

---

## 3. Scope Specification

### 3.1 In-Scope (MVP)

#### A. Atmospheric Seeing & Dew Forecaster (TabPFN)
- Ingests hourly meteorological telemetry CSVs (Open-Meteo).
- Uses Prior Labs' **TabPFN** tabular foundation model to predict:
  - Seeing Quality Index (`0.0` to `10.0`, based on Antoniadi seeing scale).
  - Peak Observation Window tonight (hours with lowest upper-level turbulence).
  - Dew Condensation Risk (lens moisture warnings).

#### B. Offline Celestial Ephemeris Engine (Skyfield)
- Ingests `(latitude, longitude, timestamp)`.
- Calculates high-precision Altitude ($0^\circ$ to $90^\circ$) and Azimuth ($0^\circ$ to $360^\circ$) for:
  - Solar System: Moon (phase & illumination %) and all 8 planets.
  - Navigational Stars: Sirius, Betelgeuse, Rigel, Vega, Arcturus, Polaris.
  - Seasonal Constellations & Asterisms: Orion, Ursa Major, Cassiopeia, Taurus, Cygnus.
  - Active meteor shower radiants.
- Strictly filters out celestial objects below the horizon ($\text{Altitude} \le 0^\circ$).

#### C. Spoken Astronomical Reasoning (Gemma-2)
- Translates celestial coordinates into evocative, concise spoken English.
- **Strict constraints**:
  - Maximum 35–45 words (maximum 3 sentences).
  - Explicit spatial cues: cardinal direction and approximate altitude in degrees.
  - Strictly zero markdown, asterisks, bullet points, or numbering.

#### D. Screenless Zero-Aim Mobile PWA
- Defaults to running face-down on grass or picnic table.
- **Single-tap anywhere on screen** toggles push-to-talk listening.
- **Glanceable Status Aura**: Peripheral low-luminance glowing edge ring:
  - Green pulse: Listening.
  - Amber pulse: Computing ephemeris / TabPFN / LLM inference.
  - Calm blue: Whispering audio.
- **OLED Ultra-Deep Red Mode**: `#1a0505` red canvas at low luminance if flipped face-up, strictly preventing rhodopsin bleaching ($>650\text{ nm}$).

#### E. End-to-End Agent Observability (Sentry)
- Custom instrumentation spans for `tabpfn_seeing_prediction`, `skyfield_ephemeris_calculation`, `whisper_stt_transcription`, `gemma_llm_inference`, and `elevenlabs_tts_synthesis`.
- Waterfall latency and token tracking.

#### F. Agent Skills Open Standard Package
- Modular, portable agent skill in `skills/celestial-whisper/` adhering to the Agent Skills Open Standard.

#### G. Fine-Tuning & Evaluation Benchmark
- 75 curated astronomy spoken interaction pairs in `benchmarks/dataset/spoken_astronomy_pairs.jsonl`.
- Quantitative benchmark measuring token reduction, TTFT, and zero-markdown compliance.

---

### 3.2 Out-of-Scope (MVP)

- ❌ Augmented Reality (AR) camera overlays (violates screenless philosophy).
- ❌ Sub-arcsecond astrometric telescope motorized mount tracking.
- ❌ Cloud-only models without offline fallback capability.
- ❌ Persistent audio storage (user audio streams are processed in memory and discarded).

---

## 4. Physical & Sensory Product Principles ("Touch Grass")

1. **Face-Down First**: The system must be 100% usable without looking at the screen.
2. **Shared Speakerphone**: No earphones required; astronomy is a collective campfire experience.
3. **Hardware-Safe Audio Gating**: The microphone is forcibly muted during TTS playback to prevent self-triggering and feedback loops.
4. **Rhodopsin Safeguard**: No white, blue, or green light emitted at high luminance.

---

## 5. Hacktoberfest Target Categories

1. **Best Use of TabPFN ($200)**: Predicting optical seeing and dew risk from tabular telemetry.
2. **Best Use of Gemma ($200)**: Open-weight edge conversational reasoning.
3. **Best Use of Tinker ($200)**: Fine-tuning Gemma to eliminate markdown and cut TTFT by >60%.
4. **Best Use of Render ($200)**: Production FastAPI deployment via `render.yaml`.
5. **Best Use of ElevenLabs ($100)**: Calm observatory narrator voice synthesis.
6. **Best Use of Sentry Agent Tracing ($100)**: Full agent execution span waterfalls.
7. **Best Use of Backboard ($100)**: Model evaluation endpoint.
8. **Overall Hacktoberfest Winner ($250)**: Ultimate embodiment of "Touch Grass".
