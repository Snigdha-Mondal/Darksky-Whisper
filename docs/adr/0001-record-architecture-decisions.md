# ADR 0001: Architecture Decisions & Division of Labor

- **Status**: Accepted
- **Date**: 2026-10-09
- **Deciders**: Snigdha Mondal, Antigravity AI Agent

---

## Context
DarkSky Whisper is designed for outdoor stargazing in zero-connectivity wilderness environments and backyards. Looking at screens bleaches rhodopsin and ruins night vision. Previous attempts using generic LLMs suffer from:
1. Mathematical hallucinations of planetary positions.
2. Inability to calculate atmospheric micro-turbulence and dew risks.
3. Chatty responses with markdown tokens that ruin text-to-speech rendering.
4. Requiring cellular data in remote dark-sky locations.

## Decisions

1. **Deterministic Ephemeris (Skyfield + NASA JPL DE421)**:
   - Use Python Skyfield for all planetary and celestial calculations.
   - Cache DE421 ephemeris locally to guarantee 100% offline precision without internet.
2. **Tabular AI for Seeing (Prior Labs TabPFN)**:
   - Use TabPFN on hourly atmospheric telemetry to predict Seeing Quality (0–10) and dew risk.
   - Fall back to a deterministic physical heuristic when offline.
3. **Open-Weight Spoken Reasoning (Gemma-2 + Tinker)**:
   - Use Google Gemma-2 fine-tuned via Tinker to output strictly 35–45 word natural spoken prose without markdown formatting tokens.
4. **Voice Synthesis (ElevenLabs with Local Fallback)**:
   - Stream audio via ElevenLabs observatory narrator voice, with local offline audio fallback.
5. **Screenless PWA & OLED Red Canvas**:
   - Tap-anywhere screenless UX with peripheral status aura and `#1a0505` red canvas.
6. **Agent Observability (Sentry)**:
   - Instrument spans for tabular seeing, celestial calculation, STT, LLM inference, and TTS audio synthesis.

## Consequences
- Clean separation between mathematical physics, tabular statistical inference, and conversational reasoning.
- Reliable edge behavior in wilderness locations.
- Zero markdown syntax errors in TTS audio.
