import pandas as pd
import streamlit as st

from components.design_context import render_design_context
from components.edd_reference import load_reference_scenario
from components.edd_views import behavior_rules_rows
from components.layout import status_pill
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Behavior Rules", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    scenario = load_reference_scenario()
except (FileNotFoundError, ValueError) as exc:
    show_api_error(exc)
    st.stop()

render_design_context(scenario)

st.markdown(
    f"""
    <div class="edd-page-header">
      <div class="edd-page-title">Rules for {scenario.agent_target.name}</div>
      <div class="edd-page-meta">{status_pill(f"{len(scenario.behavior_rules)} rules", "blue")}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

rows = behavior_rules_rows(scenario)
st.dataframe(
    pd.DataFrame(rows),
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.TextColumn("Rule ID", width="medium"),
        "name": st.column_config.TextColumn("Name", width="medium"),
        "severity": st.column_config.TextColumn("Severity", width="small"),
        "category": st.column_config.TextColumn("Category", width="small"),
        "description": st.column_config.TextColumn("Description", width="large"),
    },
)

for rule in scenario.behavior_rules:
    severity = rule.severity.lower()
    pill_status = "red" if severity == "critical" else "yellow" if severity == "high" else "blue"
    with st.expander(f"{rule.name} ({rule.id})"):
        st.markdown(
            f"{status_pill(rule.severity, pill_status)} "
            f"{status_pill(rule.category, 'blue')}"
        )
        st.write(rule.description.strip())
