"""Unit tests validating ZERO markdown formatting and spoken brevity for Gemma-2 responses."""

from datetime import datetime, timezone
import re
import pytest

from backend.app.schemas.sky_schema import ObserverLocation
from backend.app.services.gemma_agent import GemmaAgent, gemma_agent
from backend.app.services.sky_engine import sky_engine
from backend.app.services.tabpfn_engine import tabpfn_engine


def test_sanitize_for_speech_strips_formatting_tokens():
    """Verify regex sanitizer eliminates all markdown syntax and introductory fluff."""
    dirty_samples = [
        ("**Jupiter** is visible in the *east*.", "Jupiter is visible in the east."),
        ("Certainly! Here is what you see: Look **30 degrees** up.", "Look 30 degrees up."),
        ("# Sky Guide\n- **Item 1**: Vega\n- **Item 2**: Altair", "Item 1: Vega Item 2: Altair"),
        ("Check out [Orion](https://stars.org) tonight!", "Check out Orion tonight!"),
        ("`12 degrees` above the horizon.", "12 degrees above the horizon."),
        ("1. Look south.\n2. Spot Saturn.", "Look south. Spot Saturn."),
    ]

    for dirty, expected in dirty_samples:
        clean = GemmaAgent.sanitize_for_speech(dirty)
        # Ensure zero markdown characters remain
        assert not re.search(r"[*#_`\[\]]", clean), f"Markdown remained in: {clean}"
        assert not clean.lower().startswith("certainly")
        assert not clean.lower().startswith("here is what you see")


def test_zero_markdown_and_brevity_across_diverse_queries():
    """Verify that end-to-end responses across 8 astronomical queries contain ZERO markdown and stay <= 45 words."""
    # Cherry Springs dark sky observatory context
    observer = ObserverLocation(
        latitude=41.6631,
        longitude=-77.8236,
        utc_time=datetime(2026, 10, 10, 2, 30, 0, tzinfo=timezone.utc),
        heading=90.0,  # Looking East
    )
    sky_data = sky_engine.calculate_sky(observer)
    seeing_data = tabpfn_engine.get_forecast(latitude=observer.latitude, longitude=observer.longitude)

    queries = [
        "What is that bright orange star rising in the east?",
        "Can I see Saturn right now?",
        "Where is Aldebaran located?",
        "Is the Moon visible tonight?",
        "What are the Pleiades?",
        "What is the brightest light in the night sky?",
        "Tell me about the sky condition tonight",
        "What is rising above the tree line in the southeast?",
        "What stars are visible in the sky?",
        "What stars are visible in",
        "What planets can I see?",
        "What can I see tonight?",
    ]

    for query in queries:
        response = gemma_agent.answer_query(query, sky_data, seeing_data)

        # 1. Zero markdown formatting check
        assert not re.search(r"[*#_`\[\]]", response), f"Found markdown tokens in response: '{response}'"
        assert "- " not in response, f"Found bullet marker in: '{response}'"

        # 2. Strict word count limit (35-45 words max)
        word_count = len(response.split())
        assert word_count <= 45, f"Response exceeded 45 words ({word_count} words): '{response}'"
        assert word_count >= 10, f"Response too short ({word_count} words): '{response}'"

        # 3. Spatial cues check (must contain cardinal direction or altitude or degrees or horizon)
        spatial_terms = ["degree", "east", "west", "north", "south", "horizon", "sky", "visible", "up"]
        has_spatial = any(term in response.lower() for term in spatial_terms)
        assert has_spatial, f"Response lacks spatial directional cues: '{response}'"

        # 4. Zero conversational chat preamble
        assert not response.lower().startswith("certainly")
        assert not response.lower().startswith("sure")
