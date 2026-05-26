from __future__ import annotations

import streamlit as st

from components.api_client import ServiceClient, get_api_base_url


def render_platform_sidebar() -> tuple[ServiceClient, str, str | None]:
    api_base_url = st.sidebar.text_input("API base URL", value=get_api_base_url())
    bearer_token = st.sidebar.text_input("Bearer token", value="", type="password")
    tenant_id: str | None = None
    if not bearer_token.strip():
        tenant_id = st.sidebar.text_input("Tenant", value="tenant-a").strip() or None
    if st.sidebar.button("Refresh", type="primary"):
        st.rerun()

    client = ServiceClient(
        api_base_url.strip(),
        bearer_token=bearer_token.strip() or None,
    )
    auth_mode = "bearer token" if bearer_token.strip() else "tenant fallback"
    st.sidebar.caption(f"Auth: {auth_mode}")
    return client, auth_mode, tenant_id
