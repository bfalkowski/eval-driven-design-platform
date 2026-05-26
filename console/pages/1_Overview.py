import streamlit as st

from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, tenant_id = render_platform_sidebar()
render_page_header("Overview", client_base_url=client.base_url, auth_mode=auth_mode)

st.markdown(
    """
    **Eval Driven Design loop**

    1. **Observe** — capture issues from traces and telemetry  
    2. **Create case** — turn observations into reusable eval cases  
    3. **Run candidates** — prompts/models/workflows with deterministic scaffold  
    4. **Evaluate** — score against EvalSpec and rubric  
    5. **Decide** — compare runs and enforce quality gates  
    """
)

health_col, ready_col, specs_col, cases_col, runs_col = st.columns(5)
try:
    health = client.health()
    ready = client.ready()
    specs = client.list_eval_specs(tenant_id=tenant_id)
    cases = client.list_eval_cases(tenant_id=tenant_id)
    runs = client.list_experiment_runs(tenant_id=tenant_id)

    health_col.metric("API health", health.get("status", "unknown"))
    ready_col.metric("API ready", ready.get("status", "unknown"))
    specs_col.metric("Eval specs", len(specs.get("eval_specs", [])))
    cases_col.metric("Eval cases", len(cases.get("eval_cases", [])))
    runs_col.metric("Experiment runs", len(runs.get("experiment_runs", [])))

    latest_run = runs.get("experiment_runs", [{}])[0] if runs.get("experiment_runs") else None
    if latest_run:
        summary = client.get_experiment_run_summary(
            tenant_id=tenant_id,
            experiment_run_id=latest_run["experiment_run_id"],
        )
        st.subheader("Latest run summary")
        summary_cols = st.columns(4)
        summary_cols[0].metric("Candidate", summary.get("candidate_version", "-"))
        summary_cols[1].metric("Pass rate", f"{summary.get('pass_rate', 0) * 100:.0f}%")
        summary_cols[2].metric("Avg score", f"{summary.get('average_score', 0):.1f}")
        summary_cols[3].metric("Results", summary.get("result_count", 0))
except RuntimeError as exc:
    show_api_error(exc)

st.info("Use the sidebar pages to create specs, cases, and runs without curl.")
