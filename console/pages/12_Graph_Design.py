import pandas as pd
import streamlit as st

from components.design_context import render_design_context
from components.edd_reference import GraphDesignBundle, load_reference_scenario
from components.edd_views import (
    graph_design_diff,
    graph_design_summary,
    graph_node_rows,
)
from components.layout import status_pill
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Graph Design", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    scenario = load_reference_scenario()
except (FileNotFoundError, ValueError) as exc:
    show_api_error(exc)
    st.stop()

render_design_context(scenario)

version_label = st.selectbox(
    "Graph version",
    options=["v1 (evidence-first triage)", "v0 (single-pass baseline)"],
    index=0,
)
selected: GraphDesignBundle = (
    scenario.graph_design_v1 if version_label.startswith("v1") else scenario.graph_design_v0
)

summary = graph_design_summary(selected)
st.markdown(
    f"""
    <div class="edd-page-header">
      <div class="edd-page-title">{summary["name"]}</div>
      <div class="edd-page-meta">
        {status_pill(summary["version"], "blue")}
        {status_pill(summary["status"], "green" if summary["status"] == "active" else "yellow")}
        {status_pill(f"{summary['node_count']} nodes", "blue")}
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

meta_left, meta_right = st.columns(2, vertical_alignment="top")
with meta_left:
    st.markdown(f"**Graph ID:** `{summary['id']}`")
    st.write(summary["description"])
with meta_right:
    if summary["source_version"]:
        st.markdown(f"**Source version:** `{summary['source_version']}`")
    if summary["fix_plan_id"]:
        st.markdown(f"**Fix plan:** `{summary['fix_plan_id']}`")
    if selected.design.flow_order:
        st.markdown("**Flow order:**")
        st.code(" → ".join(selected.design.flow_order), language=None)

st.subheader("Nodes")
node_frame = pd.DataFrame(graph_node_rows(selected))
st.dataframe(
    node_frame,
    use_container_width=True,
    hide_index=True,
    column_config={
        "id": st.column_config.TextColumn("Node ID", width="medium"),
        "purpose": st.column_config.TextColumn("Purpose", width="large"),
        "behavior_rules": st.column_config.TextColumn("Rules", width="medium"),
        "information_requirements": st.column_config.TextColumn("Information", width="medium"),
        "tool_requirements": st.column_config.TextColumn("Tools", width="medium"),
        "tool_mode": st.column_config.TextColumn("Tool mode", width="small"),
        "active_tool_binding": st.column_config.TextColumn("Binding", width="medium"),
        "production_blocker": st.column_config.CheckboxColumn("Prod blocker"),
        "failure_packets": st.column_config.TextColumn("Failures addressed", width="medium"),
    },
)

st.subheader("v0 → v1 diff")
diff = graph_design_diff(scenario.graph_design_v0, scenario.graph_design_v1)
diff_cols = st.columns(3)
diff_cols[0].metric("Added nodes", len(diff["added_nodes"]))
diff_cols[1].metric("Removed nodes", len(diff["removed_nodes"]))
diff_cols[2].metric("Shared nodes", len(diff["shared_nodes"]))

st.markdown("**Added in v1**")
st.code("\n".join(diff["added_nodes"]) or "(none)", language=None)
st.markdown("**Removed from v0**")
st.code("\n".join(diff["removed_nodes"]) or "(none)", language=None)

st.caption(
    "v1 adds evidence collection, normalization, facts/hypotheses separation, "
    "and customer-safe update review in response to fp-v0-unsupported-root-cause."
)
