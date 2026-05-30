import streamlit as st

from components.design_context import render_design_context
from components.edd_reference import load_reference_scenario
from components.edd_views import failure_packet_summary
from components.layout import status_pill
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Failure Packets", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    scenario = load_reference_scenario()
except (FileNotFoundError, ValueError) as exc:
    show_api_error(exc)
    st.stop()

render_design_context(scenario)

packet = scenario.failure_packet_v0
summary = failure_packet_summary(scenario)

st.markdown(
    f"""
    <div class="edd-page-header">
      <div class="edd-page-title">Failure packet for {scenario.agent_target.name}</div>
      <div class="edd-page-meta">{status_pill(summary["severity"] or "unknown", "red")}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(f"**ID:** `{summary['id']}`")
st.markdown(f"**Failed rule:** `{summary['failed_rule']}`")
st.markdown(f"**Version:** `{summary['version']}`")

if packet.suspected_cause:
    st.markdown("**Suspected cause**")
    st.info(packet.suspected_cause.strip())

st.markdown("**Observed behavior**")
st.error(summary["observed_behavior"].strip() if summary["observed_behavior"] else "—")

st.markdown("**Expected behavior**")
st.success(summary["expected_behavior"].strip() if summary["expected_behavior"] else "—")

if summary["recommended_fix"]:
    st.markdown("**Recommended fix**")
    st.markdown(summary["recommended_fix"].strip())

if packet.trace_link_ids:
    st.markdown("**Trace links**")
    for trace_id in packet.trace_link_ids:
        st.markdown(f"- `{trace_id}`")
