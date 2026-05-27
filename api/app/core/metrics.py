from __future__ import annotations

import threading
from collections import defaultdict
from collections.abc import Mapping

LabelSet = tuple[tuple[str, str], ...]
MetricKey = tuple[str, LabelSet]


class MetricsRegistry:
    def __init__(self) -> None:
        self._values: defaultdict[MetricKey, float] = defaultdict(float)
        self._metadata: dict[str, tuple[str, str]] = {
            "http_requests_total": ("counter", "HTTP requests handled by the API."),
            "http_request_duration_seconds_count": (
                "counter",
                "HTTP request duration observation count.",
            ),
            "http_request_duration_seconds_sum": (
                "counter",
                "Total observed HTTP request duration in seconds.",
            ),
            "langfuse_score_push_total": (
                "counter",
                "Langfuse score push attempts by outcome.",
            ),
        }
        self._lock = threading.Lock()

    def increment(
        self,
        name: str,
        labels: Mapping[str, str] | None = None,
        amount: float = 1.0,
    ) -> None:
        with self._lock:
            self._values[(name, self._label_set(labels))] += amount

    def observe_duration(self, name: str, seconds: float, labels: Mapping[str, str]) -> None:
        self.increment(f"{name}_count", labels)
        self.increment(f"{name}_sum", labels, seconds)

    def render_prometheus(self) -> str:
        with self._lock:
            values = dict(self._values)

        lines: list[str] = []
        for name in sorted({metric_name for metric_name, _ in values}):
            metric_type, help_text = self._metadata.get(name, ("gauge", name))
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} {metric_type}")
            for (metric_name, labels), value in sorted(values.items()):
                if metric_name != name:
                    continue
                lines.append(f"{name}{self._format_labels(labels)} {value:g}")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _label_set(labels: Mapping[str, str] | None) -> LabelSet:
        if labels is None:
            return ()
        return tuple(sorted((key, value) for key, value in labels.items()))

    @staticmethod
    def _format_labels(labels: LabelSet) -> str:
        if not labels:
            return ""
        rendered = ",".join(f'{key}="{_escape_label(value)}"' for key, value in labels)
        return f"{{{rendered}}}"


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


metrics = MetricsRegistry()


def record_http_request(
    *,
    method: str,
    route: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    labels = {"method": method, "route": route, "status_code": str(status_code)}
    metrics.increment("http_requests_total", labels)
    metrics.observe_duration("http_request_duration_seconds", duration_seconds, labels)


def record_langfuse_score_push(*, outcome: str) -> None:
    metrics.increment("langfuse_score_push_total", {"outcome": outcome})
