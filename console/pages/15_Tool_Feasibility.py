import pandas as pd
import streamlit as st

from components.design_context import render_design_context
from components.edd_reference import load_reference_scenario
from components.edd_views import production_readiness_blocked, tool_feasibility_rows
from components.layout import status_pill
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Tool Feasibility", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    scenario = load_reference_scenario()
except (FileNotFoundError, ValueError) as exc:
    show_api_error(exc)
    st.stop()

render_design_context(scenario)

if production_readiness_blocked(scenario):
    st.warning(
        "Production readiness is blocked because required tools are not live. "
        "This version may be suitable for demo or offline evaluation only."
    )

st.markdown(
    f"""
    <div class="edd-page-header">
      <div class="edd-page-title">Feasibility for {scenario.agent_target.name}</div>
      <div class="edd-page-meta">{status_pill(f"{len(scenario.tool_feasibility)} reviews", "blue")}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

rows = tool_feasibility_rows(scenario)
st.dataframe(
    pd.DataFrame(rows),
    use_container_width=True,
    hide_index=True,
    column_config={
        "requirement_id": st.column_config.TextColumn("Requirement", width="medium"),
        "suggested_tool_name": st.column_config.TextColumn("Suggested tool", width="medium"),
        "implementation_status": st.column_config.TextColumn("Status", width="small"),
        "feasibility_status": st.column_config.TextColumn("Feasibility", width="small"),
        "demo_ready": st.column_config.CheckboxColumn("Demo ready"),
        "production_ready": st.column_config.CheckboxColumn("Production ready"),
        "mvp_strategy": st.column_config.TextColumn("MVP strategy", width="medium"),
        "production_strategy": st.column_config.TextColumn("Production strategy", width="medium"),
        "blocker": st.column_config.TextColumn("Blocker", width="medium"),
        "risks": st.column_config.TextColumn("Risks", width="large"),
    },
)

for review in scenario.tool_feasibility:
    status = "green" if review.production_ready else "yellow" if review.demo_ready else "red"
    with st.expander(f"{review.suggested_tool_name} ({review.requirement_id})"):
        st.markdown(
            f"{status_pill(review.implementation_status, 'blue')} "
            f"{status_pill(review.feasibility_status, status)} "
            f"{status_pill('demo ready' if review.demo_ready else 'demo blocked', 'green' if review.demo_ready else 'red')} "
            f"{status_pill('production ready' if review.production_ready else 'production blocked', 'green' if review.production_ready else 'red')}"
        )
        st.markdown(f"**MVP strategy:** `{review.mvp_strategy}`")
        st.markdown(f"**Production strategy:** `{review.production_strategy}`")
        if review.risks:
            st.markdown("**Risks:**")
            for risk in review.risks:
                st.markdown(f"- {risk}")
