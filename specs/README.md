# Specifications Index (`specs/`)

> **Playbook Rule**: "One file per area. When the code changes one of these areas, the spec changes in the same commit. A doc that drifts from the code counts as a bug."

---

## Specification Areas

| Specification File | Domain | Key Responsibilities |
|---|---|---|
| [ephemeris_engine.md](ephemeris_engine.md) | Celestial Ephemeris & Geometry | Skyfield DE421 loader, coordinate transforms (Alt/Az), horizon filtering, constellation tracking |
| [seeing_forecast.md](seeing_forecast.md) | Atmospheric Tabular Forecasting | Open-Meteo hourly telemetry ingestion, TabPFN seeing score regression, dew risk warning |
| [spoken_reasoning.md](spoken_reasoning.md) | Conversational Synthesis & LLM | Gemma-2 prompt constraints, zero-markdown enforcement, spatial cue injection, 35-word brevity |
| [audio_ux.md](audio_ux.md) | Mobile Client & Screenless Audio | Single-tap anywhere listener, peripheral status aura, mic muting during playback, OLED red canvas |
