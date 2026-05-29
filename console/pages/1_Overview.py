import streamlit as st

from components.layout import integration_card, metric_card, run_card, workflow_loop
from components.platform_sidebar import render_platform_sidebar
from components.ui import render_overview_header, show_api_error

client, auth_mode, tenant_id = render_platform_sidebar()
render_overview_header(client_base_url=client.base_url, auth_mode=auth_mode)
workflow_loop()


def _gate_pill(gate_status: str) -> tuple[str, str]:
    mapping = {
        "pass": ("Pass", "green"),
        "fail": ("Fail", "red"),
        "insufficient_evidence": ("Insufficient", "yellow"),
    }
    return mapping.get(gate_status, (gate_status.title(), "blue"))


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

    latest_gate = "-"
    latest_candidate = "No runs yet"
    if run_list:
        latest_run = run_list[0]
        latest_gate_info = client.get_experiment_run_gate(
            tenant_id=tenant_id,
            experiment_run_id=latest_run["experiment_run_id"],
        )
        latest_gate = latest_gate_info.get("gate_status", "-")
        source = (
            latest_gate_info.get("ingest_source")
            or (latest_run.get("ingest") or {}).get("source")
            or "platform"
        )
        latest_candidate = f"{latest_gate_info.get('candidate_version', '-')} · {source}"

    with metric_cols[0]:
        metric_card("Eval Specs", str(spec_count), "Definitions of success")
    with metric_cols[1]:
        metric_card("Eval Cases", str(case_count), "Reusable regression cases")
    with metric_cols[2]:
        metric_card("Latest Gate", latest_gate, latest_candidate)
    with metric_cols[3]:
        metric_card("API", api_status, ready.get("status", "unknown"))

    st.markdown("## Recent Experiment Runs")
    if not run_list:
        st.info("No experiment runs yet. Create a spec and case, then run a candidate on the Runs page.")
    else:
        for run in run_list[:3]:
            gate = client.get_experiment_run_gate(
                tenant_id=tenant_id,
                experiment_run_id=run["experiment_run_id"],
            )
            ingest = run.get("ingest") or {}
            source = gate.get("ingest_source") or ingest.get("source") or "platform"
            status_label, status = _gate_pill(gate.get("gate_status", "unknown"))
            subtitle = (
                f"{source} · {gate.get('evaluation_source', 'unknown')} · "
                f"{gate.get('gate_explanation', '')[:80]}"
            )
            run_card(
                f"{gate.get('candidate_version', '-')} · {run['experiment_run_id'][:8]}",
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
    ingest_count = sum(1 for run in run_list if run.get("ingest"))
    integration_card(
        "External run ingest",
        f"{ingest_count} of {len(run_list)} recent run(s) include ingest provenance. "
        "Publish via POST /v1/integrations/runs/publish.",
        "Active" if ingest_count else "Ready",
        "green" if ingest_count else "blue",
    )
except RuntimeError as exc:
    show_api_error(exc)
