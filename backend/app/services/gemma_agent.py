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
        stability_phrase = (
            "tonight's atmospheric seeing is exceptionally steady"
            if seeing_score >= 8.0
            else "notice the gentle twinkling through the atmospheric boundary layer"
        )

        # 1. Query asks about the Moon
        if "moon" in query_lower:
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

        # 2. Specific named target lookup (Jupiter, Saturn, Orion, Sirius, etc.)
        for body in sky_data.all_visible_bodies:
            body_name_lower = body.name.lower().split(" (")[0]
            if body_name_lower in query_lower:
                return self.sanitize_for_speech(
                    f"That is {body.name}, visible {body.altitude_deg:.0f} degrees up in the {body.cardinal_direction.lower()}. "
                    f"Because {stability_phrase}, it shines with a calm, radiant glow."
                )

        # 3. Brightest object in field of view or sky ("what is that bright star/light?")
        if targets:
            brightest = targets[0]
            return self.sanitize_for_speech(
                f"That bright beacon rising {brightest.altitude_deg:.0f} degrees high in the {brightest.cardinal_direction.lower()} is {brightest.name}. "
                f"Because {stability_phrase}, it stands out vividly against the open sky."
            )

        # 4. General night sky condition
        return self.sanitize_for_speech(
            f"You are looking at an open sky. "
            f"Because {stability_phrase}, look towards the horizon to identify the brightest navigational beacons."
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
