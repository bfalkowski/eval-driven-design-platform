import pandas as pd
import streamlit as st

from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, tenant_id = render_platform_sidebar()
render_page_header("Quality Gates", client_base_url=client.base_url, auth_mode=auth_mode)

st.caption(
    "Evaluates experiment runs against EvalSpec pass thresholds. "
    "Ingested runs reuse gate results from external producers (e.g. edd-agent-lab)."
)

ingest_filter = st.text_input(
    "Filter by ingest source (optional)",
    placeholder="edd-agent-lab",
)

try:
    runs = client.list_experiment_runs(
        tenant_id=tenant_id,
        ingest_source=ingest_filter.strip() or None,
        limit=25,
    ).get("experiment_runs", [])
except RuntimeError as exc:
    show_api_error(exc)
    st.stop()

if not runs:
    st.info("No experiment runs yet. Run a candidate or publish from an external producer.")
    st.stop()

rows: list[dict] = []
for run in runs:
    try:
        gate = client.get_experiment_run_gate(
            tenant_id=tenant_id,
            experiment_run_id=run["experiment_run_id"],
        )
    except RuntimeError as exc:
        show_api_error(exc)
        st.stop()
    ingest = run.get("ingest") or {}
    rows.append(
        {
            "gate": gate["gate_status"],
            "candidate": run["candidate_version"],
            "source": gate.get("ingest_source") or ingest.get("source") or "platform",
            "evaluation": gate["evaluation_source"],
            "avg_score": gate.get("average_score"),
            "threshold": gate["pass_threshold"],
            "external_run_id": gate.get("external_run_id") or "-",
            "run_id": run["experiment_run_id"],
            "explanation": gate["gate_explanation"],
        }
    )

table = pd.DataFrame(rows)
st.dataframe(
    table[
        [
            "gate",
            "candidate",
            "source",
            "evaluation",
            "avg_score",
            "threshold",
            "external_run_id",
            "run_id",
        ]
    ],
    use_container_width=True,
    hide_index=True,
)

selected_run_id = st.selectbox(
    "Gate explanation",
    options=[row["run_id"] for row in rows],
    format_func=lambda run_id: run_id[:8],
)
selected = next(row for row in rows if row["run_id"] == selected_run_id)
st.markdown(f"**{selected['gate'].upper()}** — {selected['explanation']}")

st.markdown(
    """
    **CI usage**

    ```bash
    ./scripts/run_quality_gate.sh <experiment_run_id>
    ```
    """
)
