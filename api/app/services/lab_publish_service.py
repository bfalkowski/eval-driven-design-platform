"""Backward-compatible re-exports. Prefer app.services.run_ingest_service."""

from app.services.run_ingest_service import (
    INGEST_SCHEMA_VERSION,
    LAB_PUBLISH_SCHEMA_VERSION,
    LAB_PUBLISH_SOURCE,
    LabPublishService,
    RunIngestService,
    compute_gate,
    extract_overall_score,
)

__all__ = [
    "INGEST_SCHEMA_VERSION",
    "LAB_PUBLISH_SCHEMA_VERSION",
    "LAB_PUBLISH_SOURCE",
    "LabPublishService",
    "RunIngestService",
    "compute_gate",
    "extract_overall_score",
]
