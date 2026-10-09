"""Offline Celestial Ephemeris Engine powered by Skyfield and NASA JPL DE421.

Calculates real-time Altitude and Azimuth coordinates for all major solar system
bodies, bright navigational stars, and asterisms for any observer coordinate.
"""

from datetime import datetime, timezone
import math
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from skyfield import almanac
from skyfield.api import Angle, Star, load, wgs84
from skyfield.magnitudelib import planetary_magnitude

from backend.app.config import settings
from backend.app.schemas.sky_schema import (
    CelestialBody,
    CelestialTargetType,
    ObserverLocation,
    SkyFieldResponse,
)

# Cardinal 16-point compass directions
CARDINAL_SECTORS = [
    (11.25, "North"),
    (33.75, "North-Northeast"),
    (56.25, "Northeast"),
    (78.75, "East-Northeast"),
    (101.25, "East"),
    (123.75, "East-Southeast"),
    (146.25, "Southeast"),
    (168.75, "South-Southeast"),
    (191.25, "South"),
    (213.75, "South-Southwest"),
    (236.25, "Southwest"),
    (258.75, "West-Southwest"),
    (281.25, "West"),
    (303.75, "West-Northwest"),
    (326.25, "Northwest"),
    (348.75, "North-Northwest"),
    (360.0, "North"),
]

# Prominent navigational and seasonal stars with J2000 coordinates and visual magnitude
PROMINENT_STARS = [
    {
        "name": "Sirius",
        "ra_hours": 6.7525,
        "dec_degrees": -16.7161,
        "magnitude": -1.46,
        "notes": "Brightest star in the night sky, vivid white-blue diamond in Canis Major",
    },
    {
        "name": "Canopus",
        "ra_hours": 6.3992,
        "dec_degrees": -52.6957,
        "magnitude": -0.74,
        "notes": "Second brightest star, bright white supergiant in Carina",
    },
    {
        "name": "Arcturus",
        "ra_hours": 14.2610,
        "dec_degrees": 19.1822,
        "magnitude": -0.05,
        "notes": "Bright orange giant star in Boötes, follow the arc from the Big Dipper handle",
    },
    {
        "name": "Vega",
        "ra_hours": 18.6156,
        "dec_degrees": 38.7837,
        "magnitude": 0.03,
        "notes": "Brilliant sapphire-blue anchor of the Summer Triangle in Lyra",
    },
    {
        "name": "Capella",
        "ra_hours": 5.2782,
        "dec_degrees": 45.9980,
        "magnitude": 0.08,
        "notes": "Bright golden multiple-star system high in Auriga",
    },
    {
        "name": "Rigel",
        "ra_hours": 5.2423,
        "dec_degrees": -8.2016,
        "magnitude": 0.13,
        "notes": "Luminous blue supergiant marking Orion's western foot",
    },
    {
        "name": "Procyon",
        "ra_hours": 7.6553,
        "dec_degrees": 5.2250,
        "magnitude": 0.38,
        "notes": "Pale yellow star in Canis Minor, vertex of the Winter Triangle",
    },
    {
        "name": "Betelgeuse",
        "ra_hours": 5.9195,
        "dec_degrees": 7.4071,
        "magnitude": 0.50,
        "notes": "Pulsating red supergiant marking Orion's eastern shoulder",
    },
    {
        "name": "Altair",
        "ra_hours": 19.8464,
        "dec_degrees": 8.8683,
        "magnitude": 0.77,
        "notes": "Rapidly rotating white star in Aquila, southern corner of the Summer Triangle",
    },
    {
        "name": "Aldebaran",
        "ra_hours": 4.5987,
        "dec_degrees": 16.5093,
        "magnitude": 0.85,
        "notes": "The fiery reddish eye of the bull in Taurus",
    },
    {
        "name": "Spica",
        "ra_hours": 13.4199,
        "dec_degrees": -11.1614,
        "magnitude": 0.98,
        "notes": "Crisp icy-blue binary star in Virgo, spike down from Arcturus",
    },
    {
        "name": "Antares",
        "ra_hours": 16.4901,
        "dec_degrees": -26.4320,
        "magnitude": 1.06,
        "notes": "Deep ruby heart of Scorpius, rival of Mars",
    },
    {
        "name": "Deneb",
        "ra_hours": 20.6905,
        "dec_degrees": 45.2803,
        "magnitude": 1.25,
        "notes": "Distantly luminous tail of Cygnus the Swan, Summer Triangle vertex",
    },
    {
        "name": "Polaris",
        "ra_hours": 2.5303,
        "dec_degrees": 89.2641,
        "magnitude": 1.98,
        "notes": "North Celestial Pole marker in Ursa Minor, constant true-north compass beacon",
    },
]

