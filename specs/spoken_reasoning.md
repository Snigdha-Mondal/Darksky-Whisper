# Specification: Spoken Astronomical Reasoning (Gemma-2)

**File location in code**: `backend/app/services/gemma_agent.py`

---

## 1. Objective
Transform user queries and structured celestial coordinates into natural, evocative spoken English suitable for speech synthesis without screen dependency.

## 2. Hard Constraints
1. **Length**: 35 to 45 words maximum (no more than 3 spoken sentences).
2. **Zero Markdown**: Output must contain strictly zero `**`, `*`, `_`, `#`, `- `, or numbered list tokens.
3. **No Fluff or Preamble**: Never start with "Certainly!", "Sure thing!", or "Here is what you see:".
4. **Spatial Anchor**: Must state the cardinal direction (North, East, South, West) and approximate altitude in degrees above the horizon.
5. **Atmospheric Context**: Reference seeing conditions when relevant (e.g. steady glow vs. heavy twinkling).

## 3. Input Context Schema
```json
{
  "user_transcript": "What is that bright orange star in the east?",
  "observer_context": {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "heading": "East (90 deg)",
    "local_time": "22:15"
  },
  "atmospheric_seeing": {
    "score": 8.7,
    "condition": "Pristine transparency"
  },
  "visible_bodies": [ ... ]
}
```

## 4. Benchmark Metric Target
- Markdown/artifact rate: 0.0%
- Average token count: $\le 45$ tokens
- Spatial cue accuracy: $\ge 95\%$
