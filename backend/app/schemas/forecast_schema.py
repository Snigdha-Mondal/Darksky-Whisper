"""Pydantic schemas for atmospheric seeing and dew point regression forecasting."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DewRiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class AntoniadiScale(str, Enum):
    I = "I - Perfect seeing without a quiver"
    II = "II - Good seeing with slight tremors"
    III = "III - Moderate seeing with noticeable air tremors"
    IV = "IV - Poor seeing with constant ripples"
    V = "V - Terrible seeing with boiling image"


class HourlyTelemetry(BaseModel):
    timestamp: datetime = Field(..., description="Hourly timestamp (UTC)")
    temperature_2m: float = Field(..., description="Surface temperature at 2m (Celsius)")
    dew_point_2m: float = Field(..., description="Dew point temperature at 2m (Celsius)")
    dew_point_depression: float = Field(
        ..., description="Difference between temperature and dew point (Celsius)"
    )
    relative_humidity_2m: float = Field(..., ge=0.0, le=100.0, description="Relative humidity (%)")
    cloud_cover_low: float = Field(default=0.0, ge=0.0, le=100.0, description="Low-level stratus clouds (%)")
    cloud_cover_mid: float = Field(default=0.0, ge=0.0, le=100.0, description="Mid-level altostratus clouds (%)")
    cloud_cover_high: float = Field(default=0.0, ge=0.0, le=100.0, description="High-level cirrus clouds (%)")
    cloud_cover_total: float = Field(default=0.0, ge=0.0, le=100.0, description="Total cloud cover (%)")
    wind_speed_10m: float = Field(..., ge=0.0, description="Surface wind speed at 10m (m/s)")
    wind_speed_100m: float = Field(..., ge=0.0, description="Boundary layer wind speed at 100m (m/s)")
    wind_shear: float = Field(
        ..., ge=0.0, description="Vertical wind shear magnitude between 10m and 100m (m/s)"
    )
    surface_pressure: float = Field(..., description="Atmospheric pressure at surface (hPa)")


class HourlySeeingPrediction(BaseModel):
    timestamp: datetime
    seeing_score: float = Field(
        ..., ge=0.0, le=10.0, description="Seeing Quality Index from 0.0 (terrible) to 10.0 (pristine)"
    )
    antoniadi_scale: AntoniadiScale = Field(..., description="Antoniadi astronomical seeing equivalent")
    dew_risk: DewRiskLevel = Field(..., description="Dew condensation risk level")
    is_optimal_window: bool = Field(
        default=False, description="True if within the highest quality observing window tonight"
    )
    summary: str = Field(..., description="Spoken-friendly one-line summary of sky conditions")


class SeeingForecastResponse(BaseModel):
    latitude: float
    longitude: float
    forecast_generated_at: datetime
    current_seeing_score: float = Field(..., ge=0.0, le=10.0)
    current_antoniadi: AntoniadiScale
    current_dew_risk: DewRiskLevel
    dew_warning: Optional[str] = Field(
        default=None, description="Concise lens moisture warning if dew risk is elevated"
    )
    peak_observation_window: str = Field(
        ..., description="Recommended hours for best viewing (e.g. '23:00 - 02:00 UTC')"
    )
    peak_seeing_score: float = Field(..., ge=0.0, le=10.0)
    hourly_forecast: List[HourlySeeingPrediction] = Field(
        default_factory=list, description="Hourly seeing predictions for the next 24 hours"
    )
    model_used: str = Field(
        default="TabPFN Atmospheric Regression",
        description="Name of the predictive model and fallback heuristic used",
    )
