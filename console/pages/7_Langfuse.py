import streamlit as st

from components.layout import integration_card, metric_card
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Langfuse", client_base_url=client.base_url, auth_mode=auth_mode)

st.markdown(
    """
    Langfuse is the observability data plane. When Langfuse is enabled, each experiment run
    creates a trace and pushes a score. You can also import an existing trace as an EvalCase.
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

    st.markdown("### Trace import")
    trace_id = st.text_input("Langfuse trace ID", value="", placeholder="trace_...")
    preview_clicked = st.button("Preview trace")

    if preview_clicked and trace_id.strip():
        preview = client.get_langfuse_trace(trace_id=trace_id.strip()).get("trace", {})
        st.success("Trace loaded.")
        st.json(preview)

    if trace_id.strip():
        specs = client.list_eval_specs(tenant_id=_tenant_id).get("eval_specs", [])
        if specs:
            spec_options = {
                f"{spec['name']} ({spec['version']}) · {spec['eval_spec_id'][:8]}": spec["eval_spec_id"]
                for spec in specs
            }
            selected_spec_label = st.selectbox("EvalSpec", options=list(spec_options.keys()))
            selected_spec_id = spec_options[selected_spec_label]
            case_name = st.text_input("Case name (optional)", value="")
            notes = st.text_area("Notes (optional)", value="")
            if st.button("Import trace as EvalCase", type="primary"):
                created = client.import_langfuse_trace_case(
                    tenant_id=_tenant_id,
                    eval_spec_id=selected_spec_id,
                    trace_id=trace_id.strip(),
                    name=case_name.strip() or None,
                    notes=notes.strip() or None,
                )
                st.success(f"Created EvalCase {created['eval_case_id']}")
        else:
            st.info("Create an EvalSpec first to import a trace as an EvalCase.")
except RuntimeError as exc:
    show_api_error(exc)
