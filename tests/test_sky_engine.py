"""Unit tests for the Skyfield Celestial Ephemeris Engine."""

from datetime import datetime, timezone
import pytest

from backend.app.schemas.sky_schema import (
    CelestialTargetType,
    ObserverLocation,
    SkyFieldResponse,
)
from backend.app.services.sky_engine import SkyEngine, sky_engine


def test_azimuth_to_cardinal_mapping():
    """Verify azimuth compass mapping for exact cardinal points."""
    assert sky_engine.azimuth_to_cardinal(0.0) == "North"
    assert sky_engine.azimuth_to_cardinal(360.0) == "North"
    assert sky_engine.azimuth_to_cardinal(90.0) == "East"
    assert sky_engine.azimuth_to_cardinal(180.0) == "South"
    assert sky_engine.azimuth_to_cardinal(270.0) == "West"
    assert sky_engine.azimuth_to_cardinal(45.0) == "Northeast"
    assert sky_engine.azimuth_to_cardinal(135.0) == "Southeast"
    assert sky_engine.azimuth_to_cardinal(225.0) == "Southwest"
    assert sky_engine.azimuth_to_cardinal(315.0) == "Northwest"


def test_angular_separation_wraparound():
    """Verify angular distance between azimuth bearings with circular 360-degree wrap."""
    # Standard separation
    assert pytest.approx(sky_engine.angular_separation(90.0, 110.0)) == 20.0
    assert pytest.approx(sky_engine.angular_separation(110.0, 90.0)) == 20.0

    # Wrap across north meridian (350 deg and 10 deg -> 20 deg separation)
    assert pytest.approx(sky_engine.angular_separation(350.0, 10.0)) == 20.0
    assert pytest.approx(sky_engine.angular_separation(5.0, 355.0)) == 10.0

    # Opposite sides of horizon
    assert pytest.approx(sky_engine.angular_separation(0.0, 180.0)) == 180.0


def test_polaris_altitude_matches_observer_latitude():
    """Fundamental celestial mechanic: Polaris altitude approximately matches observer latitude in Northern Hemisphere."""
    # San Francisco (Lat 37.7749 N, Lon -122.4194 W)
    obs = ObserverLocation(
        latitude=37.7749,
        longitude=-122.4194,
        utc_time=datetime(2026, 10, 9, 5, 0, 0, tzinfo=timezone.utc),
        heading=0.0,  # Looking North
    )
    result = sky_engine.calculate_sky(obs)

    polaris = next((b for b in result.all_visible_bodies if b.name == "Polaris"), None)
    assert polaris is not None, "Polaris should always be visible in San Francisco"
    assert polaris.cardinal_direction == "North"
    # Polaris is ~0.7 degrees offset from the exact celestial pole
    assert pytest.approx(polaris.altitude_deg, abs=1.5) == 37.77
    assert polaris.in_field_of_view is True


def test_horizon_filtering_strictly_above_zero():
    """Verify that every body reported in all_visible_bodies has altitude strictly > 0 degrees."""
    obs = ObserverLocation(
        latitude=51.5074,
        longitude=-0.1278,
        utc_time=datetime(2026, 10, 9, 22, 0, 0, tzinfo=timezone.utc),
    )
    result = sky_engine.calculate_sky(obs)

    for body in result.all_visible_bodies:
        assert body.altitude_deg > 0.0, f"{body.name} was returned with altitude {body.altitude_deg} <= 0"


def test_field_of_view_filtering():
    """Verify that in_field_of_view is True only for bodies within +/- 45 degrees of observer heading."""
    # Observer looking due East (heading = 90 deg)
    obs = ObserverLocation(
        latitude=34.0522,
        longitude=-118.2437,
        utc_time=datetime(2026, 10, 9, 4, 0, 0, tzinfo=timezone.utc),
        heading=90.0,
    )
    result = sky_engine.calculate_sky(obs)

    for body in result.all_visible_bodies:
        sep = body.angular_separation_from_heading_deg
        assert sep is not None
        if sep <= 45.0:
            assert body.in_field_of_view is True
            assert body in result.visible_bodies_in_view
        else:
            assert body.in_field_of_view is False
            assert body not in result.visible_bodies_in_view


def test_astronomical_night_detection():
    """Verify astronomical twilight detection: Sun <= -18 deg means astronomical night."""
    # Local noon in Greenwich (Sun is high in sky, Alt > 0)
    daytime_obs = ObserverLocation(
        latitude=51.4769,
        longitude=0.0,
        utc_time=datetime(2026, 10, 9, 12, 0, 0, tzinfo=timezone.utc),
    )
    day_res = sky_engine.calculate_sky(daytime_obs)
    assert day_res.sun_altitude_deg > 0.0
    assert day_res.is_astronomical_night is False

    # Midnight in Greenwich (Sun is far below horizon, Alt < -18 deg)
    night_obs = ObserverLocation(
        latitude=51.4769,
        longitude=0.0,
        utc_time=datetime(2026, 10, 9, 0, 0, 0, tzinfo=timezone.utc),
    )
    night_res = sky_engine.calculate_sky(night_obs)
    assert night_res.sun_altitude_deg < -18.0
    assert night_res.is_astronomical_night is True


def test_magnitude_sorting():
    """Verify that all_visible_bodies is ordered with brightest apparent magnitudes first."""
    obs = ObserverLocation(
        latitude=40.7128,
        longitude=-74.0060,
        utc_time=datetime(2026, 10, 9, 2, 0, 0, tzinfo=timezone.utc),
    )
    result = sky_engine.calculate_sky(obs)

    mags = [b.apparent_magnitude for b in result.all_visible_bodies if b.apparent_magnitude is not None]
    assert len(mags) > 0
    # Verify non-decreasing order (lower magnitude = brighter)
    for i in range(len(mags) - 1):
        assert mags[i] <= mags[i + 1]


def test_moon_data_when_visible():
    """Verify that if Moon is above horizon, illumination percentage and distance are provided."""
    obs = ObserverLocation(
        latitude=28.6139,
        longitude=77.2090,
        utc_time=datetime(2026, 10, 9, 18, 0, 0, tzinfo=timezone.utc),
    )
    result = sky_engine.calculate_sky(obs)

    if result.moon is not None:
        assert 0.0 <= result.moon.illumination_pct <= 100.0
        assert result.moon.distance_au > 0.002
        assert result.moon.target_type == CelestialTargetType.MOON
