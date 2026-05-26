import streamlit as st

from components.layout import integration_card, metric_card, run_card, workflow_loop
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_overview_header, show_api_error

client, auth_mode, tenant_id = render_platform_sidebar()
render_overview_header(client_base_url=client.base_url, auth_mode=auth_mode)
workflow_loop()

metric_cols = st.columns(4)
try:
    health = client.health()
    ready = client.ready()
    specs = client.list_eval_specs(tenant_id=tenant_id)
    cases = client.list_eval_cases(tenant_id=tenant_id)
    runs = client.list_experiment_runs(tenant_id=tenant_id)

    spec_count = len(specs.get("eval_specs", []))
    case_count = len(cases.get("eval_cases", []))
    run_list = runs.get("experiment_runs", [])

    api_status = "Healthy" if health.get("status") == "ok" else "Unknown"

    latest_pass_rate = "-"
    latest_candidate = "No runs yet"
    if run_list:
        latest_summary = client.get_experiment_run_summary(
            tenant_id=tenant_id,
            experiment_run_id=run_list[0]["experiment_run_id"],
        )
        latest_pass_rate = f"{latest_summary.get('pass_rate', 0) * 100:.0f}%"
        latest_candidate = latest_summary.get("candidate_version", "-")

    with metric_cols[0]:
        metric_card("Eval Specs", str(spec_count), "Definitions of success")
    with metric_cols[1]:
        metric_card("Eval Cases", str(case_count), "Reusable regression cases")
    with metric_cols[2]:
        metric_card("Latest Pass Rate", latest_pass_rate, latest_candidate)
    with metric_cols[3]:
        metric_card("API", api_status, ready.get("status", "unknown"))

    st.markdown("## Recent Experiment Runs")
    if not run_list:
        st.info("No experiment runs yet. Create a spec and case, then run a candidate on the Runs page.")
    else:
        for run in run_list[:3]:
            summary = client.get_experiment_run_summary(
                tenant_id=tenant_id,
                experiment_run_id=run["experiment_run_id"],
            )
            failed_count = summary.get("failed_count", 0)
            status_label = "Passed" if failed_count == 0 else "Failed"
            status = "green" if failed_count == 0 else "red"
            subtitle = (
                f"{summary.get('result_count', 0)} cases · "
                f"{summary.get('pass_rate', 0) * 100:.0f}% pass rate · "
                f"avg score {summary.get('average_score', 0):.1f}"
            )
            run_card(
                f"{summary.get('candidate_version', '-')} · {run['experiment_run_id'][:8]}",
                subtitle,
                status_label,
                status,
            )

    st.markdown("## Integrations")
    langfuse = client.get_langfuse_health()
    langfuse_status = langfuse.get("status", "unknown")
    langfuse_pills = {
        "healthy": ("Connected", "green"),
        "disabled": ("Disabled", "blue"),
        "misconfigured": ("Misconfigured", "yellow"),
        "degraded": ("Degraded", "yellow"),
        "unreachable": ("Unreachable", "red"),
    }
    langfuse_label, langfuse_pill = langfuse_pills.get(langfuse_status, ("Unknown", "blue"))
    integration_card(
        "Langfuse",
        langfuse.get("message", "Langfuse integration status unavailable."),
        langfuse_label,
        langfuse_pill,
    )
except RuntimeError as exc:
    show_api_error(exc)
