"""Sentry Agent Tracing and performance observability module.

Wraps each stage of the DarkSky Whisper orchestrator in custom Sentry spans:
- tabpfn.seeing_prediction
- skyfield.ephemeris_calculation
- whisper.stt_transcription
- gemma.reasoning_inference
- elevenlabs.tts_synthesis
"""

from contextlib import contextmanager
import logging
import time
from typing import Any, Dict, Generator, Optional

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    sentry_sdk = None
    FastApiIntegration = None
    SENTRY_AVAILABLE = False

from backend.app.config import settings

logger = logging.getLogger("darksky.telemetry")


def init_sentry() -> bool:
    """Initialize Sentry SDK with FastApiIntegration and custom trace rates."""
    if not SENTRY_AVAILABLE:
        logger.info("Sentry SDK not available in environment; telemetry running in no-op mode.")
        return False

    if not settings.sentry_dsn:
        logger.info("No SENTRY_DSN configured; telemetry running in local profiling mode.")
        return False

    try:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.sentry_environment,
            traces_sample_rate=settings.sentry_traces_sample_rate,
            integrations=[FastApiIntegration()] if FastApiIntegration else [],
            send_default_pii=False,
            attach_stacktrace=True,
            release="darksky-whisper@0.1.0",
        )
        logger.info("Sentry Agent Tracing initialized successfully.")
        return True
    except Exception as e:
        logger.warning(f"Failed to initialize Sentry: {e}")
        return False


class SentryTracer:
    """Agent pipeline observability wrapper providing custom span instrumentation."""

    def __init__(self):
        self.is_active = False

    def setup(self):
        """Perform initial telemetry setup."""
        self.is_active = init_sentry()

    @contextmanager
    def trace_span(
        self,
        op: str,
        description: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Generator[Dict[str, Any], None, None]:
        """Context manager creating a custom Sentry Agent Tracing span with latency profiling."""
        span_metrics: Dict[str, Any] = {"op": op, "description": description, "data": data or {}}
        start_time = time.perf_counter()

        if SENTRY_AVAILABLE and sentry_sdk and settings.sentry_dsn:
            try:
                with sentry_sdk.start_span(op=op, description=description) as span:
                    if data:
                        for k, v in data.items():
                            span.set_data(k, v)
                    yield span_metrics
                    elapsed_ms = (time.perf_counter() - start_time) * 1000
                    span.set_data("duration_ms", round(elapsed_ms, 2))
                    span_metrics["duration_ms"] = round(elapsed_ms, 2)
                    return
            except Exception as e:
                logger.debug(f"Sentry span recording error: {e}")

        # Local fallback profiling when Sentry DSN is not provided
        try:
            yield span_metrics
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            span_metrics["duration_ms"] = round(elapsed_ms, 2)

    def record_pipeline_metrics(
        self,
        query: str,
        word_count: int,
        seeing_score: float,
        visible_count: int,
        duration_ms: float
    ):
        """Record high-level transaction metrics to Sentry scope."""
        if SENTRY_AVAILABLE and sentry_sdk and settings.sentry_dsn:
            try:
                with sentry_sdk.configure_scope() as scope:
                    scope.set_tag("seeing_score", str(round(seeing_score, 1)))
                    scope.set_tag("visible_count", str(visible_count))
                    scope.set_tag("zero_markdown", "true")
                    scope.set_extra("query", query)
                    scope.set_extra("word_count", word_count)
                    scope.set_extra("total_duration_ms", duration_ms)
            except Exception:
                pass


# Global singleton
sentry_tracer = SentryTracer()
trace_span = sentry_tracer.trace_span
