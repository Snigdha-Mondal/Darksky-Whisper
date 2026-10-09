# PROGRESS.md — DarkSky Whisper Memory & Session Diary

> **Playbook Rule**: "You don't carry memory between sessions. The docs do." Every session must update this file with dated entries, real execution evidence, logged decisions, and notes for the next iteration.

---

## 1. Project Status Summary

- **Current Phase**: Phase 1 — Core Physics & Offline Ephemeris Engine (Skyfield)
- **Status**: 🟡 Phase 1 Complete / Awaiting Product Owner Sign-off (🔒 Checkpoint)
- **Active Task**: 🔒 Phase 1 Checkpoint: Review Phase 1 test coverage and celestial accuracy with Product Owner
- **Blockers**: None

---

## 2. Decisions Log

| Date | Decision | Rationale | Reference |
|---|---|---|---|
| 2026-10-09 | Adopt DeftBench AI Agent Loop architecture | Ensures structured autonomous iterations, strict memory persistence, and clear human checkpoints. | [ENGINEERING_PLAYBOOK.md](ENGINEERING_PLAYBOOK.md) |
| 2026-10-09 | Use Skyfield + NASA JPL DE421 for celestial math | 100% deterministic, offline sub-arcminute planetary coordinates without LLM hallucination. | [ARCHITECTURE.md](ARCHITECTURE.md) |
| 2026-10-09 | Use Prior Labs TabPFN for seeing & dew prediction | Foundation tabular model avoids manual model training on meteorological CSV features. | [PRD.md](PRD.md) |
| 2026-10-09 | Zero-Markdown rule for spoken Gemma strings | Formatting tokens (`*`, `_`, `#`, `-`) corrupt text-to-speech audio rendering. | [specs/spoken_reasoning.md](specs/spoken_reasoning.md) |
| 2026-10-09 | Screenless face-down mobile UX with OLED red fallback | Preserves retinal rhodopsin and 30-minute scotopic night vision adaptation. | [PRD.md](PRD.md) |
| 2026-10-09 | Replace elevenlabs SDK with direct lightweight HTTP client | ElevenLabs official SDK triggers Windows MAX_PATH length limits (>260 chars) on Windows paths. | [requirements.txt](requirements.txt) |
| 2026-10-09 | Use --no-gpg-sign on automated agent git commits | Avoids headless agent hanging on interactive GPG pinentry prompts. | [ENGINEERING_PLAYBOOK.md](ENGINEERING_PLAYBOOK.md) |

---

## 3. Session Log

### Session 2 — 2026-10-09 (Phase 1: Celestial Ephemeris Engine)
- **Goal**: Implement and verify 100% offline celestial ephemeris engine with Skyfield & NASA JPL DE421.
- **What was done**:
  1. Configured Python 3.13 `.venv` with `skyfield`, `numpy`, `scipy`, `pydantic`, `fastapi`, and `pytest`.
  2. Implemented [backend/app/schemas/sky_schema.py](backend/app/schemas/sky_schema.py) (`CelestialBody`, `ObserverLocation`, `SkyFieldResponse`).
  3. Implemented [backend/app/services/sky_engine.py](backend/app/services/sky_engine.py) using Skyfield with local JPL DE421 caching, 16-point cardinal mapping, and FOV filtering.
  4. Created [tests/test_sky_engine.py](tests/test_sky_engine.py) covering 8 automated test cases.
  5. Created [scripts/verify_ephemeris.py](scripts/verify_ephemeris.py) for real-world dark sky park verification.
- **Evidence Seen Working**:
  - `pytest tests/test_sky_engine.py` passed all 8/8 tests in 8.75s:
    - Polaris altitude test confirmed matching observer latitude within 1.5 degrees.
    - Horizon filtering strictly verified (`altitude > 0` for all returned bodies).
    - Compass heading wraparound verified (e.g., 350° to 10° = 20°).
    - Astronomical night threshold confirmed (Sun $\le -18^\circ$).
  - `python scripts/verify_ephemeris.py` executed for Cherry Springs State Park (Lat 41.6631° N, Lon 77.8236° W) at 02:30 UTC:
    - Sun altitude: -41.94° (Astronomical night: YES).
    - Total visible bodies: 13. In field of view facing East: 5 (Pleiades at Alt 23.8°, Uranus at Alt 17.4°, Aldebaran at Alt 10.2°, Capella at Alt 22.1°, Saturn at Alt 40.5°).
    - Top 5 brightest visible across sky: Vega (Mag +0.03), Capella (+0.08), Saturn (+0.36), Altair (+0.77), Aldebaran (+0.85).
- **Flagged Issues (🔴)**: None.

### Session 1 — 2026-10-09 (System Bootstrapping)
- **Goal**: Scaffold the complete DeftBench AI Agent Loop operating system for DarkSky Whisper.
- **What was done**: Created all foundational docs ([AGENTS.md](AGENTS.md), [ENGINEERING_PLAYBOOK.md](ENGINEERING_PLAYBOOK.md), [PRD.md](PRD.md), [ARCHITECTURE.md](ARCHITECTURE.md), [BACKLOG.md](BACKLOG.md), [PROGRESS.md](PROGRESS.md), `specs/`, `docs/`).
- **Evidence**: Initial commit created cleanly.
- **Flagged Issues (🔴)**: None.

---

## 4. Known Issues & Open Questions

- 🔴 None currently.

---

## 5. Notes for the Next Iteration

> **Standard Boot Sequence for Next Session**:
> 1. Review 🔒 Phase 1 Checkpoint with Product Owner.
> 2. Once approved, proceed to Phase 2: Tabular Atmospheric Seeing & Dew Forecaster (TabPFN).
> 3. Active task will be **Task 2.1**: Define forecast schemas in `backend/app/schemas/forecast_schema.py`.

