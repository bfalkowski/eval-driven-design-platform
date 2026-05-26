from __future__ import annotations

from typing import Literal

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor, SpanExporter

OtelExporter = Literal["console", "otlp", "none"]
ActiveOtelExporter = Literal["console", "otlp"]


def configure_worker_tracing(
    service_name: str,
    enabled: bool = True,
    exporter: OtelExporter = "console",
    otlp_endpoint: str | None = None,
) -> None:
    if not enabled or exporter == "none":
        return

    span_exporter = _build_span_exporter(exporter, otlp_endpoint)
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    trace.set_tracer_provider(provider)


def _build_span_exporter(exporter: ActiveOtelExporter, otlp_endpoint: str | None) -> SpanExporter:
    if exporter == "console":
        return ConsoleSpanExporter()
    if exporter == "otlp":
        if otlp_endpoint:
            return OTLPSpanExporter(endpoint=otlp_endpoint)
        return OTLPSpanExporter()
    raise ValueError(f"Unsupported OpenTelemetry exporter: {exporter}")
