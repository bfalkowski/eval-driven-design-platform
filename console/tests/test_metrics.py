from components.metrics import parse_prometheus_text, sum_metric


def test_parse_prometheus_text() -> None:
    text = """
# HELP http_requests_total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",route="/v1/health",status_code="200"} 3
"""
    samples = parse_prometheus_text(text)
    assert len(samples) == 1
    assert samples[0]["name"] == "http_requests_total"
    assert samples[0]["value"] == 3.0


def test_sum_metric_with_labels() -> None:
    samples = [
        {"name": "http_requests_total", "labels": {"status_code": "200"}, "value": 2.0},
        {"name": "http_requests_total", "labels": {"status_code": "500"}, "value": 1.0},
    ]
    assert sum_metric(samples, "http_requests_total", {"status_code": "200"}) == 2.0
