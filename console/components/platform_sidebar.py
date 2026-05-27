from __future__ import annotations

import streamlit as st

from components.api_client import ServiceClient, get_api_base_url
from components.layout import load_css, sidebar_brand


def _state_default(key: str, default: str) -> str:
    value = st.session_state.get(key)
    if isinstance(value, str):
        return value
    return default


def render_platform_sidebar() -> tuple[ServiceClient, str, str | None]:
    load_css()
    sidebar_brand()
    st.sidebar.markdown("---")
    api_base_url = st.sidebar.text_input(
        "API base URL",
        value=_state_default("api_base_url", get_api_base_url()),
        key="api_base_url",
    )
    bearer_token = st.sidebar.text_input(
        "Bearer token",
        value=_state_default("bearer_token", ""),
        type="password",
        key="bearer_token",
    )
    tenant_id: str | None = None
    if not bearer_token.strip():
        tenant_id = (
            st.sidebar.text_input(
                "Tenant",
                value=_state_default("tenant_id", "tenant-a"),
                key="tenant_id",
            ).strip()
            or None
        )
    if st.sidebar.button("Refresh", type="primary"):
        st.rerun()

    client = ServiceClient(
        api_base_url.strip(),
        bearer_token=bearer_token.strip() or None,
    )
    auth_mode = "bearer token" if bearer_token.strip() else "tenant fallback"
    st.sidebar.caption(f"Auth: {auth_mode}")
    return client, auth_mode, tenant_id