# Prominent asterisms & seasonal constellations
PROMINENT_ASTERISMS = [
    {
        "name": "Orion (Belt & Body)",
        "ra_hours": 5.58,
        "dec_degrees": 0.0,
        "magnitude": 0.5,
        "notes": "Iconic winter constellation featuring the three in-line belt stars (Alnitak, Alnilam, Mintaka)",
    },
    {
        "name": "Big Dipper (Ursa Major)",
        "ra_hours": 11.67,
        "dec_degrees": 55.0,
        "magnitude": 1.8,
        "notes": "Circumpolar ladle asterism whose pointer stars Dubhe and Merak point to Polaris",
    },
    {
        "name": "Cassiopeia (The Celestial W)",
        "ra_hours": 1.0,
        "dec_degrees": 60.0,
        "magnitude": 2.2,
        "notes": "Distinctive five-star W or M asterism opposite the Big Dipper across Polaris",
    },
    {
        "name": "Cygnus (Northern Cross)",
        "ra_hours": 20.5,
        "dec_degrees": 42.0,
        "magnitude": 1.3,
        "notes": "Flying swan soaring along the Milky Way dust rift, crowned by Deneb",
    },
    {
        "name": "Pleiades (Seven Sisters)",
        "ra_hours": 3.79,
        "dec_degrees": 24.1,
        "magnitude": 1.6,
        "notes": "Dazzling open cluster of youthful blue stars shining like diamonds in Taurus",
    },
]

# Planet target names mapped to JPL barycenters
PLANET_KEYS = [
    ("Mercury", "mercury barycenter", "Small fleeting planet closest to the Sun"),
    ("Venus", "venus barycenter", "Extremely dazzling Morning or Evening Star with brilliant steady white light"),
    ("Mars", "mars barycenter", "Distinctive rusty amber beacon, the Red Planet"),
    ("Jupiter", "jupiter barycenter", "Creamy golden gas giant, steady non-twinkling beacon"),
    ("Saturn", "saturn barycenter", "Serene golden jewel adorned with majestic planetary rings"),
    ("Uranus", "uranus barycenter", "Faint turquoise gas giant at the threshold of naked-eye visibility"),
    ("Neptune", "neptune barycenter", "Distant deep cobalt ice giant requiring binoculars"),
]


