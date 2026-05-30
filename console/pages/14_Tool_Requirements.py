import pandas as pd
import streamlit as st

from components.design_context import render_design_context
from components.edd_reference import load_reference_scenario
from components.edd_views import tool_requirements_rows
from components.layout import status_pill
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Tool Requirements", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    scenario = load_reference_scenario()
except (FileNotFoundError, ValueError) as exc:
    show_api_error(exc)
    st.stop()

render_design_context(scenario)

st.markdown(
    f"""
    <div class="edd-page-header">
      <div class="edd-page-title">Tools for {scenario.agent_target.name}</div>
      <div class="edd-page-meta">{status_pill(f"{len(scenario.tool_requirements)} requirements", "blue")}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

rows = tool_requirements_rows(scenario)
st.dataframe(
    pd.DataFrame(rows),
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.TextColumn("Requirement ID", width="medium"),
        "suggested_tool_name": st.column_config.TextColumn("Suggested tool", width="medium"),
        "information_requirement": st.column_config.TextColumn("Information", width="medium"),
        "access_mode": st.column_config.TextColumn("Access mode", width="small"),
        "required_for_demo": st.column_config.CheckboxColumn("Demo"),
        "required_for_production": st.column_config.CheckboxColumn("Production"),
        "implementation_status": st.column_config.TextColumn("Implementation", width="small"),
        "purpose": st.column_config.TextColumn("Purpose", width="large"),
    },
)

for item in scenario.tool_requirements:
    with st.expander(f"{item.suggested_tool_name} ({item.id})"):
        st.markdown(
            f"{status_pill(item.access_mode, 'blue')} "
            f"{status_pill('demo required' if item.required_for_demo else 'demo optional', 'green' if item.required_for_demo else 'yellow')} "
            f"{status_pill('production required' if item.required_for_production else 'production optional', 'green' if item.required_for_production else 'yellow')}"
        )
        st.markdown(f"**Information requirement:** `{item.information_requirement_id}`")
        st.write(item.purpose.strip())
