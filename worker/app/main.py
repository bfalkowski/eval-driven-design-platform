import logging
import signal
import time

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.tracing import configure_worker_tracing

logger = logging.getLogger("edd-worker")


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    configure_worker_tracing(
        settings.service_name,
        settings.otel_enabled,
        settings.otel_exporter,
        settings.otel_otlp_endpoint,
    )
    logger.info("edd-worker started (Phase 2 — experiment execution runs in API for now)")

    stop = False

    def handle_stop(*_args: object) -> None:
        nonlocal stop
        stop = True

    signal.signal(signal.SIGINT, handle_stop)
    signal.signal(signal.SIGTERM, handle_stop)

    while not stop:
        time.sleep(1)

    logger.info("edd-worker stopped")


if __name__ == "__main__":
    main()
