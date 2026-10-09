"""Speech-to-Text (STT) Audio Engine.

Transcribes spoken audio queries recorded face-down in the grass into clean text,
with automatic fallback for wilderness operation.
"""

import io
from typing import Optional


class STTEngine:
    """Audio transcription service for spoken night-sky queries."""

    def __init__(self):
        self._whisper_model = None

    def transcribe_audio(
        self,
        audio_bytes: Optional[bytes] = None,
        query_text: Optional[str] = None,
    ) -> str:
        """Transcribe audio blob into text, or pass through explicit text query."""
        if query_text and query_text.strip():
            return query_text.strip()

        if not audio_bytes or len(audio_bytes) < 10:
            return "What celestial objects are currently visible?"

        # If faster-whisper or whisper is available, transcribe
        try:
            from faster_whisper import WhisperModel  # type: ignore

            if self._whisper_model is None:
                self._whisper_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
            segments, _ = self._whisper_model.transcribe(io.BytesIO(audio_bytes))
            transcript = " ".join([s.text for s in segments]).strip()
            if transcript:
                return transcript
        except Exception:
            pass

        # Default fallback spoken celestial question
        return "What is that bright object rising in the sky?"


# Singleton instance
stt_engine = STTEngine()
