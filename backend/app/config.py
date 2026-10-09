"""Application configuration and environment settings."""

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Environment
    app_env: str = Field(default="development", alias="APP_ENV")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    # ElevenLabs Voice API
    elevenlabs_api_key: str = Field(default="", alias="ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = Field(default="21m00Tcm4TlvDq8ikWAM", alias="ELEVENLABS_VOICE_ID")

    # Gemma-2 / Hugging Face
    huggingface_token: str = Field(default="", alias="HUGGINGFACE_TOKEN")
    gemma_model_id: str = Field(default="google/gemma-2-2b-it", alias="GEMMA_MODEL_ID")

    # Prior Labs TabPFN
    tabpfn_api_key: str = Field(default="", alias="TABPFN_API_KEY")

    # Sentry Observability
    sentry_dsn: str = Field(default="", alias="SENTRY_DSN")
    sentry_environment: str = Field(default="development", alias="SENTRY_ENVIRONMENT")
    sentry_traces_sample_rate: float = Field(default=1.0, alias="SENTRY_TRACES_SAMPLE_RATE")

    # Local Ephemeris Cache
    ephemeris_dir: Path = Field(
        default=Path(__file__).resolve().parent.parent.parent / "data" / "ephemeris",
        alias="EPHEMERIS_DIR"
    )


settings = Settings()
