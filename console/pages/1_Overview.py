import streamlit as st

from components.platform_sidebar import render_platform_sidebar

st.header("Overview")

client, auth_mode = render_platform_sidebar()

st.markdown(
    """
    **Eval Driven Design loop**

    1. **Observe** — capture issues from traces and telemetry  
    2. **Create case** — turn observations into reusable eval cases  
    3. **Run candidates** — prompts/models/workflows with deterministic scaffold  
    4. **Evaluate** — score against EvalSpec and rubric  
    5. **Decide** — compare runs and enforce quality gates  
    """
)

st.caption(f"{client.base_url} · {auth_mode}")

col1, col2, col3 = st.columns(3)
with col1:
    try:
        health = client.health()
        st.metric("API health", health.get("status", "unknown"))
    except RuntimeError as exc:
        st.error(f"Health check failed: {exc}")

with col2:
    try:
        ready = client.ready()
        st.metric("API ready", ready.get("status", "unknown"))
    except RuntimeError as exc:
        st.error(f"Ready check failed: {exc}")

with col3:
    try:
        metrics_text = client.metrics()
        request_count = metrics_text.count("http_requests_total")
        st.metric("Metrics", "available" if request_count else "empty")
    except RuntimeError as exc:
        st.error(f"Metrics check failed: {exc}")

st.info(
    "Platform spine imported (Phase 0.5). Eval specs, cases, and Langfuse integration "
    "arrive in Phases 1–4."
)
