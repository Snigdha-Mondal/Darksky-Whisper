# Specification: Atmospheric Seeing & Dew Forecaster

**File location in code**: `backend/app/services/tabpfn_engine.py`  
**Data models**: `backend/app/schemas/forecast_schema.py`

---

## 1. Objective
Ingest hourly meteorological telemetry from Open-Meteo and use Prior Labs' TabPFN tabular foundation model to predict tonight's Seeing Quality Index (0.0 to 10.0), identify the optimal observation window, and assess dew condensation risk.

## 2. Telemetry Feature Vector
From Open-Meteo hourly CSV / JSON:
- `cloud_cover_high` (%)
- `cloud_cover_mid` (%)
- `cloud_cover_low` (%)
- `relative_humidity_2m` (%)
- `dew_point_depression` ($^\circ\text{C} = T_{\text{ambient}} - T_{\text{dew}}$)
- `wind_speed_10m` (m/s)
- `wind_speed_100m` (m/s)
- `surface_pressure` (hPa)

## 3. TabPFN Regression & Fallback
1. **TabPFN Model**: Prior Labs `TabPFNRegressor` fitted on verified astronomical turbulence datasets (or calibrated seeing metrics).
2. **Offline / Fallback Heuristic**: If TabPFN or network telemetry is unavailable, calculate seeing score deterministically:
   - High humidity and boundary shear degrade score.
   - Cloud cover > 40% bounds seeing score below 3.0.
3. **Seeing Score Scale (Antoniadi equivalent)**:
   - 8.5 – 10.0: Pristine (stable planetary discs)
   - 6.5 – 8.4: Good (faint nebulae visible)
   - 4.0 – 6.4: Moderate (noticeable twinkling)
   - 0.0 – 3.9: Poor (heavy shear / cloud cover)
4. **Dew Risk Metric**:
   - `HIGH` if dew-point depression $\le 1.5^\circ\text{C}$ and relative humidity $\ge 85\%$.
   - `MODERATE` if dew-point depression $\le 3.0^\circ\text{C}$.
   - `LOW` otherwise.
