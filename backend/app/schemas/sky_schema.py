"""Pydantic schemas for celestial ephemeris calculations and observer spatial context."""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class CelestialTargetType(str, Enum):
    PLANET = "planet"
    MOON = "moon"
    SUN = "sun"
    STAR = "star"
    CONSTELLATION = "constellation"
    METEOR_RADIANT = "meteor_radiant"


class ObserverLocation(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    elevation_m: float = Field(default=0.0, description="Observer elevation above sea level in meters")
    utc_time: Optional[datetime] = Field(default=None, description="Observation timestamp in UTC (defaults to now)")
    heading: Optional[float] = Field(default=None, ge=0.0, lt=360.0, description="Compass azimuth heading (0=N, 90=E)")


class CelestialBody(BaseModel):
    name: str = Field(..., description="Common celestial name (e.g., Jupiter, Vega)")
    target_type: CelestialTargetType = Field(..., description="Target category")
    altitude_deg: float = Field(..., description="Altitude above horizon in degrees (0 = horizon, 90 = zenith)")
    azimuth_deg: float = Field(..., ge=0.0, lt=360.0, description="Azimuth in degrees (0 = North, 90 = East, 180 = South)")
    cardinal_direction: str = Field(..., description="Compass cardinal sector (e.g., East, South-East)")
    apparent_magnitude: Optional[float] = Field(default=None, description="Visual apparent magnitude (lower = brighter)")
    distance_au: Optional[float] = Field(default=None, description="Distance from Earth in Astronomical Units")
    illumination_pct: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Lunar illuminated fraction %")
    in_field_of_view: bool = Field(default=False, description="True if within observer heading field of view (+/- 45 deg)")
    angular_separation_from_heading_deg: Optional[float] = Field(
        default=None, description="Angular separation between object azimuth and observer heading"
    )
    notes: Optional[str] = Field(default=None, description="Observational characteristics or visual cues")


class SkyFieldResponse(BaseModel):
    observer: ObserverLocation
    timestamp_utc: datetime
    sun_altitude_deg: float
    is_astronomical_night: bool = Field(
        ..., description="True if Sun is below -18 degrees, meaning full astronomical darkness"
    )
    moon: Optional[CelestialBody] = None
    visible_bodies_in_view: List[CelestialBody] = Field(
        default_factory=list, description="Visible bodies above horizon matching observer directional heading"
    )
    all_visible_bodies: List[CelestialBody] = Field(
        default_factory=list, description="All visible celestial bodies with Altitude > 0 degrees"
    )
    total_visible_count: int = Field(default=0, description="Count of bodies above horizon")
