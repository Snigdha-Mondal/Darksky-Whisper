# Specification: Celestial Ephemeris Engine

**File location in code**: `backend/app/services/sky_engine.py`  
**Data models**: `backend/app/schemas/sky_schema.py`

---

## 1. Objective
Calculate accurate real-time celestial coordinates (Altitude and Azimuth) for an observer given `(latitude, longitude, timestamp, heading)`, filtering out all subterranean bodies ($\text{Altitude} \le 0^\circ$) and prioritizing objects within the observer's field of view.

## 2. Requirements & Calculations
1. **Ephemeris Source**:
   - NASA JPL DE421 ephemeris loaded via `skyfield.api.load('de421.bsp')`.
   - Ephemeris file cached locally to ensure 100% offline functionality.
2. **Targets Computed**:
   - **Planets**: Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune.
   - **Moon**: Altitude, Azimuth, illumination percentage (phase), and distance.
   - **Sun**: Used to verify twilight / true astronomical darkness.
   - **Bright Stars**: Sirius, Betelgeuse, Rigel, Vega, Arcturus, Polaris, Aldebaran, Antares, Spica.
   - **Constellations & Asterisms**: Centers and bright asterism stars (Orion, Big Dipper / Ursa Major, Cassiopeia, Cygnus).
3. **Coordinate Filtering**:
   - `altitude > 0.0` degrees (above horizon).
   - If `heading` is supplied: calculate angular difference $\Delta = |\text{azimuth} - \text{heading}| \pmod{360^\circ}$; flag bodies with $\Delta \le 45^\circ$ as `in_field_of_view = True`.
4. **Accuracy Threshold**:
   - Altitude and Azimuth must match NASA JPL Horizons within $\pm 0.5^\circ$.
