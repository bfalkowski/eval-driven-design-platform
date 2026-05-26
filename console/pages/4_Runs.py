import pandas as pd
import streamlit as st

from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, tenant_id = render_platform_sidebar()
render_page_header("Runs", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    specs = client.list_eval_specs(tenant_id=tenant_id).get("eval_specs", [])
except RuntimeError as exc:
    show_api_error(exc)
    st.stop()

if not specs:
    st.info("Create an eval spec and at least one case before running experiments.")
    st.stop()

spec_options = {f"{spec['name']} ({spec['eval_spec_id'][:8]})": spec["eval_spec_id"] for spec in specs}
selected_label = st.selectbox("Eval spec", options=list(spec_options.keys()))
selected_spec_id = spec_options[selected_label]

try:
    cases = client.list_eval_cases(
        tenant_id=tenant_id,
        eval_spec_id=selected_spec_id,
    ).get("eval_cases", [])
except RuntimeError as exc:
    show_api_error(exc)
    st.stop()

left, right = st.columns([0.45, 0.55], vertical_alignment="top")

with left:
    st.subheader("Run candidate")
    if not cases:
        st.warning("No cases for this spec. Add cases on the Eval Cases page.")
    else:
        case_options = {
            f"{case['name']} ({case['eval_case_id'][:8]})": case["eval_case_id"] for case in cases
        }
        with st.form("create-experiment-run"):
            candidate_version = st.text_input("Candidate version", value="prompt_v4")
            selected_case_labels = st.multiselect(
                "Cases to run",
                options=list(case_options.keys()),
                default=list(case_options.keys()),
            )
            submitted = st.form_submit_button("Run experiment", type="primary")
        if submitted:
            if not selected_case_labels:
                st.error("Select at least one case.")
            else:
                try:
                    run = client.create_experiment_run(
                        tenant_id=tenant_id,
                        eval_spec_id=selected_spec_id,
                        candidate_version=candidate_version.strip(),
                        eval_case_ids=[case_options[label] for label in selected_case_labels],
                    )
                    summary = client.get_experiment_run_summary(
                        tenant_id=tenant_id,
                        experiment_run_id=run["experiment_run_id"],
                    )
                    st.success(f"Run {run['experiment_run_id']} completed.")
                    metric_cols = st.columns(3)
                    metric_cols[0].metric("Pass rate", f"{summary['pass_rate'] * 100:.0f}%")
                    metric_cols[1].metric("Avg score", f"{summary['average_score']:.1f}")
                    metric_cols[2].metric("Results", summary["result_count"])
                except RuntimeError as exc:
                    show_api_error(exc)

with right:
    st.subheader("Recent runs")
    try:
        runs = client.list_experiment_runs(
            tenant_id=tenant_id,
            eval_spec_id=selected_spec_id,
        ).get("experiment_runs", [])
        if not runs:
            st.info("No experiment runs yet.")
        else:
            st.dataframe(
                pd.DataFrame(runs)[
                    ["candidate_version", "status", "result_count", "experiment_run_id"]
                ],
                use_container_width=True,
                hide_index=True,
            )
    except RuntimeError as exc:
        show_api_error(exc)
