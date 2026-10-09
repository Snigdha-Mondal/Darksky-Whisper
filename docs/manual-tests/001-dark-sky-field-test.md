# Manual Test 001: Dark Sky Field & Rhodopsin Test

> **What automation cannot test**: Real outdoor sensory perception, screenless touch reliability on grass, and dark adaptation preservation.

---

## Pre-Conditions
- Smartphone loaded with DarkSky Whisper PWA or connected to local dev server.
- Outdoor night environment (backyard or dark park) after astronomical twilight.
- Phone resting face-down on a picnic blanket or grass.

---

## Test Checklist

- [ ] **Step 1: Face-Down Blind Tap**
  - Without looking at the phone, reach out and single-tap anywhere on the back/screen.
  - *Expected*: Subtle audio click / peripheral low-intensity green status aura indicates recording has started.
- [ ] **Step 2: Spoken Query**
  - Ask: *"What is that bright orange star rising in the east?"*
  - Tap once to finish.
  - *Expected*: Peripheral aura turns amber (processing).
- [ ] **Step 3: Audio Playback & Microphone Gating**
  - Listen to phone speaker.
  - *Expected*: Calm voice whispers response (identifying Jupiter / Aldebaran with altitude and seeing context). Microphone is muted during playback to prevent echo.
- [ ] **Step 4: Dark Vision Preservation**
  - Observe faint stars or the Milky Way immediately after the voice response finishes.
  - *Expected*: Night vision remains 100% adapted; no blinding white screen flashes occurred.
- [ ] **Step 5: Face-Up Red Canvas Inspection**
  - Turn phone face-up.
  - *Expected*: Display renders only deep dark red `#1a0505` on pitch black `#000000`. No blue, white, or green high-luminance pixels.
