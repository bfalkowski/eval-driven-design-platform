import pandas as pd
import streamlit as st

from components.design_context import render_design_context
from components.edd_reference import load_reference_scenario
from components.edd_views import information_requirements_rows
from components.layout import status_pill
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Information Requirements", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    scenario = load_reference_scenario()
except (FileNotFoundError, ValueError) as exc:
    show_api_error(exc)
    st.stop()

render_design_context(scenario)

st.markdown(
    f"""
    <div class="edd-page-header">
      <div class="edd-page-title">Information for {scenario.agent_target.name}</div>
      <div class="edd-page-meta">{status_pill(f"{len(scenario.information_requirements)} requirements", "blue")}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

rows = information_requirements_rows(scenario)
st.dataframe(
    pd.DataFrame(rows),
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.TextColumn("Requirement ID", width="medium"),
        "name": st.column_config.TextColumn("Name", width="medium"),
        "behavior_rules": st.column_config.TextColumn("Required by rules", width="medium"),
        "required": st.column_config.CheckboxColumn("Required"),
        "sensitivity": st.column_config.TextColumn("Sensitivity", width="small"),
        "tool_requirements": st.column_config.TextColumn("Tool requirements", width="medium"),
        "description": st.column_config.TextColumn("Description", width="large"),
    },
)

for item in scenario.information_requirements:
    with st.expander(f"{item.name} ({item.id})"):
        st.markdown(
            f"{status_pill('required' if item.required else 'optional', 'red' if item.required else 'yellow')} "
            f"{status_pill(item.sensitivity, 'blue')}"
        )
        st.markdown("**Behavior rules:** " + ", ".join(f"`{rule_id}`" for rule_id in item.behavior_rule_ids))
        st.write(item.description.strip())
