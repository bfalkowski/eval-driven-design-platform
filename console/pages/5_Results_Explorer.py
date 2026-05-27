import pandas as pd
import streamlit as st

from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, tenant_id = render_platform_sidebar()
render_page_header("Results Explorer", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    runs = client.list_experiment_runs(tenant_id=tenant_id).get("experiment_runs", [])
except RuntimeError as exc:
    show_api_error(exc)
    st.stop()

if not runs:
    st.info("Run an experiment on the Runs page to see evaluation results here.")
    st.stop()

run_options = {
    f"{run['candidate_version']} · {run['experiment_run_id'][:8]}": run["experiment_run_id"]
    for run in runs
}
selected_label = st.selectbox("Experiment run", options=list(run_options.keys()))
selected_run_id = run_options[selected_label]

try:
    summary = client.get_experiment_run_summary(
        tenant_id=tenant_id,
        experiment_run_id=selected_run_id,
    )
    summary_cols = st.columns(4)
    summary_cols[0].metric("Pass rate", f"{summary['pass_rate'] * 100:.0f}%")
    summary_cols[1].metric("Avg score", f"{summary['average_score']:.1f}")
    summary_cols[2].metric("Passed", summary["passed_count"])
    summary_cols[3].metric("Failed", summary["failed_count"])

    results = client.list_evaluation_results(
        tenant_id=tenant_id,
        experiment_run_id=selected_run_id,
    ).get("evaluation_results", [])
    langfuse_health = client.get_langfuse_health()
    langfuse_host = str(langfuse_health.get("host", "")).rstrip("/")
    project_name = langfuse_health.get("project_name")
    if not results:
        st.info("No evaluation results for this run.")
    else:
        rows = [
            {
                "eval_case_id": result["eval_case_id"],
                "score": result["score"],
                "passed": result["passed"],
                "langfuse_trace_id": result.get("langfuse_trace_id"),
                "langfuse_score_id": result.get("langfuse_score_id"),
                "rubric_overlap": result["judge_breakdown"].get("rubric_overlap"),
                "task_overlap": result["judge_breakdown"].get("task_overlap"),
            }
            for result in results
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if langfuse_host and project_name:
            trace_links = []
            for result in results:
                trace_id = result.get("langfuse_trace_id")
                if not trace_id:
                    continue
                trace_links.append(
                    f"- [{trace_id}]({langfuse_host}/project/{project_name}/traces/{trace_id})"
                )
            if trace_links:
                st.markdown("#### Langfuse trace links")
                st.markdown("\n".join(trace_links))
except RuntimeError as exc:
    show_api_error(exc)
