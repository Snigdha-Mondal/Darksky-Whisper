# BACKLOG.md — DarkSky Whisper Engineering Backlog

> **Work Management Protocol**: Work is organized into phases. Each task is a small, verifiable slice. The agent executes one slice at a time. Items requiring Product Owner approval or external resources are flagged with 🔒.

---

## Phase 1: Core Physics & Offline Ephemeris Engine (Skyfield)
**Exit Goal**: A standalone, 100% offline Python engine that ingests `(latitude, longitude, timestamp)` and returns verified Altitude, Azimuth, and visibility for the Moon, 8 planets, major navigation stars, and seasonal constellations with $\pm 0.5^\circ$ accuracy.

- [x] **Task 1.1**: Initialize project scaffolding (`pyproject.toml`, `requirements.txt`, `.gitignore`, `.env.example`).
- [x] **Task 1.2**: Define Pydantic celestial schemas in `backend/app/schemas/sky_schema.py` (`CelestialBody`, `ObserverLocation`, `SkyFieldResponse`).
- [x] **Task 1.3**: Implement `backend/app/services/sky_engine.py` using Skyfield + NASA JPL DE421 ephemeris loader with local caching.
- [x] **Task 1.4**: Implement cardinal direction mapping, field-of-view filtering ($\pm 45^\circ$ heading), and horizon filtering ($\text{Alt} > 0^\circ$).
- [x] **Task 1.5**: Write unit tests in `tests/test_sky_engine.py` validating ephemeris calculations against known JPL horizons fixtures.
- [x] **Task 1.6**: Run end-to-end verification script and record live output evidence in [PROGRESS.md](PROGRESS.md).
- [ ] 🔒 **Phase 1 Checkpoint**: Review Phase 1 test coverage and celestial accuracy with Product Owner.

---

## Phase 2: Tabular Atmospheric Seeing & Dew Forecaster (TabPFN)
**Exit Goal**: Tabular model inference pipeline that ingests meteorological telemetry CSVs and outputs Seeing Quality Score (0–10), peak observation window, and dew risk warning.

- [x] **Task 2.1**: Define forecast schemas in `backend/app/schemas/forecast_schema.py` (`WeatherTelemetry`, `SeeingForecastResponse`).
- [x] **Task 2.2**: Create sample weather telemetry fixture in `tests/fixtures/sample_weather.csv` mirroring Open-Meteo hourly variables.
- [x] **Task 2.3**: Implement `backend/app/services/tabpfn_engine.py` with Prior Labs `TabPFNRegressor` and deterministic fallback heuristic.
- [x] **Task 2.4**: Implement Open-Meteo hourly weather telemetry fetcher with offline cache fallback.
- [x] **Task 2.5**: Write unit tests in `tests/test_tabpfn_engine.py` testing seeing score bounds, dew warnings, and offline fallback behavior.
- [x] **Task 2.6**: Run live tabular inference test on sample fixture and record evidence in [PROGRESS.md](PROGRESS.md).
- [ ] 🔒 **Phase 2 Checkpoint**: Review TabPFN prediction behavior and fallback rules with Product Owner.

---

## Phase 3: Conversational Reasoning & Audio Engine (Gemma-2 + ElevenLabs)
**Exit Goal**: Reasoning pipeline that fuses ephemeris data + seeing score + user query into a concise 35-word zero-markdown spoken response, with voice streaming via ElevenLabs.

- [x] **Task 3.1**: Create prompt template in `backend/app/services/gemma_agent.py` enforcing strict zero-markdown, spatial cues, and 35–45 word limit.
- [x] **Task 3.2**: Implement `backend/app/services/voice_engine.py` for ElevenLabs TTS streaming with local offline audio fallback.
- [x] **Task 3.3**: Implement `backend/app/services/stt_engine.py` for speech-to-text audio query transcription.
- [x] **Task 3.4**: Write unit tests in `tests/test_zero_markdown.py` with regex verification ensuring zero asterisks, bolding, or lists.
- [x] **Task 3.5**: Wire `/api/forecast` and `/api/whisper` endpoints in `backend/app/main.py`.
- [ ] 🔒 **Phase 3 Checkpoint**: Verify voice narration tone and ask before pushing.

---

## Phase 4: Screenless Zero-Aim Mobile PWA Client
**Exit Goal**: Responsive, dark-adapted web interface running face-down with single-tap anywhere touch listener, status aura, and OLED red canvas.

- [x] **Task 4.1**: Build `frontend/index.html` with minimalist structure and `#000000` / `#1a0505` color scheme.
- [x] **Task 4.2**: Implement `frontend/src/style.css` with peripheral status aura animation rings (listening green, computing amber, speaking blue).
- [x] **Task 4.3**: Implement `frontend/src/app.js` with full-screen tap-to-talk state machine, Web Audio recording, and speaker mic-muting.
- [x] **Task 4.4**: Configure `frontend/public/manifest.json` for standalone PWA mobile installation.
- [x] **Task 4.5**: Verify zero rhodopsin bleaching in dark mode and test tap responsiveness.
- [ ] 🔒 **Phase 4 Checkpoint**: Product Owner field test review of screenless touch-to-talk interface.

---

## Phase 5: Reusable Agent Skill Package (Open Standard)
**Exit Goal**: Self-contained `skills/celestial-whisper` package conforming to the Agent Skills Open Standard.

- [x] **Task 5.1**: Author `skills/celestial-whisper/SKILL.md` with YAML frontmatter, procedures, and hard rules.
- [x] **Task 5.2**: Add reference guides in `skills/celestial-whisper/references/` (`constellations.md`, `seeing-scale.md`).
- [x] **Task 5.3**: Add verification utility script in `skills/celestial-whisper/scripts/verify_ephemeris.py`.
- [x] **Task 5.4**: Run automated validation against Agent Skills specification.
- [ ] 🔒 **Phase 5 Checkpoint**: Review Agent Skill package metadata and open-source licensing.

---

## Phase 6: Gemma Fine-Tuning & Evaluation Benchmark (Tinker)
**Exit Goal**: Benchmark dataset and automated evaluation script demonstrating token reduction and zero-markdown compliance.

- [x] **Task 6.1**: Curate 75 spoken astronomy interaction pairs in `benchmarks/dataset/spoken_astronomy_pairs.jsonl`.
- [x] **Task 6.2**: Implement `benchmarks/run_benchmark.py` comparing base Gemma-2 vs Tinker fine-tuned weights.
- [x] **Task 6.3**: Generate quantitative comparison report in `benchmarks/benchmark_results.md`.
- [x] **Task 6.4**: Execute remote distributed LoRA fine-tuning run on Thinking Machines Tinker API (`scripts/train_tinker_lora.py`), achieving 68.3% loss reduction and saving results to `benchmarks/tinker_training_report.json`.
- [ ] 🔒 **Phase 6 Checkpoint**: Review benchmark metrics and Tinker fine-tuning spend with Product Owner.

---

## Phase 7: Sentry Tracing, Packaging & Render Deployment
**Exit Goal**: Production-ready deployment on Render with end-to-end Sentry Agent Tracing waterfalls.

- [x] **Task 7.1**: Instrument custom pipeline spans in `backend/app/telemetry/sentry_tracer.py`.
- [x] **Task 7.2**: Create production `Dockerfile` and `render.yaml` deployment manifest.
- [x] **Task 7.3**: Create comprehensive `README.md` and Apache-2.0 `LICENSE`.
- [x] **Task 7.4**: Draft DEV.to submission article in `docs/devto-submission-draft.md`.
- [ ] 🔒 **Phase 7 Checkpoint**: Product Owner authorization to deploy to Render and publish repository.
