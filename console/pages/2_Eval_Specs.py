import pandas as pd
import streamlit as st

from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header, show_api_error

client, auth_mode, tenant_id = render_platform_sidebar()
render_page_header("Eval Specs", client_base_url=client.base_url, auth_mode=auth_mode)

left, right = st.columns([0.45, 0.55], vertical_alignment="top")

with left:
    st.subheader("Create spec")
    with st.form("create-eval-spec"):
        name = st.text_input("Name", value="Support workflow quality")
        description = st.text_area("Description", value="Checks support answer quality.")
        rubric = st.text_area(
            "Rubric",
            value="Mention empathy, resolution steps, failures, latency, or quality.",
        )
        pass_threshold = st.slider("Pass threshold", min_value=0, max_value=100, value=70)
        submitted = st.form_submit_button("Create spec", type="primary")
    if submitted:
        try:
            created = client.create_eval_spec(
                tenant_id=tenant_id,
                name=name.strip(),
                description=description.strip() or None,
                rubric=rubric.strip(),
                pass_threshold=float(pass_threshold),
            )
            st.success(f"Created spec {created['eval_spec_id']}")
        except RuntimeError as exc:
            show_api_error(exc)

with right:
    st.subheader("Specs")
    try:
        response = client.list_eval_specs(tenant_id=tenant_id)
        specs = response.get("eval_specs", [])
        if not specs:
            st.info("No eval specs yet.")
        else:
            frame = pd.DataFrame(specs)
            st.dataframe(
                frame[["name", "version", "pass_threshold", "eval_spec_id"]],
                use_container_width=True,
                hide_index=True,
            )
    except RuntimeError as exc:
        show_api_error(exc)
