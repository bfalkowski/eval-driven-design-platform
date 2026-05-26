import streamlit as st

from components.layout import integration_card, metric_card, status_pill
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Langfuse", client_base_url=client.base_url, auth_mode=auth_mode)

st.markdown(
    """
    Langfuse is the observability data plane. EDD connects optionally for trace inspection,
    score push, and trace-to-case import in later phases.
    """
)

try:
    health = client.get_langfuse_health()
    status = health.get("status", "unknown")
    pill_map = {
        "healthy": ("Connected", "green"),
        "disabled": ("Disabled", "blue"),
        "misconfigured": ("Misconfigured", "yellow"),
        "degraded": ("Degraded", "yellow"),
        "unreachable": ("Unreachable", "red"),
    }
    pill_label, pill_status = pill_map.get(status, ("Unknown", "blue"))

    metric_cols = st.columns(4)
    with metric_cols[0]:
        metric_card("Status", status.replace("_", " ").title(), health.get("message", ""))
    with metric_cols[1]:
        metric_card("Host", health.get("host", "-").replace("http://", ""), "Configured Langfuse URL")
    with metric_cols[2]:
        projects = health.get("project_count")
        metric_card("Projects", str(projects) if projects is not None else "-", health.get("project_name") or "")
    with metric_cols[3]:
        auth_value = health.get("authenticated")
        auth_label = "Yes" if auth_value is True else "No" if auth_value is False else "-"
        metric_card("API keys", auth_label, "Public/secret key validation")

    integration_card(
        "Langfuse integration",
        health.get("message", "No status message returned."),
        pill_label,
        pill_status,
    )

    st.markdown("### Planned next steps")
    st.markdown(
        f"""
        - Phase 5: push evaluation scores after experiment runs {status_pill("Planned", "blue")}
        - Phase 6: import Langfuse traces as EvalCases {status_pill("Planned", "blue")}
        """
        ,
        unsafe_allow_html=True,
    )
except RuntimeError as exc:
    show_api_error(exc)