class SkyEngine:
    """Deterministic ephemeris calculation service."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or settings.ephemeris_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.loader = load
        self.eph = None
        self.ts = None
        self._init_skyfield()

    def _init_skyfield(self) -> None:
        """Load ephemeris file and timescale with local directory caching."""
        self.ts = self.loader.timescale()
        bsp_path = self.cache_dir / "de421.bsp"

        if bsp_path.exists():
            self.eph = self.loader(str(bsp_path))
        else:
            # Load and save to cache directory
            self.eph = self.loader("de421.bsp")

    @staticmethod
    def azimuth_to_cardinal(azimuth_deg: float) -> str:
        """Convert decimal azimuth degrees (0=N, 90=E) to cardinal compass text."""
        norm_az = azimuth_deg % 360.0
        for threshold, direction in CARDINAL_SECTORS:
            if norm_az <= threshold:
                return direction
        return "North"

    @staticmethod
    def angular_separation(az1: float, az2: float) -> float:
        """Calculate shortest angular difference between two azimuth angles in degrees."""
        diff = abs(az1 - az2) % 360.0
        return min(diff, 360.0 - diff)

    def calculate_sky(self, observer: ObserverLocation) -> SkyFieldResponse:
        """Calculate coordinates of all celestial targets above the horizon for the given observer."""
        obs_time = observer.utc_time or datetime.now(timezone.utc)
        if obs_time.tzinfo is None:
            obs_time = obs_time.replace(tzinfo=timezone.utc)

        t = self.ts.from_datetime(obs_time)
        topos = wgs84.latlon(
            latitude_degrees=observer.latitude,
            longitude_degrees=observer.longitude,
            elevation_m=observer.elevation_m,
        )
        earth = self.eph["earth"]
        location = earth + topos

        # 1. Sun position & astronomical twilight check
        sun_apparent = location.at(t).observe(self.eph["sun"]).apparent()
        sun_alt, sun_az, _ = sun_apparent.altaz()
        sun_alt_deg = round(sun_alt.degrees, 2)
        is_astronomical_night = sun_alt_deg <= -18.0

        all_bodies: List[CelestialBody] = []
        moon_body: Optional[CelestialBody] = None

        # 2. Moon
        moon_apparent = location.at(t).observe(self.eph["moon"]).apparent()
        moon_alt, moon_az, moon_dist = moon_apparent.altaz()
        if moon_alt.degrees > 0.0:
            moon_illum = round(almanac.fraction_illuminated(self.eph, "moon", t) * 100.0, 1)
            moon_sep = (
                round(self.angular_separation(moon_az.degrees, observer.heading), 2)
                if observer.heading is not None
                else None
            )
            moon_body = CelestialBody(
                name="Moon",
                target_type=CelestialTargetType.MOON,
                altitude_deg=round(moon_alt.degrees, 2),
                azimuth_deg=round(moon_az.degrees, 2),
                cardinal_direction=self.azimuth_to_cardinal(moon_az.degrees),
                apparent_magnitude=-12.7 if moon_illum > 90 else -10.0,
                distance_au=round(moon_dist.au, 6),
                illumination_pct=moon_illum,
                in_field_of_view=(moon_sep is not None and moon_sep <= 45.0),
                angular_separation_from_heading_deg=moon_sep,
                notes=f"{moon_illum}% illuminated disc casting natural ambient moonlight",
            )
            all_bodies.append(moon_body)

        # 3. Planets
        for name, key, notes in PLANET_KEYS:
            target = self.eph[key]
            apparent = location.at(t).observe(target).apparent()
            alt, az, dist = apparent.altaz()
            alt_deg = alt.degrees

            if alt_deg > 0.0:
                sep = (
                    round(self.angular_separation(az.degrees, observer.heading), 2)
                    if observer.heading is not None
                    else None
                )
                try:
                    mag = round(planetary_magnitude(apparent), 2)
                except Exception:
                    mag = None

                all_bodies.append(
                    CelestialBody(
                        name=name,
                        target_type=CelestialTargetType.PLANET,
                        altitude_deg=round(alt_deg, 2),
                        azimuth_deg=round(az.degrees, 2),
                        cardinal_direction=self.azimuth_to_cardinal(az.degrees),
                        apparent_magnitude=mag,
                        distance_au=round(dist.au, 3),
                        in_field_of_view=(sep is not None and sep <= 45.0),
                        angular_separation_from_heading_deg=sep,
                        notes=notes,
                    )
                )

        # 4. Navigational and Bright Stars
        for star_info in PROMINENT_STARS:
            star = Star(ra_hours=star_info["ra_hours"], dec_degrees=star_info["dec_degrees"])
            apparent = location.at(t).observe(star).apparent()
            alt, az, _ = apparent.altaz()
            alt_deg = alt.degrees

            if alt_deg > 0.0:
                sep = (
                    round(self.angular_separation(az.degrees, observer.heading), 2)
                    if observer.heading is not None
                    else None
                )
                all_bodies.append(
                    CelestialBody(
                        name=star_info["name"],
                        target_type=CelestialTargetType.STAR,
                        altitude_deg=round(alt_deg, 2),
                        azimuth_deg=round(az.degrees, 2),
                        cardinal_direction=self.azimuth_to_cardinal(az.degrees),
                        apparent_magnitude=star_info["magnitude"],
                        in_field_of_view=(sep is not None and sep <= 45.0),
                        angular_separation_from_heading_deg=sep,
                        notes=star_info["notes"],
                    )
                )

        # 5. Prominent Asterisms & Constellations
        for ast in PROMINENT_ASTERISMS:
            asterism = Star(ra_hours=ast["ra_hours"], dec_degrees=ast["dec_degrees"])
            apparent = location.at(t).observe(asterism).apparent()
            alt, az, _ = apparent.altaz()
            alt_deg = alt.degrees

            if alt_deg > 0.0:
                sep = (
                    round(self.angular_separation(az.degrees, observer.heading), 2)
                    if observer.heading is not None
                    else None
                )
                all_bodies.append(
                    CelestialBody(
                        name=ast["name"],
                        target_type=CelestialTargetType.CONSTELLATION,
                        altitude_deg=round(alt_deg, 2),
                        azimuth_deg=round(az.degrees, 2),
                        cardinal_direction=self.azimuth_to_cardinal(az.degrees),
                        apparent_magnitude=ast["magnitude"],
                        in_field_of_view=(sep is not None and sep <= 45.0),
                        angular_separation_from_heading_deg=sep,
                        notes=ast["notes"],
                    )
                )

        # Sort all visible bodies by apparent magnitude (brightest first; None at end)
        all_bodies.sort(key=lambda b: (b.apparent_magnitude is None, b.apparent_magnitude))

        # Filter bodies in observer's field of view
        in_view_bodies = [b for b in all_bodies if b.in_field_of_view]
        # In field of view, sort by angular separation from heading (most centered first)
        in_view_bodies.sort(
            key=lambda b: (
                b.angular_separation_from_heading_deg is None,
                b.angular_separation_from_heading_deg,
            )
        )

        return SkyFieldResponse(
            observer=observer,
            timestamp_utc=obs_time,
            sun_altitude_deg=sun_alt_deg,
            is_astronomical_night=is_astronomical_night,
            moon=moon_body,
            visible_bodies_in_view=in_view_bodies,
            all_visible_bodies=all_bodies,
            total_visible_count=len(all_bodies),
        )


# Singleton instance for fast cached queries
sky_engine = SkyEngine()
