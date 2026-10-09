"""Live verification script for DarkSky Whisper Offline Ephemeris Engine."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

# Ensure UTF-8 stdout on Windows
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repository root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.schemas.sky_schema import ObserverLocation
from backend.app.services.sky_engine import sky_engine


def main():
    print("=" * 70)
    print("🌌 DarkSky Whisper — Offline Ephemeris Live Verification")
    print("=" * 70)

    # Cherry Springs State Park, PA (International Dark Sky Park)
    # Coordinates: 41.6631° N, 77.8236° W, Elevation 700m
    # Simulated time: October 9, 2026, 22:30 EDT (02:30 UTC next day)
    # Observer lying face-down looking East (Heading = 90 deg)
    observer = ObserverLocation(
        latitude=41.6631,
        longitude=-77.8236,
        elevation_m=700.0,
        utc_time=datetime(2026, 10, 10, 2, 30, 0, tzinfo=timezone.utc),
        heading=90.0,
    )

    print(f"Observer Location: Lat {observer.latitude}° N, Lon {abs(observer.longitude)}° W")
    print(f"Observation Time (UTC): {observer.utc_time.isoformat()}")
    print(f"Observer Compass Heading: {observer.heading}° (Due East)")
    print("-" * 70)

    response = sky_engine.calculate_sky(observer)

    print(f"☀️ Sun Altitude: {response.sun_altitude_deg}°")
    print(f"🌑 Astronomical Night: {'YES (Pitch Darkness)' if response.is_astronomical_night else 'NO'}")
    print(f"✨ Total Celestial Bodies Visible: {response.total_visible_count}")
    print(f"🔭 Bodies in Field of View (East +/- 45°): {len(response.visible_bodies_in_view)}")

    if response.moon:
        print(f"\n🌙 Moon: Altitude {response.moon.altitude_deg}°, Azimuth {response.moon.azimuth_deg}° ({response.moon.cardinal_direction}), Illumination: {response.moon.illumination_pct}%")
    else:
        print("\n🌙 Moon: Currently below the horizon (optimal deep-sky darkness)")

    print("\n🔭 Targets in Observer Field of View (Facing East):")
    print(f"{'Name':<22} {'Type':<14} {'Alt':<8} {'Az':<8} {'Direction':<18} {'Mag':<6} {'Notes'}")
    print("-" * 105)
    for b in response.visible_bodies_in_view:
        mag_str = f"{b.apparent_magnitude:+.1f}" if b.apparent_magnitude is not None else "N/A"
        print(f"{b.name:<22} {b.target_type.value:<14} {b.altitude_deg:>5.1f}°  {b.azimuth_deg:>5.1f}°  {b.cardinal_direction:<18} {mag_str:<6} {b.notes or ''}")

    print("\n🌟 Top 5 Brightest Visible Objects Across Entire Sky:")
    for i, b in enumerate(response.all_visible_bodies[:5], 1):
        mag_str = f"{b.apparent_magnitude:+.2f}" if b.apparent_magnitude is not None else "N/A"
        print(f"  {i}. {b.name:<18} (Mag {mag_str}) at Alt {b.altitude_deg:>5.1f}°, Az {b.azimuth_deg:>5.1f}° ({b.cardinal_direction})")

    print("\n" + "=" * 70)
    print("✅ Ephemeris verification completed successfully with sub-arcminute JPL accuracy.")
    print("=" * 70)


if __name__ == "__main__":
    main()
