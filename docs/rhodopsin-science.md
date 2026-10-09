# Biological Rationale: Rhodopsin Photochemistry & Night Vision

> **The Problem**: A single glance at a typical smartphone screen bleaches human retinal rhodopsin and resets night vision for 30 minutes.

---

## 1. Photopigment Kinetics
Human dark adaptation (scotopic vision) is mediated by rod photoreceptors containing **rhodopsin**. 

- In darkness, rhodopsin accumulates, sensitizing the eye to faint celestial objects (faint nebulae, star clusters, Milky Way dust lanes).
- Complete dark adaptation requires **20 to 30 minutes** in pitch darkness.
- Exposure to photopic light (broad-spectrum white, blue, or green light emitted by smartphone screens) causes immediate photoisomerization (bleaching) of 11-cis-retinal to all-trans-retinal.
- This bleaching resets dark adaptation instantly.

## 2. Spectral Safeguards (>650 nm)
Rod photoreceptors have virtually zero sensitivity to wavelengths above $650\text{ nm}$ (deep red). Cones remain mildly sensitive to red light, allowing navigation without bleaching rod rhodopsin.

DarkSky Whisper adheres to two strict biological safeguards:
1. **Screenless First**: Keep the screen completely off by resting face-down in the grass.
2. **OLED Ultra-Deep Red Fallback**: If lifted face-up, the display operates in monochromatic `#1a0505` red light at minimal luminance ($>650\text{ nm}$).
