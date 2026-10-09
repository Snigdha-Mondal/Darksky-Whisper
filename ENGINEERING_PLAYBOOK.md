# ENGINEERING_PLAYBOOK.md — DarkSky Whisper Operating Manual

> This document acts as the Engineering Manager for DarkSky Whisper. It sets the rules, workflows, quality bars, and escalation paths for autonomous agent iterations.

---

## 1. The 9-Step Loop

Every engineering session traverses this loop once to produce **one small, verified slice**. Never a big bang.

```text
    ┌───────────┐
    │ 1. ORIENT │ ──> Read AGENTS.md, Playbook, PROGRESS.md, and Backlog
    └─────┬─────┘
          v
    ┌───────────┐
    │ 2. SELECT │ ──> Pick the next unblocked task (respect phase order & 🔒)
    └─────┬─────┘
          v
    ┌───────────┐
    │  3. PLAN  │ ──> Write a concise plan: target files, edits, test approach
    └─────┬─────┘
          v
    ┌───────────┐
    │  4. BUILD │ ──> Implement the minimal clean slice that achieves the goal
    └─────┬─────┘
          v
    ┌───────────┐
    │  5. TEST  │ ──> Run unit tests and execute live verification ("seen working")
    └─────┬─────┘
          v
    ┌───────────┐
    │ 6. REVIEW │ ──> Self-critique for bugs, secrets, markdown artifacts, standards
    └─────┬─────┘
          v
    ┌───────────┐
    │ 7. RECORD │ ──> Update PROGRESS.md and any associated spec files
    └─────┬─────┘
          v
    ┌───────────┐
    │ 8. COMMIT │ ──> Commit with a semantic message ("feat:", "fix:", "test:")
    └─────┬─────┘
          v
    ┌───────────┐
    │ 9. REFLECT│ ──> Log new backlog items, blockers, or lessons; prepare next pass
    └───────────┘
```

---

## 2. Roles & Escalation

| Role | Entity | Responsibilities |
|---|---|---|
| **Product Owner** | **Snigdha (Human)** | Sets priorities, approves checkpoints (🔒), handles budget, cloud keys, external publishing, and final acceptance. |
| **Engineering Manager** | **The Playbook (This file)** | Sets engineering standards, Definition of Ready/Done, boundaries, and validation requirements. |
| **Engineer** | **AI Agent** | Plans, codes, writes tests, runs live verification, reviews work, and maintains memory in docs. |

---

## 3. Source of Truth Hierarchy

When documents disagree, the higher tier strictly overrides the lower tier:

1. **What the User Says Now** *(Most trusted)*
2. **[PRD.md](PRD.md)** *(Product intent and user needs)*
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** *(System design & fixed technical decisions)*
4. **[ENGINEERING_PLAYBOOK.md](ENGINEERING_PLAYBOOK.md)** *(Engineering process & standards)*
5. **[BACKLOG.md](BACKLOG.md)** *(Concrete work items and phases)*
6. **Existing Code & Comments** *(Least trusted — can drift from specifications)*

### Conflict Resolution Rules
- **Never silently resolve a conflict**: If two docs disagree, halt and surface the discrepancy to the Product Owner with a recommended fix.
- **Never invent missing decisions**: If a detail is absent from the specs, propose an addition rather than making an unwritten assumption.
- **Do not re-argue settled decisions**: The [PROGRESS.md](PROGRESS.md) Decisions Log and ADRs are permanent records.

---

## 4. Phase Plan & Phase-by-Phase Autonomy

Build sequentially. Establish a thin, working end-to-end slice before polishing deep edge cases:

1. **Phase 1: Celestial Mechanics Engine (Skyfield + DE421)** — Deterministic offline Alt/Az math.
2. **Phase 2: Atmospheric Seeing Forecaster (TabPFN)** — Tabular inference on weather CSVs.
3. **Phase 3: Conversational Reasoning & Audio Engine (Gemma-2 + ElevenLabs)** — Spoken response synthesis with zero markdown.
4. **Phase 4: Screenless PWA Client** — Touch-to-talk, status aura, OLED deep red `#1a0505`.
5. **Phase 5: Agent Skills Open Standard Package** — Reusable `celestial-whisper` skill.
6. **Phase 6: Tinker Fine-Tuning & Evaluation Benchmark** — Curated dataset and latency/token comparisons.
7. **Phase 7: Sentry Tracing, Packaging & Deployment** — APM span waterfalls and Render deployment.

