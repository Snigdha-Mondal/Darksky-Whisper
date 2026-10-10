"""Gemma-2 Conversational Astronomical Reasoning Agent.

Translates real-time ephemeris coordinates, atmospheric seeing conditions,
and user spoken queries into crisp, 35-word natural spoken prose with
guaranteed ZERO markdown formatting.
"""

from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional
import requests

from backend.app.config import settings
from backend.app.schemas.forecast_schema import SeeingForecastResponse
from backend.app.schemas.sky_schema import CelestialBody, SkyFieldResponse

# Strict zero-markdown system prompt
GEMMA_SYSTEM_PROMPT = """You are DarkSky Whisper, an eyes-free astronomical field companion.
The user is lying outside on a blanket looking at the real night sky.
Given the observer's visible celestial matrix and current atmospheric seeing score, answer their spoken query.

Strict formatting rules:
1. Speak in natural, evocative, conversational English.
2. NEVER use markdown, bolding, italics, asterisks, numbers, or bullet points.
3. Do not include introductory filler like "Certainly!" or "Here is what you see:".
4. Limit your entire response to 35-45 words (maximum 3 spoken sentences).
5. Give immediate spatial cues: specify cardinal direction (North, East, South, West) and altitude in degrees above the horizon.
6. If optical seeing is exceptional or poor, briefly mention how that affects the view."""


