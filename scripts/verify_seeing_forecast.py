"""Live verification script for DarkSky Whisper Atmospheric Seeing Forecaster."""

from datetime import datetime, timezone
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

from backend.app.services.tabpfn_engine import tabpfn_engine


def main():
    print("=" * 80)
    print("🔭 DarkSky Whisper — Tabular Atmospheric Seeing Forecaster Live Test")
    print("=" * 80)

    # Cherry Springs State Park, PA (Dark Sky Park)
    lat, lon = 41.6631, -77.8236
    print(f"Target Observatory: Cherry Springs State Park (Lat {lat}° N, Lon {abs(lon)}° W)")
    print(f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("-" * 80)

    # Generate forecast
    forecast = tabpfn_engine.get_forecast(latitude=lat, longitude=lon)

    print(f"📡 Telemetry Engine: {forecast.model_used}")
    print(f"🌟 Current Seeing Quality Index: {forecast.current_seeing_score:.1f} / 10.0")
    print(f"🔭 Antoniadi Scale: {forecast.current_antoniadi.value}")
    print(f"💧 Dew Condensation Risk: {forecast.current_dew_risk.value.upper()}")
    if forecast.dew_warning:
        print(f"⚠️  Dew Advisory: {forecast.dew_warning}")
    else:
        print("✅ Dew Advisory: None (Optics and blankets remain dry)")

    print(f"\n🎯 Peak Observation Window: {forecast.peak_observation_window}")
    print(f"💎 Peak Seeing Score Tonight: {forecast.peak_seeing_score:.1f} / 10.0")

    print("\n📊 24-Hour Seeing & Atmospheric Trend:")
    print(f"{'Time (UTC)':<12} {'Seeing':<8} {'Antoniadi':<12} {'Dew Risk':<10} {'Optimal?':<10} {'Summary'}")
    print("-" * 95)
    for p in forecast.hourly_forecast[:12]:  # Show next 12 hours
        opt_str = "★ YES" if p.is_optimal_window else "-"
        time_str = p.timestamp.strftime("%H:%M")
        ant_short = p.antoniadi_scale.value.split(" - ")[0]
        print(f"{time_str:<12} {p.seeing_score:>4.1f}/10  {ant_short:<12} {p.dew_risk.value:<10} {opt_str:<10} {p.summary[:45]}...")

    print("\n" + "=" * 80)
    print("✅ Tabular atmospheric seeing verification completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    main()
