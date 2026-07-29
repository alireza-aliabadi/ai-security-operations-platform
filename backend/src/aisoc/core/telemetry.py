"""OpenTelemetry bootstrap."""

from __future__ import annotations

from aisoc.core.config import Settings
from aisoc.core.logging import get_logger

logger = get_logger(__name__)


def setup_telemetry(settings: Settings) -> None:
    if not settings.otel_enabled:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": settings.otel_service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        logger.info("otel_enabled", endpoint=settings.otel_exporter_otlp_endpoint)
    except Exception as exc:  # noqa: BLE001
        logger.warning("otel_setup_failed", error=str(exc))


def instrument_app(app: object) -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001
        logger.warning("otel_instrument_failed", error=str(exc))
