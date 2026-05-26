import streamlit as st

from components.platform_sidebar import render_platform_sidebar
from components.ui import render_page_header

client, auth_mode, _tenant_id = render_platform_sidebar()
render_page_header("Langfuse", client_base_url=client.base_url, auth_mode=auth_mode)

st.info(
    "Langfuse integration arrives in Phases 4–6. EDD will connect optionally for trace "
    "inspection, score push, and trace-to-case import."
)
st.markdown(
    """
    **Planned capabilities**

    - `/v1/integrations/langfuse/health` status check  
    - Push evaluation scores after experiment runs  
    - Import Langfuse traces as EvalCases  
    """
)
