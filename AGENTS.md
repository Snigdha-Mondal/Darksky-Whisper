# AGENTS.md — DarkSky Whisper Front Door

> **Important**: Before performing any work in this repository, read the operating manual: [ENGINEERING_PLAYBOOK.md](ENGINEERING_PLAYBOOK.md).

---

## 1. What This Project Is

**DarkSky Whisper** is an eyes-free, local-first astronomical observatory companion that preserves human dark adaptation by keeping the screen completely off while resting face-down in the grass. It listens to natural spoken celestial questions, calculates offline orbital mechanics with Skyfield, predicts atmospheric seeing turbulence via TabPFN, reasons with fine-tuned Gemma-2, and whispers spoken answers through the phone speaker via ElevenLabs.

- Product intent, users, and scope: [PRD.md](PRD.md)
- Technical architecture and component design: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 2. The 8 Golden Rules

1. **Small, verified slices**: Build one small piece at a time. Never leave the build broken.
2. **Evidence over assertion**: "Done" means you executed the code and observed it working with real outputs.
3. **Respect the fixed decisions**: Changing any architectural standard requires explicit user approval.
4. **Use shared building blocks**: Abstract external providers (voice, LLM, weather) behind engine interfaces so the system remains resilient offline.
5. **Never commit secrets or spend money**: No API keys, credentials, or paid cloud resources without approval.
6. **Stop and ask when unclear or sensitive**: When facing ambiguity, security considerations, or schema changes, pause and ask.
7. **Keep docs in sync with code**: Docs ship in the same commit as code. Update [PROGRESS.md](PROGRESS.md) every session.
8. **Verify without drowning in output**: Extract high-signal error traces rather than dumping multi-megabyte log streams.

---

## 3. Fixed Decisions

| Domain | Locked Decision | Rationale |
|---|---|---|
| **Runtime & Language** | Python 3.10+ | Compatibility with Skyfield, TabPFN, PyTorch, and FastAPI |
| **Backend Framework** | FastAPI (ASGI) | Async streaming audio endpoints and OpenAPI documentation |
| **Celestial Ephemeris** | Skyfield (NASA JPL DE421) | 100% offline, deterministic sub-arcminute accuracy |
| **Atmospheric Seeing** | TabPFN (Prior Labs) | Tabular foundation model for seeing index (0–10) & dew risk |
| **Cognitive Reasoning** | Gemma-2 (Google Open-Weight) | Offline-capable, fine-tuned for 35-word zero-markdown spoken prose |
| **Voice Synthesis** | ElevenLabs (with local fallback) | Low-pitch calm observatory narrator; muted mic during playback |
| **Mobile Client** | Screenless PWA (Vanilla JS/CSS) | Zero-aim full-screen touch listener; OLED red mode (`#1a0505`) |
| **Agent Observability** | Sentry Agent Tracing | End-to-end span performance waterfalls (`tabpfn` → `skyfield` → `gemma` → `elevenlabs`) |
| **Deployment** | Render (`render.yaml`) | Containerized web service deployment |
| **Open License** | Apache-2.0 | Open-source foundation and Agent Skills Open Standard compliance |

---

## 4. Where to Find Things

| What do you need? | Document to open |
|---|---|
| Operating rules, checklists, and 9-step loop | [ENGINEERING_PLAYBOOK.md](ENGINEERING_PLAYBOOK.md) |
| Product vision, target users, and scope | [PRD.md](PRD.md) |
| Architecture, data flow, and components | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Current sprint, phased tasks, and checkpoints | [BACKLOG.md](BACKLOG.md) |
| Project memory, decision log, and session handoffs | [PROGRESS.md](PROGRESS.md) |
| Detailed specifications (ephemeris, seeing, voice, PWA) | [specs/README.md](specs/README.md) |
| Decision records, feature stories, build plans, manual tests | [docs/README.md](docs/README.md) |
| Agent Skills Open Standard package | [skills/celestial-whisper/SKILL.md](skills/celestial-whisper/SKILL.md) |
| Evaluation benchmark dataset and comparison | [benchmarks/benchmark_results.md](benchmarks/benchmark_results.md) |
