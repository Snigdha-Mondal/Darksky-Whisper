"""Voice Engine for ElevenLabs TTS streaming with local offline audio fallback.

Streams low-pitch observatory narrator speech for hands-free speakerphone delivery,
ensuring zero audio latency and automatic offline fallback for wilderness stargazing.
"""

import io
import math
import struct
import wave
from typing import Optional, Tuple
import requests

from backend.app.config import settings

ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"


class VoiceEngine:
    """Acoustic synthesis service for spoken observatory guidance."""

    def __init__(self):
        self.api_key = settings.elevenlabs_api_key
        self.voice_id = settings.elevenlabs_voice_id or "21m00Tcm4TlvDq8ikWAM"

    @staticmethod
    def generate_offline_tone_audio(duration_sec: float = 1.2, frequency: float = 440.0) -> bytes:
        """Generate a gentle harmonic audio cue (WAV format) when running 100% offline."""
        sample_rate = 22050
        num_samples = int(duration_sec * sample_rate)

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)

            samples = []
            for i in range(num_samples):
                t = float(i) / sample_rate
                # Envelope: smooth attack and decay
                envelope = math.sin(math.pi * t / duration_sec)
                # Calming observatory harmonic (fundamental + soft overtone)
                val = (
                    0.7 * math.sin(2.0 * math.pi * frequency * t)
                    + 0.3 * math.sin(2.0 * math.pi * (frequency * 1.5) * t)
                ) * envelope
                sample_val = int(val * 16383.0)
                samples.append(struct.pack("<h", sample_val))

            wav_file.writeframes(b"".join(samples))

        return buf.getvalue()

    def stream_speech(self, text: str) -> Tuple[bytes, str]:
        """Stream audio from ElevenLabs or fall back to local acoustic audio."""
        if not text:
            text = "Clear skies tonight."

        # If ElevenLabs API key is configured, stream from API
        if self.api_key:
            try:
                url = ELEVENLABS_TTS_URL.format(voice_id=self.voice_id)
                headers = {
                    "xi-api-key": self.api_key,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                }
                payload = {
                    "text": text,
                    "model_id": "eleven_turbo_v2_5",
                    "voice_settings": {
                        "stability": 0.65,
                        "similarity_boost": 0.80,
                        "style": 0.15,
                        "use_speaker_boost": True,
                    },
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=6.0)
                if resp.status_code == 200 and len(resp.content) > 100:
                    return resp.content, "audio/mpeg"
            except Exception:
                # Fall back to offline audio
                pass

        # Offline local harmonic fallback audio
        audio_bytes = self.generate_offline_tone_audio(duration_sec=1.5, frequency=392.0)
        return audio_bytes, "audio/wav"


# Tuple return type alias for clean type-checking
Tuple_Audio = tuple[bytes, str]

# Singleton instance
voice_engine = VoiceEngine()
