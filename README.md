# 🌌 DarkSky Whisper

> **The screenless, eyes-free audio observatory guide powered by Gemma-2 and TabPFN.**  
> *Touch Grass Hackathon — Built with the DeftBench AI Agent Loop.*

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com)
[![TabPFN](https://img.shields.io/badge/Prior_Labs-TabPFN-purple.svg)](https://github.com/priorlabs/TabPFN)
[![Gemma-2](https://img.shields.io/badge/Google-Gemma--2-orange.svg)](https://ai.google.dev/gemma)
[![Sentry](https://img.shields.io/badge/Sentry-Agent_Tracing-red.svg)](https://docs.sentry.io)

---

## The Biological Problem

Human night vision depends on **rhodopsin**, a retinal photopigment in rod cells that takes 20 to 30 minutes in pitch darkness to fully regenerate. A single glance at a typical glowing smartphone screen instantly bleaches rhodopsin and resets night adaptation to zero.

Existing astronomy apps force users to look through a glowing glass rectangle at 3D virtual graphics. **DarkSky Whisper does the opposite: it turns the screen off.** Resting face-down on a blanket in the grass, it listens to natural questions, calculates real-time celestial mechanics completely offline, forecasts atmospheric seeing via tabular AI, and whispers guidance out loud through the phone speaker.

---

## How It Works (The 0-Screen Experience)

```text
┌───────────────────────┐
│ Observer on blanket   │
└───────────┬───────────┘
            │ Spoken query ("What is rising in the east?")
            v
┌───────────────────────┐
│ Phone (Face-Down)     │  Screenless tap anywhere, OLED deep-red fallback (#1a0505)
└───────────┬───────────┘
            │ Audio Blob + GPS / Compass
            v
┌───────────────────────┐
│ FastAPI Orchestrator  │  Render-hosted container
└───────────┬───────────┘
            ├──> [Faster-Whisper STT] ────> Spoken transcript
            ├──> [Skyfield Engine]   ────> Altitude & Azimuth (NASA JPL DE421 offline)
            └──> [TabPFN Forecaster] ────> Optical seeing score (0–10) & dew warning
                    │
                    v
┌───────────────────────┐
│ Gemma-2 Reasoning     │  Tinker fine-tuned: strictly 35 words, zero markdown tokens
└───────────┬───────────┘
            │ Spoken answer
            v
┌───────────────────────┐
│ ElevenLabs Voice      │  Calm observatory narrator audio stream
└───────────┬───────────┘
            │ Audio playback (phone mic temporarily muted)
            v
┌───────────────────────┐
│ Phone Speaker Out Loud│  Everyone on the blanket listens together under the real stars
└───────────────────────┘
```

---

## Operating System & Navigation

This repository is governed by the **DeftBench AI Agent Loop** system:

- 🚪 **[AGENTS.md](AGENTS.md)**: Front door for AI agents and human contributors; 8 golden rules and quick reference.
- 📋 **[ENGINEERING_PLAYBOOK.md](ENGINEERING_PLAYBOOK.md)**: The operating manual and engineering manager; 9-step loop, Ready/Done definitions, and stop signs.
- 🎯 **[PRD.md](PRD.md)**: Product requirements, target personas, scope, and "Touch Grass" principles.
- 🏗️ **[ARCHITECTURE.md](ARCHITECTURE.md)**: Technical shape, division of labor, and locked decisions.
- 📝 **[BACKLOG.md](BACKLOG.md)**: Phased backlog, small slices, and 🔒 human checkpoints.
- 🧠 **[PROGRESS.md](PROGRESS.md)**: Persistent memory, session log, and decisions log.
- 📐 **[specs/](specs/)**: Detailed specifications for ephemeris, seeing models, reasoning, and audio UX.
- 📚 **[docs/](docs/)**: ADRs, rhodopsin photochemistry science, and field tests.

---

## License

Licensed under the [Apache-2.0 License](LICENSE).
