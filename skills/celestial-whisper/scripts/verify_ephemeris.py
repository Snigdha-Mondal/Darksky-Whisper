#!/usr/bin/env python3
"""Verification CLI script for the celestial-whisper Agent Skill.

Computes real-time ephemeris, queries atmospheric seeing telemetry, tests
zero-markdown spoken prose synthesis, and validates compliance with the
Agent Skills Open Standard invariants.
"""

import argparse
from datetime import datetime, timezone
import json
import re
import sys
from typing import Any, Dict

# Ensure project root is in sys.path
from pathlib import Path
project_root = Path(__file__).resolve().parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.app.schemas.sky_schema import ObserverLocation
from backend.app.services.gemma_agent import gemma_agent
from backend.app.services.sky_engine import sky_engine
from backend.app.services.tabpfn_engine import tabpfn_engine

# Ensure UTF-8 output on Windows consoles
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def verify_celestial_skill(
    latitude: float,
    longitude: float,
    heading: float = 90.0,
    elevation: float = 0.0,
    query: str = "What bright star is rising in the east right now?"
) -> Dict[str, Any]:
    """Execute the skill pipeline and validate all invariant rules."""
    observer = ObserverLocation(
        latitude=latitude,
        longitude=longitude,
        elevation_m=elevation,
        utc_time=datetime.now(timezone.utc),
        heading=heading
    )

    # 1. Ephemeris Calculation
    sky_data = sky_engine.calculate_sky(observer)

    # 2. Seeing & Dew Forecast
    seeing_data = tabpfn_engine.get_forecast(latitude=latitude, longitude=longitude)

    # 3. Spoken Prose Generation
    spoken_answer = gemma_agent.answer_query(query, sky_data, seeing_data)

    # 4. Invariant Validations
    violations = []

    # Invariant A: Horizon check (Altitude > 0 deg)
    for body in sky_data.all_visible_bodies:
        if body.altitude_deg <= 0.0:
            violations.append(f"Body {body.name} has altitude <= 0: {body.altitude_deg}")

    # Invariant B: Zero markdown syntax
    if re.search(r"[*#_`\[\]]", spoken_answer):
        violations.append(f"Markdown tokens detected in spoken answer: '{spoken_answer}'")
    if "- " in spoken_answer:
        violations.append(f"List bullet detected in spoken answer: '{spoken_answer}'")

    # Invariant C: Word count brevity limit (10 to 45 words)
    words = spoken_answer.split()
    word_count = len(words)
    if word_count > 45:
        violations.append(f"Spoken answer exceeded 45 words ({word_count} words): '{spoken_answer}'")
    elif word_count < 8:
        violations.append(f"Spoken answer too short ({word_count} words): '{spoken_answer}'")

    # Invariant D: Spatial cue check
    spatial_terms = ["degree", "east", "west", "north", "south", "horizon", "sky", "visible", "up", "overhead"]
    if not any(term in spoken_answer.lower() for term in spatial_terms):
        violations.append(f"Spoken answer missing spatial/directional cues: '{spoken_answer}'")

    targets = sky_data.visible_bodies_in_view or sky_data.all_visible_bodies
    primary_target = targets[0] if targets else None

    return {
        "verified": len(violations) == 0,
        "violations": violations,
        "observer": {
            "latitude": latitude,
            "longitude": longitude,
            "heading": heading,
            "utc_time": observer.utc_time.isoformat()
        },
        "query": query,
        "spoken_answer": spoken_answer,
        "word_count": word_count,
        "seeing_score": seeing_data.current_seeing_score,
        "antoniadi": seeing_data.current_antoniadi.value,
        "dew_risk": seeing_data.current_dew_risk.value,
        "visible_count": len(sky_data.all_visible_bodies),
        "primary_target": {
            "name": primary_target.name,
            "altitude_deg": primary_target.altitude_deg,
            "azimuth_deg": primary_target.azimuth_deg,
            "cardinal": primary_target.cardinal_direction,
            "magnitude": primary_target.apparent_magnitude
        } if primary_target else None
    }


def main():
    parser = argparse.ArgumentParser(description="Verify celestial-whisper Agent Skill compliance.")
    parser.add_argument("--lat", type=float, default=41.6631, help="Observer latitude (default: Cherry Springs 41.6631)")
    parser.add_argument("--lon", type=float, default=-77.8236, help="Observer longitude (default: Cherry Springs -77.8236)")
    parser.add_argument("--heading", type=float, default=90.0, help="Compass heading in degrees (default: 90 East)")
    parser.add_argument("--elevation", type=float, default=625.0, help="Elevation in meters (default: 625m)")
    parser.add_argument("--query", type=str, default="What bright star is rising in the east right now?", help="User query")
    parser.add_argument("--json", action="store_true", help="Output raw JSON result")

    args = parser.parse_args()

    result = verify_celestial_skill(
        latitude=args.lat,
        longitude=args.lon,
        heading=args.heading,
        elevation=args.elevation,
        query=args.query
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status_symbol = "PASS" if result["verified"] else "FAIL"
        print("=" * 65)
        print(f"  CELESTIAL-WHISPER AGENT SKILL VERIFICATION [{status_symbol}]")
        print("=" * 65)
        print(f"Observer Location: {result['observer']['latitude']}° N, {result['observer']['longitude']}° W")
        print(f"Heading:           {result['observer']['heading']}° Azimuth")
        print(f"Seeing Score:      {result['seeing_score']:.1f}/10 ({result['antoniadi']})")
        print(f"Dew Risk:          {result['dew_risk'].upper()}")
        print(f"Visible Bodies:    {result['visible_count']} above horizon")
        if result["primary_target"]:
            pt = result["primary_target"]
            print(f"Primary Target:    {pt['name']} ({pt['altitude_deg']:.1f}° Alt, {pt['cardinal']}, Mag {pt['magnitude']:.2f})")
        print("-" * 65)
        print(f"User Query:        \"{result['query']}\"")
        print(f"Spoken Answer:     \"{result['spoken_answer']}\"")
        print(f"Word Count:        {result['word_count']} words (Limit: 45)")
        print(f"Zero Markdown:     {'VERIFIED' if len(result['violations']) == 0 else 'FAILED'}")
        if result["violations"]:
            print("VIOLATIONS:")
            for v in result["violations"]:
                print(f"  - {v}")
        print("=" * 65)

    sys.exit(0 if result["verified"] else 1)


if __name__ == "__main__":
    main()
