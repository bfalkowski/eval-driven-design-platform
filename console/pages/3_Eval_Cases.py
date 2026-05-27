import pandas as pd
import streamlit as st

from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, tenant_id = render_platform_sidebar()
render_page_header("Eval Cases", client_base_url=client.base_url, auth_mode=auth_mode)

try:
    specs_response = client.list_eval_specs(tenant_id=tenant_id)
    specs = specs_response.get("eval_specs", [])
except RuntimeError as exc:
    show_api_error(exc)
    st.stop()

if not specs:
    st.info("Create an eval spec first on the Eval Specs page.")
    st.stop()

spec_options = {f"{spec['name']} ({spec['eval_spec_id'][:8]})": spec["eval_spec_id"] for spec in specs}
selected_label = st.selectbox("Eval spec", options=list(spec_options.keys()))
selected_spec_id = spec_options[selected_label]

left, right = st.columns([0.45, 0.55], vertical_alignment="top")

with left:
    st.subheader("Create case")
    with st.form("create-eval-case"):
        name = st.text_input("Case name", value="Refund escalation")
        task = st.text_area(
            "Task",
            value="Handle refund request with empathy and clear next steps.",
            height=120,
        )
        notes = st.text_input("Notes", value="Manual console case")
        submitted = st.form_submit_button("Create case", type="primary")
    if submitted:
        try:
            created = client.create_eval_case(
                tenant_id=tenant_id,
                eval_spec_id=selected_spec_id,
                name=name.strip(),
                task=task.strip(),
                notes=notes.strip() or None,
            )
            st.success(f"Created case {created['eval_case_id']}")
        except RuntimeError as exc:
            show_api_error(exc)

with right:
    st.subheader("Cases")
    try:
        response = client.list_eval_cases(
            tenant_id=tenant_id,
            eval_spec_id=selected_spec_id,
        )
        cases = response.get("eval_cases", [])
        if not cases:
            st.info("No cases for this spec yet.")
        else:
            rows = [
                {
                    "name": case["name"],
                    "source": case["source"],
                    "langfuse_trace_id": case.get("langfuse_trace_id"),
                    "task": case["input_payload"].get("task", ""),
                    "eval_case_id": case["eval_case_id"],
                }
                for case in cases
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    except RuntimeError as exc:
        show_api_error(exc)
