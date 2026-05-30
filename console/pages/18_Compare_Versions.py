import pandas as pd
import streamlit as st

from components.design_context import render_design_context
from components.edd_reference import load_reference_scenario
from components.edd_views import (
    compare_versions_story,
    comparison_metric_rows,
    production_readiness_blocked,
)
from components.layout import status_pill
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Compare Versions", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    scenario = load_reference_scenario()
except (FileNotFoundError, ValueError) as exc:
    show_api_error(exc)
    st.stop()

render_design_context(scenario)

comparison = scenario.comparison_v0_v1
gate = scenario.gate_result_v1

st.markdown(
    f"""
    <div class="edd-page-header">
      <div class="edd-page-title">Compare {comparison.baseline_version_id} vs {comparison.candidate_version_id}</div>
      <div class="edd-page-meta">{status_pill(gate.overall_status or "unknown", "yellow")}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("**Story**")
for line in compare_versions_story(scenario):
    st.markdown(f"- {line}")

metric_rows = comparison_metric_rows(scenario)
if metric_rows:
    st.markdown("**Metric deltas**")
    st.dataframe(
        pd.DataFrame(metric_rows),
        use_container_width=True,
        hide_index=True,
        column_config={
            "metric": st.column_config.TextColumn("Metric", width="medium"),
            "baseline": st.column_config.TextColumn("Baseline", width="small"),
            "candidate": st.column_config.TextColumn("Candidate", width="small"),
            "delta": st.column_config.TextColumn("Delta", width="small"),
        },
    )

if comparison.regression_warnings:
    st.markdown("**Regression warnings**")
    for warning in comparison.regression_warnings:
        st.warning(warning)

if production_readiness_blocked(scenario):
    st.info(
        "Production readiness remains blocked because required tools are mock/local only."
    )

if gate.blockers:
    st.markdown("**Gate blockers**")
    for blocker in gate.blockers:
        st.markdown(f"- {blocker}")
