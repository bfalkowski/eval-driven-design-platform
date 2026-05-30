import pandas as pd
import streamlit as st

from components.design_context import render_design_context
from components.edd_reference import load_reference_scenario
from components.edd_views import eval_gates_rows, eval_metrics_rows
from components.layout import status_pill
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Eval Contract", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    scenario = load_reference_scenario()
except (FileNotFoundError, ValueError) as exc:
    show_api_error(exc)
    st.stop()

render_design_context(scenario)

contract = scenario.eval_contract
st.markdown(
    f"""
    <div class="edd-page-header">
      <div class="edd-page-title">{contract.name}</div>
      <div class="edd-page-meta">
        {status_pill(contract.version, "blue")}
        {status_pill(f"{len(contract.metrics)} metrics", "green")}
        {status_pill(f"{len(contract.gates)} gates", "yellow")}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Metrics")
metrics_frame = pd.DataFrame(eval_metrics_rows(scenario))
st.dataframe(
    metrics_frame,
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.TextColumn("Metric ID", width="medium"),
        "name": st.column_config.TextColumn("Name", width="medium"),
        "scale": st.column_config.TextColumn("Scale", width="small"),
        "behavior_rules": st.column_config.TextColumn("Behavior rules", width="medium"),
        "rubric": st.column_config.TextColumn("Rubric", width="large"),
    },
)

st.subheader("Gates")
gates_frame = pd.DataFrame(eval_gates_rows(scenario))
st.dataframe(
    gates_frame,
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.TextColumn("Gate ID", width="medium"),
        "name": st.column_config.TextColumn("Name", width="medium"),
        "type": st.column_config.TextColumn("Type", width="small"),
        "category": st.column_config.TextColumn("Category", width="small"),
        "condition": st.column_config.TextColumn("Condition", width="large"),
    },
)

for metric in contract.metrics:
    with st.expander(f"{metric.name} ({metric.id})"):
        st.markdown(f"**Scale:** {metric.scale_min:g}–{metric.scale_max:g}")
        st.markdown("**Behavior rules:** " + ", ".join(f"`{rule_id}`" for rule_id in metric.behavior_rule_ids))
        st.write(metric.rubric.strip())