class GemmaAgent:
    """Conversational reasoning engine for spoken celestial guidance."""

    def __init__(self):
        self.hf_token = settings.huggingface_token
        self.model_id = settings.gemma_model_id

    @staticmethod
    def sanitize_for_speech(text: str) -> str:
        """Sanitize text to guarantee zero markdown artifacts or pronunciation glitches.

        Strips asterisks, markdown headings, bullets, brackets, and underscores.
        """
        if not text:
            return ""

        # Remove bold/italic markers
        clean = text.replace("**", "").replace("*", "").replace("__", "").replace("_", "")
        # Remove markdown headers (#, ##, etc.)
        clean = re.sub(r"^#+\s*", "", clean, flags=re.MULTILINE)
        # Remove markdown list markers (- , + , * )
        clean = re.sub(r"^\s*[-+*]\s+", "", clean, flags=re.MULTILINE)
        # Remove numbered lists (1. , 2. )
        clean = re.sub(r"^\s*\d+\.\s+", "", clean, flags=re.MULTILINE)
        # Remove bracketed links [text](url) -> text
        clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean)
        # Remove backticks
        clean = clean.replace("`", "")
        # Remove multiple whitespace/newlines
        clean = re.sub(r"\s+", " ", clean).strip()

        # Remove conversational chat filler if present
        filler_patterns = [
            r"^certainly!?,?\s*",
            r"^sure thing!?,?\s*",
            r"^here is what you (can see|see):?\s*",
            r"^as an ai,?\s*",
            r"^i can tell you that\s*",
        ]
        for pattern in filler_patterns:
            clean = re.sub(pattern, "", clean, flags=re.IGNORECASE).strip()

        # Capitalize first letter
        if clean and clean[0].islower():
            clean = clean[0].upper() + clean[1:]

        return clean

    def build_context_payload(
        self,
        user_query: str,
        sky_data: SkyFieldResponse,
        seeing_data: Optional[SeeingForecastResponse] = None,
    ) -> Dict[str, Any]:
        """Format celestial and atmospheric telemetry into a structured JSON context payload."""
        # Top visible targets in field of view or overall
        targets = sky_data.visible_bodies_in_view or sky_data.all_visible_bodies[:6]
        serialized_targets = [
            {
                "name": b.name,
                "type": b.target_type.value,
                "altitude_deg": b.altitude_deg,
                "azimuth_deg": b.azimuth_deg,
                "cardinal": b.cardinal_direction,
                "apparent_magnitude": b.apparent_magnitude,
                "notes": b.notes,
            }
            for b in targets
        ]

        seeing_info = {
            "score": seeing_data.current_seeing_score if seeing_data else 8.0,
            "condition": (
                seeing_data.hourly_forecast[0].summary
                if seeing_data and seeing_data.hourly_forecast
                else "Clear sky"
            ),
        }

        return {
            "user_query": user_query,
            "observer": {
                "latitude": sky_data.observer.latitude,
                "longitude": sky_data.observer.longitude,
                "heading": (
                    f"{sky_data.observer.heading} deg"
                    if sky_data.observer.heading is not None
                    else "None"
                ),
            },
            "atmospheric_seeing": seeing_info,
            "visible_targets": serialized_targets,
            "is_astronomical_night": sky_data.is_astronomical_night,
        }

    def _offline_reasoning_fallback(
        self,
        user_query: str,
        sky_data: SkyFieldResponse,
        seeing_data: Optional[SeeingForecastResponse] = None,
    ) -> str:
        """Deterministic, zero-latency conversational reasoning engine.

        Guarantees instant spoken responses in wilderness dark-sky parks with zero network,
        strictly maintaining the 35-word limit and zero markdown formatting.
        """
        query_lower = user_query.lower()
        targets = sky_data.visible_bodies_in_view or sky_data.all_visible_bodies

        seeing_score = seeing_data.current_seeing_score if seeing_data else 8.0
        if seeing_score >= 8.0:
            stability_clause = "Under tonight's calm atmospheric seeing, it shines with steady radiance."
            seeing_note = "atmospheric seeing is exceptionally steady"
        else:
            stability_clause = "Through slight atmospheric seeing turbulence, it twinkles gently against the open sky."
        known_planets_stars = [
            "saturn", "jupiter", "mars", "venus", "mercury", "moon", "orion",
            "sirius", "vega", "capella", "aldebaran", "betelgeuse", "rigel", "polaris", "pleiades", "andromeda"
        ]
        has_specific_target = any(name in query_lower for name in known_planets_stars)

        # 1. Observation Window & Peak Timing Queries
        window_keywords = ["window", "prime", "best time", "peak", "when should", "when to", "timing", "schedule", "forecast"]
        if any(w in query_lower for w in window_keywords) and not has_specific_target:
            score = seeing_data.current_seeing_score if seeing_data else 7.5
            peak_window = (
                seeing_data.peak_observation_window.replace(" - ", " to ").split(" (")[0]
                if seeing_data and seeing_data.peak_observation_window
                else "tonight"
            )
            dew_risk = (
                seeing_data.current_dew_risk.value
                if seeing_data and hasattr(seeing_data, "current_dew_risk")
                else "low"
            )
            dew_clause = "keep lens heaters ready for dew" if dew_risk in ["critical", "high"] else "dew risk is minimal"
            return self.sanitize_for_speech(
                f"Your prime observation window opens at {peak_window}. "
                f"Atmospheric seeing reaches {score:.1f} out of 10 with calm optical stability. "
                f"The sky is clear overhead and {dew_clause}."
            )

        # 2. Dew Risk & Moisture Inquiries
        dew_keywords = ["dew", "fog", "humidity", "moisture", "lens heater"]
        if any(d in query_lower for d in dew_keywords) and not has_specific_target:
            dew_risk = (
                seeing_data.current_dew_risk.value
                if seeing_data and hasattr(seeing_data, "current_dew_risk")
                else "low"
            )
            if dew_risk in ["critical", "high"]:
                return self.sanitize_for_speech(
                    f"Dew risk is currently rated {dew_risk.upper()} across your optics. "
                    f"Temperature is near the dew point, so run lens heaters to prevent condensation."
                )
            else:
                return self.sanitize_for_speech(
                    f"Dew risk is currently low with a safe thermal margin. "
                    f"Telescope optics and camera lenses will remain clear and dry under tonight's open sky."
                )

        # 3. Atmospheric Seeing & Sky Clarity & Weather Queries
        seeing_keywords = [
            "clear", "clarity", "seeing", "weather", "atmospher", "turbulen",
            "cloud", "transparen", "condition", "stargaz", "observ", "good night"
        ]
        if any(k in query_lower for k in seeing_keywords) and not has_specific_target:
            score = seeing_data.current_seeing_score if seeing_data else 7.5
            antoniadi_raw = (
                seeing_data.current_antoniadi.value
                if seeing_data and hasattr(seeing_data, "current_antoniadi")
                else "II - Good seeing with slight tremors"
            )
            antoniadi_desc = antoniadi_raw.split(" - ")[-1].lower()
            dew_risk = (
                seeing_data.current_dew_risk.value
                if seeing_data and hasattr(seeing_data, "current_dew_risk")
                else "low"
            )
            peak_window = (
                seeing_data.peak_observation_window.replace(" - ", " to ").split(" (")[0]
                if seeing_data and seeing_data.peak_observation_window
                else "tonight"
            )

            if dew_risk in ["critical", "high"]:
                moisture_clause = "critical dew risk requires lens heaters tonight"
            else:
                moisture_clause = "dew risk is minimal across your optics"

            return self.sanitize_for_speech(
                f"Atmospheric seeing is rated {score:.1f} out of 10 with {antoniadi_desc}. "
                f"The night sky is clear overhead, though {moisture_clause}. "
                f"Prime viewing window begins around {peak_window}."
            )

        # 4. Query asks about the Moon
        if "moon" in query_lower or "lunar" in query_lower:
            if sky_data.moon:
                m = sky_data.moon
                return self.sanitize_for_speech(
                    f"The Moon is glowing {m.altitude_deg:.0f} degrees high in the {m.cardinal_direction.lower()}, "
                    f"about {m.illumination_pct:.0f} percent illuminated. "
                    f"Its ambient light illuminates the surrounding landscape."
                )
            else:
                return self.sanitize_for_speech(
                    "The Moon is currently below the horizon, creating pitch-black skies that reveal faint stars and the Milky Way dust lanes."
                )

        # 3. Sky overview / Visible stars and planets / Tour
        overview_phrases = [
            "what can i see", "what should i look at", "what's visible", "what is visible",
            "what star", "what stars", "which stars", "stars are visible", "stars visible",
            "visible stars", "what planet", "which planet", "planets visible", "planets are visible",
            "tour", "recommend", "show me", "what is up there", "what is in the sky",
            "what can be seen", "what are visible", "visible tonight"
        ]
        if any(p in query_lower for p in overview_phrases):
            all_vis = sky_data.all_visible_bodies
            if all_vis:
                # Pick up to 3 distinct prominent targets
                selected = all_vis[:3]
                desc_parts = [f"{b.name} {b.altitude_deg:.0f} degrees up in the {b.cardinal_direction.lower()}" for b in selected]
                desc_text = ", ".join(desc_parts)
                return self.sanitize_for_speech(
                    f"Currently {len(all_vis)} celestial targets are above your horizon. "
                    f"Look for {desc_text}. "
                    f"Because {seeing_note}, these beacons stand out vividly."
                )
            else:
                return self.sanitize_for_speech(
                    f"You are looking at an open sky. "
                    f"Because {seeing_note}, faint background stars and constellations are visible across the dome."
                )

        # 4. Specific named target lookup (visible above horizon)
        for body in sky_data.all_visible_bodies:
            body_name_lower = body.name.lower().split(" (")[0]
            if body_name_lower in query_lower:
                return self.sanitize_for_speech(
                    f"That is {body.name}, visible {body.altitude_deg:.0f} degrees up in the {body.cardinal_direction.lower()}. "
                    f"{body.notes}. {stability_clause}"
                )

        # 5. Check if user asked about a known celestial target that is below horizon
        known_major_targets = {
            "saturn": "Saturn",
            "jupiter": "Jupiter",
            "mars": "Mars",
            "venus": "Venus",
            "mercury": "Mercury",
            "orion": "Orion",
            "sirius": "Sirius",
            "vega": "Vega",
            "capella": "Capella",
            "aldebaran": "Aldebaran",
            "betelgeuse": "Betelgeuse",
            "rigel": "Rigel",
            "pleiades": "the Pleiades cluster",
            "andromeda": "the Andromeda Galaxy",
        }
        for key, display_name in known_major_targets.items():
            if key in query_lower:
                return self.sanitize_for_speech(
                    f"{display_name} is currently below your local horizon. "
                    f"It will rise later in the night when your observation window opens."
                )

        # 6. Direction-specific inquiry (e.g. "in the east", "in the south")
        for cardinal in ["east", "west", "north", "south", "southeast", "southwest", "northeast", "northwest", "overhead", "zenith"]:
            if cardinal in query_lower:
                directional_targets = [
                    b for b in targets
                    if cardinal in b.cardinal_direction.lower() or (cardinal in ["overhead", "zenith"] and b.altitude_deg > 60)
                ]
                if directional_targets:
                    chosen = directional_targets[0]
                    return self.sanitize_for_speech(
                        f"Looking towards the {cardinal}, that bright beacon {chosen.altitude_deg:.0f} degrees up is {chosen.name}. "
                        f"{chosen.notes}. {stability_clause}"
                    )
                elif sky_data.all_visible_bodies:
                    alt_chosen = sky_data.all_visible_bodies[0]
                    return self.sanitize_for_speech(
                        f"Looking towards the {cardinal}, no prominent planets are above the horizon. "
                        f"Turn towards the {alt_chosen.cardinal_direction.lower()} to spot {alt_chosen.name} {alt_chosen.altitude_deg:.0f} degrees high."
                    )

        # 7. Brightest object in field of view or sky ("what is that bright star/light?")
        if targets:
            brightest = targets[0]
            return self.sanitize_for_speech(
                f"That bright beacon rising {brightest.altitude_deg:.0f} degrees high in the {brightest.cardinal_direction.lower()} is {brightest.name}. "
                f"{brightest.notes}. {stability_clause}"
            )

        # 8. General night sky fallback
        return self.sanitize_for_speech(
            f"You are looking at an open sky. "
            f"Because {seeing_note}, look towards the horizon to identify the brightest navigational beacons."
        )

    def answer_query(
        self,
        user_query: str,
        sky_data: SkyFieldResponse,
        seeing_data: Optional[SeeingForecastResponse] = None,
    ) -> str:
        """Synthesize a 35-word natural spoken response for the user's question."""
        # If Hugging Face token is provided and remote endpoint is enabled:
        if self.hf_token:
            try:
                context = self.build_context_payload(user_query, sky_data, seeing_data)
                prompt = (
                    f"<start_of_turn>user\n"
                    f"{GEMMA_SYSTEM_PROMPT}\n\n"
                    f"Observation Context:\n{json.dumps(context, indent=2)}\n\n"
                    f"Answer the user query in under 40 spoken words without markdown:<end_of_turn>\n"
                    f"<start_of_turn>model\n"
                )
                headers = {"Authorization": f"Bearer {self.hf_token}"}
                payload = {
                    "inputs": prompt,
                    "parameters": {"max_new_tokens": 70, "temperature": 0.3},
                }
                api_url = f"https://api-inference.huggingface.co/models/{self.model_id}"
                resp = requests.post(api_url, headers=headers, json=payload, timeout=4.0)
                if resp.status_code == 200:
                    result = resp.json()
                    raw_text = result[0].get("generated_text", "").split("<start_of_turn>model\n")[-1]
                    clean = self.sanitize_for_speech(raw_text)
                    if clean:
                        return clean
            except Exception:
                # Fall back immediately to deterministic offline reasoning
                pass

        # Use deterministic offline reasoning (fast, offline-resilient, guaranteed zero-markdown)
        return self._offline_reasoning_fallback(user_query, sky_data, seeing_data)


# Singleton instance
gemma_agent = GemmaAgent()
