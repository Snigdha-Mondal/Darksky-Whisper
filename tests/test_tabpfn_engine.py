"""Unit tests for TabPFN Seeing & Dew Point Forecaster."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import pytest

from backend.app.schemas.forecast_schema import (
    AntoniadiScale,
    DewRiskLevel,
    HourlyTelemetry,
)
from backend.app.services.tabpfn_engine import TabPFNSeeingEngine, tabpfn_engine

SAMPLE_CSV_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_weather.csv"


def test_dew_risk_levels():
    """Verify dew risk categorization and advisory warnings."""
    # Critical: ground cooling hits dew point
    risk_crit, warn_crit = tabpfn_engine.calculate_dew_risk(dew_point_depression=0.8, relative_humidity=96.0)
    assert risk_crit == DewRiskLevel.CRITICAL
    assert warn_crit is not None
    assert "dew" in warn_crit.lower()

    # High risk
    risk_high, warn_high = tabpfn_engine.calculate_dew_risk(dew_point_depression=2.0, relative_humidity=85.0)
    assert risk_high == DewRiskLevel.HIGH
    assert warn_high is not None

    # Low risk (warm dry afternoon)
    risk_low, warn_low = tabpfn_engine.calculate_dew_risk(dew_point_depression=8.0, relative_humidity=45.0)
    assert risk_low == DewRiskLevel.LOW
    assert warn_low is None


def test_antoniadi_scale_mapping():
    """Verify seeing score translation to Antoniadi astronomical scale."""
    assert tabpfn_engine.seeing_to_antoniadi(9.5) == AntoniadiScale.I
    assert tabpfn_engine.seeing_to_antoniadi(8.5) == AntoniadiScale.I
    assert tabpfn_engine.seeing_to_antoniadi(7.2) == AntoniadiScale.II
    assert tabpfn_engine.seeing_to_antoniadi(5.0) == AntoniadiScale.III
    assert tabpfn_engine.seeing_to_antoniadi(2.5) == AntoniadiScale.IV
    assert tabpfn_engine.seeing_to_antoniadi(1.0) == AntoniadiScale.V


def test_csv_telemetry_ingestion():
    """Verify parsing of standard Open-Meteo hourly weather CSV."""
    telemetries = tabpfn_engine.parse_csv_telemetry(SAMPLE_CSV_PATH)
    assert len(telemetries) == 24

    first = telemetries[0]
    assert first.temperature_2m == 18.5
    assert first.dew_point_2m == 9.2
    assert pytest.approx(first.dew_point_depression) == 9.3
    assert first.wind_shear == 4.3


def test_physical_seeing_score_bounds_and_physics():
    """Verify seeing scores remain bounded within 0.0-10.0 and respond to atmospheric stability."""
    telemetries = tabpfn_engine.parse_csv_telemetry(SAMPLE_CSV_PATH)

    for t in telemetries:
        score = tabpfn_engine.compute_physical_seeing(t)
        assert 0.0 <= score <= 10.0, f"Score {score} out of bounds for timestamp {t.timestamp}"

    # Nighttime clear window (00:00 - 03:00 UTC) with 0% clouds and low shear should be pristine (>= 8.0)
    night_hours = [t for t in telemetries if 0 <= t.timestamp.hour <= 3]
    for nh in night_hours:
        score = tabpfn_engine.compute_physical_seeing(nh)
        assert score >= 8.0, f"Expected pristine seeing at {nh.timestamp}, got {score}"

    # Overcast hour with heavy clouds (15:00 UTC) should have heavily degraded seeing
    cloudy = next(t for t in telemetries if t.cloud_cover_total >= 40.0)
    cloudy_score = tabpfn_engine.compute_physical_seeing(cloudy)
    assert cloudy_score < 7.0


def test_optimal_observation_window_detection():
    """Verify identification of peak observation window and optimal hours."""
    forecast = tabpfn_engine.get_forecast(
        latitude=41.6631,
        longitude=-77.8236,
        csv_fallback_path=SAMPLE_CSV_PATH,
    )

    assert forecast.peak_seeing_score >= 8.5
    assert "Peak:" in forecast.peak_observation_window
    assert any(p.is_optimal_window for p in forecast.hourly_forecast)


def test_offline_fallback_when_api_unreachable():
    """Verify that when Open-Meteo API raises a network error, system smoothly falls back to CSV fixture."""
    with patch.object(tabpfn_engine, "fetch_open_meteo_telemetry", side_effect=Exception("Network Timeout")):
        forecast = tabpfn_engine.get_forecast(
            latitude=37.7749,
            longitude=-122.4194,
            csv_fallback_path=SAMPLE_CSV_PATH,
        )

        assert forecast is not None
        assert "Fallback" in forecast.model_used
        assert len(forecast.hourly_forecast) == 24
        assert forecast.current_seeing_score > 0.0
