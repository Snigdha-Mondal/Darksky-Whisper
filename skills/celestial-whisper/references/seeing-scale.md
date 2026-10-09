# Atmospheric Seeing, Optical Turbulence & Dew Risk Reference

This reference manual documents astronomical seeing scales, boundary-layer turbulence mechanics, and optics condensation physics for the `celestial-whisper` agent skill.

---

## 1. The Antoniadi Seeing Scale

Created by Eugène Michel Antoniadi at the Meudon Observatory in 1909, this five-tier scale evaluates optical atmospheric turbulence for planetary and double-star observation:

| Scale | Roman Numeral | Scientific Description | Observational Quality | Visual Appearance at 200× Magnification |
|---|---|---|---|---|
| **I** | **Class I** | Perfect seeing without a quiver | Exceptional / Space-grade | Planetary discs appear laser-etched; Encke division in Saturn's rings visible; Cassini division jet-black and motionless. |
| **II** | **Class II** | Good seeing with slight tremors | Fine / Very Good | Planetary details crisp with momentary quivers lasting a fraction of a second; Jupiter's Great Red Spot festoons sharp. |
| **III** | **Class III** | Moderate seeing with noticeable air tremors | Average / Fair | Intermittent ripples across planetary limbs; fine detail washed out, but major belts and polar hoods readily seen. |
| **IV** | **Class IV** | Poor seeing with constant ripples | Degraded / Sub-optimal | Image constantly agitated like looking through running water; stars bloated into shimmering discs without distinct Airy rings. |
| **V** | **Class V** | Terrible seeing with boiling image | Severe / Unusable | Planetary discs boil and deform continuously; impossible to achieve fine focus; only wide-field lunar or deep-sky targets viable. |

---

## 2. The Pickering Seeing Scale (1 to 10)

Developed by William Henry Pickering using a 5-inch refractor, this scale classifies seeing based on the diffraction pattern of a 2nd-magnitude star at the focal plane:

1. **Pickering 1**: Star image is twice or more the diameter of the third diffraction ring; star is continuously in motion.
2. **Pickering 2**: Image is twice diameter of third ring; occasional momentary quivers.
3. **Pickering 3**: Image about diameter of third ring; central peak blurred.
4. **Pickering 4**: Central Airy disc visible; rings in violent irregular motion.
5. **Pickering 5**: Airy disc always visible; ring arcs visible for ~50% of the time.
6. **Pickering 6**: Airy disc visible; complete diffraction rings appear intermittently.
7. **Pickering 7**: Disc sharp; inner ring complete and stationary; outer rings fractured.
8. **Pickering 8**: Disc sharp; inner ring complete and steady; second ring steady for long intervals.
9. **Pickering 9**: Inner and outer rings motionless; occasional fleeting ripples.
10. **Pickering 10**: Perfect, motionless diffraction pattern; concentric Airy rings textbook-perfect.

---

## 3. DarkSky Whisper 0–10 Seeing Quality Index Mapping

DarkSky Whisper translates meteorological variables and TabPFN regression output to a calibrated 0.0–10.0 Seeing Quality Index:

$$\text{Seeing Score} = 10.0 \times \left(1.0 - \min(1.0, \frac{\text{Turbulence Penalty}}{10.0})\right)$$

| Score Range | Antoniadi Equivalent | Pickering Equivalent | Atmospheric Condition | Recommended Target |
|---|---|---|---|---|
| **8.5 – 10.0** | Class I | Pickering 9–10 | Laminar jet stream, zero wind shear | High-magnification planetary (Saturn, Jupiter, Mars at 250×+) |
| **7.0 – 8.4** | Class II | Pickering 7–8 | Calm boundary layer, light ground breeze | Planetary & close binary stars (Castor, Porrima) |
| **5.0 – 6.9** | Class III | Pickering 5–6 | Moderate upper-tropospheric wind shear | Lunar maria, brighter Messier deep-sky objects |
| **3.0 – 4.9** | Class IV | Pickering 3–4 | Active thermal currents, gusty surface | Wide-field open clusters (Pleiades, Double Cluster) |
| **0.0 – 2.9** | Class V | Pickering 1–2 | Rapid front passage, boiling boundary layer | Naked-eye constellation orientation only |

---

## 4. Dew Point Depression & Condensation Hazards

### Dew Point Depression Definition
Dew Point Depression ($\Delta T_{\text{dew}}$) is the algebraic difference between ambient air temperature ($T$) and dew point temperature ($T_d$):

$$\Delta T_{\text{dew}} = T - T_d$$

As radiative cooling causes telescope optics and camera sensor lenses to drop below ambient air temperature, water vapor condenses once optical glass reaches $T_d$.

### Hazard Classification
* **Critical Hazard** ($\Delta T_{\text{dew}} < 1.5^\circ\text{C}$): Rapid condensation on Schmidt corrector plates, refractor objectives, and eyepiece lenses within 15 minutes. Immediate activation of dew heater strips or dew shields required.
* **High Hazard** ($1.5^\circ\text{C} \le \Delta T_{\text{dew}} < 3.0^\circ\text{C}$): Condensation expected within 45–60 minutes. Keep dew heaters on medium duty cycle.
* **Moderate Hazard** ($3.0^\circ\text{C} \le \Delta T_{\text{dew}} < 5.0^\circ\text{C}$): Light condensation possible on grass-level equipment; telescope tubes safe with standard passive dew shield.
* **Low Hazard** ($\Delta T_{\text{dew}} \ge 5.0^\circ\text{C}$): Dry desert air or brisk gentle breeze preventing thermal saturation. Passive dew shields sufficient.

---

## 5. Spoken Phrasing Guidelines for Seeing & Dew

When formulating guidance for observers under dark skies, follow these spoken templates:

* **High Seeing + Low Dew**:
  *"Atmospheric seeing is rated [Score] out of ten with class one stability. The night sky is calm and dry, ideal for resolving fine planetary details."*
* **High Seeing + Critical Dew**:
  *"Atmospheric seeing is rated [Score] out of ten with steady planetary views. However, critical humidity threatens lens fogging, so activate your dew heaters."*
* **Low Seeing**:
  *"Atmospheric seeing is rated [Score] out of ten with noticeable ripples through the boundary layer. Focus on wide-field star clusters tonight rather than high magnification."*
