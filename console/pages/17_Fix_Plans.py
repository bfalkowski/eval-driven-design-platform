import streamlit as st

from components.design_context import render_design_context
from components.edd_reference import load_reference_scenario
from components.edd_views import fix_plan_sections
from components.layout import status_pill
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Fix Plans", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    scenario = load_reference_scenario()
except (FileNotFoundError, ValueError) as exc:
    show_api_error(exc)
    st.stop()

render_design_context(scenario)

plan = scenario.fix_plan_v1
sections = fix_plan_sections(scenario)

st.markdown(
    f"""
    <div class="edd-page-header">
      <div class="edd-page-title">Fix plan for {scenario.agent_target.name}</div>
      <div class="edd-page-meta">{status_pill(plan.status, "blue")}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(f"**ID:** `{plan.id}`")
st.markdown(
    f"**Version path:** `{plan.source_version_id or 'v0-baseline'}` → "
    f"`{plan.target_version_label or 'v1-evidence-triage-graph'}`"
)

for title, items in sections.items():
    with st.expander(title, expanded=title == "Rules addressed"):
        if not items:
            st.caption("None")
            continue
        for item in items:
            st.markdown(f"- {item}")
