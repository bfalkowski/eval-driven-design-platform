import pandas as pd
import streamlit as st

from components.metrics import parse_prometheus_text, sum_metric
from components.platform_sidebar import render_platform_sidebar

st.header("Operations")

client, auth_mode = render_platform_sidebar()
st.caption(f"{client.base_url} · {auth_mode}")

try:
    samples = parse_prometheus_text(client.metrics())
except RuntimeError as exc:
    st.error(str(exc))
    st.stop()

total_requests = sum_metric(samples, "http_requests_total")
duration_count = sum_metric(samples, "http_request_duration_seconds_count")
duration_sum = sum_metric(samples, "http_request_duration_seconds_sum")
average_ms = (duration_sum / duration_count * 1000) if duration_count else 0

metrics = st.columns(3)
metrics[0].metric("HTTP requests", f"{total_requests:.0f}")
metrics[1].metric("Duration samples", f"{duration_count:.0f}")
metrics[2].metric("Avg request", f"{average_ms:.1f} ms")

if samples:
    st.dataframe(
        pd.DataFrame(samples),
        use_container_width=True,
        hide_index=True,
        column_config={
            "name": st.column_config.TextColumn("Metric", width="medium"),
            "labels": st.column_config.JsonColumn("Labels"),
            "value": st.column_config.NumberColumn("Value"),
        },
    )
else:
    st.info("No Prometheus samples yet. Hit the API once, then refresh.")
