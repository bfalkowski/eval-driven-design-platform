import streamlit as st

from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Quality Gates", client_base_url=client.base_url, auth_mode=auth_mode)

st.info(
    "Quality gates arrive in Phase 7. They will evaluate experiment summaries against "
    "EvalSpec thresholds and support CI-style pass/fail checks."
)
st.markdown(
    """
    **Planned capabilities**

    - Threshold evaluation from EvalSpec pass criteria  
    - `scripts/run_quality_gate.sh` for local and CI use  
    - Gate history linked to experiment runs  
    """
)
