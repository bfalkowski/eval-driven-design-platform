import streamlit as st

from components.design_context import render_design_context
from components.edd_reference import load_reference_scenario
from components.edd_views import target_detail_sections
from components.layout import status_pill
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Agent Target", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    scenario = load_reference_scenario()
except (FileNotFoundError, ValueError) as exc:
    show_api_error(exc)
    st.stop()

render_design_context(scenario)

target = scenario.agent_target
st.markdown(
    f"""
    <div class="edd-page-header">
      <div class="edd-page-title">{target.name}</div>
      <div class="edd-page-meta">
        {status_pill(target.version, "blue")}
        {status_pill("read-only", "yellow")}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

left, right = st.columns(2, vertical_alignment="top")

with left:
    st.subheader("Agent")
    st.markdown(f"**ID:** `{scenario.agent.id}`")
    st.markdown(f"**Name:** {scenario.agent.name}")
    st.caption(scenario.agent.description.strip())

with right:
    st.subheader("Target metadata")
    st.markdown(f"**Target ID:** `{target.id}`")
    st.markdown(f"**Agent ID:** `{target.agent_id}`")
    st.markdown(f"**Version:** `{target.version}`")

sections = target_detail_sections(scenario)
for title, items in sections.items():
    st.subheader(title)
    if len(items) == 1 and title == "Purpose":
        st.write(items[0])
    else:
        st.markdown("\n".join(f"- {item}" for item in items))
