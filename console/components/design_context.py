from __future__ import annotations

import streamlit as st

from components.edd_reference import ReferenceScenario
from components.edd_views import design_context_rows


def render_design_context(scenario: ReferenceScenario) -> None:
    st.markdown("#### Design context")
    for label, value in design_context_rows(scenario):
        st.markdown(f"**{label}:** `{value}`")
    st.caption("Read-only reference scenario (HLD-005). Loaded from examples/customer_escalation_triage.")
