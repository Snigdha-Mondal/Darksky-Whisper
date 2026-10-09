# Specification: Screenless Audio UX & Mobile PWA

**File location in code**: `frontend/`

---

## 1. Objective
Provide a screenless, eyes-free audio observatory interface optimized for outdoor field use face-down in the grass, strictly preventing rhodopsin bleaching.

## 2. Interaction Design
1. **Single Tap Anywhere**:
   - `document.body` handles pointer/touch events.
   - Tap 1: Start audio capture; glanceable status aura pulses green.
   - Tap 2: Stop capture; aura pulses amber while FastAPI processes.
   - On Audio Receive: Plays spoken audio through speaker; aura glows calm blue.
2. **Microphone Gating**:
   - Web Audio recording input is forcibly muted/disabled during TTS audio playback to eliminate acoustic feedback.
3. **Glanceable Status Aura**:
   - Low-intensity, peripheral glowing rim.
   - Green = listening; Amber = processing; Blue = speaking.
4. **OLED Ultra-Deep Red Mode**:
   - Canvas background: `#000000`.
   - Text color: `#1a0505` (deep red $>650\text{ nm}$).
   - Zero high-luminance blue/white/green pixels emitted when face-up.