*Phase boundary rule*: The agent completes a phase, presents evidence of the exit goal working, and pauses for human sign-off before entering the next phase.

---

## 5. Task Management

- Work on **one task at a time**.
- Break large features into independent slices that can be finished, tested, and committed in a single iteration.
- **No stealth work**: If a bug or missing feature is discovered during a task, log it in [BACKLOG.md](BACKLOG.md) rather than expanding the current task's scope.

---

## 6. Checklists

### Definition of Ready (DoR)
Before writing code for a task:
- [ ] The outcome and success criteria are clearly articulated.
- [ ] All prerequisite tasks and dependencies are already implemented and tested.
- [ ] The slice is small enough to complete and verify within one session.
- [ ] Relevant specs ([specs/](specs/)) and architecture sections have been reviewed.

### Definition of Done (DoD)
Before marking a task complete:
- [ ] Implementation satisfies the acceptance criteria.
- [ ] Automated tests pass with clean exit codes.
- [ ] **Evidence of live execution** is recorded (real command output, observed coordinates, or test runs).
- [ ] No API keys, secrets, or sensitive tokens are committed.
- [ ] Docs, specs, and [PROGRESS.md](PROGRESS.md) are updated in the same commit.
- [ ] Git commit has a clean, conventional message.

---

## 7. Engineering Standards

- **Settings in Environment / Config**: Never hardcode API keys, lat/lon defaults, or thresholds. Centralize them in `backend/app/config.py` backed by `.env`.
- **Zero Markdown Rule for Spoken Strings**: Spoken outputs from Gemma must contain strictly zero markdown tokens (`*`, `_`, `#`, `- `, `**`). Any formatting artifacts cause speech synthesis glitches.
- **Local-First & Offline Resilient**: Skyfield ephemeris calculations must function with zero network access using downloaded JPL DE421 files.
- **Microphone Gating**: In audio pipelines, disable microphone listeners immediately upon audio playback initiation to prevent acoustic feedback loops.

---

## 8. Testing & Verification

- **"It compiles" is not "it works"**: Always execute code against realistic data fixtures (e.g. `tests/fixtures/sample_weather.csv` or live JPL horizons checks).
- **The Two-Try Rule**: If an integration test or client check fails twice, inspect the underlying service layer or direct API call rather than retrying blindly.
- **Get the signal, not the stream**: Run test commands with targeted filtering (e.g. `pytest tests/test_sky_engine.py -q`) rather than dumping unparsed logs.

---

## 9. Git & Commit Guidelines

- Work on clean commits: `feat: add skyfield alt-az celestial engine`, `test: add TabPFN seeing score regression tests`.
- Commit code and documentation together in the same commit to prevent doc drift.
- Never force push to shared branches without approval.

---

## 10. Stop Signs: When to Ask the Product Owner

```text
● GO: Do It Yourself
  • Pick and execute the next backlog slice within the active phase
  • Write unit tests and run verification scripts
  • Fix minor bugs within scope
  • Update documentation, specs, and PROGRESS.md
  • Make low-level implementation choices (and record them)

● PAUSE: Checkpoint (🔒)
  • Database schema or model changes
  • External service configuration or API additions
  • Security, authentication, or privacy considerations
  • End-of-phase milestone review
  • Unresolvable ambiguities between specs and code

● NEVER: Without Explicit Approval
  • Commit real API keys or sensitive user credentials
  • Execute real money transactions or paid deployments
  • Delete files or git history destructively
  • Add heavyweight unplanned third-party dependencies
  • Modify locked architectural decisions
```

---

## 11. Stuck Protocol

If a command fails twice or editing the same file makes no progress:
1. Immediately stop the loop.
2. Summarize what was attempted, the exact error observed, and the two most likely root causes.
3. Formulate a specific question with a recommended option for the Product Owner.

---

## 12. Memory & Session Continuity

Because context resets across agent sessions, repository docs act as the shared memory:
- **[PROGRESS.md](PROGRESS.md)** must have a dated entry after every slice.
- Record what was done, what was seen working, open items (flagged with 🔴), and the exact prompt or note for the next iteration.
- The Decisions Log captures every architectural or library choice with rationale.
