from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from components.api_client import ServiceClient, get_api_base_url
from components.layout import load_css, sidebar_brand

_DEFAULT_TOKEN_FILE = Path(os.environ.get("TMPDIR", "/tmp")) / "edd-api.token"


def _load_token_from_env_or_file() -> str:
    token = os.environ.get("EDD_BEARER_TOKEN", "").strip()
    if token:
        return token
    token_file = Path(os.environ.get("EDD_TOKEN_FILE", str(_DEFAULT_TOKEN_FILE)))
    if token_file.is_file():
        return token_file.read_text(encoding="utf-8").strip()
    return ""


def init_platform_session_state() -> None:
    if "api_base_url" not in st.session_state:
        st.session_state.api_base_url = get_api_base_url()
    if "bearer_token" not in st.session_state:
        st.session_state.bearer_token = _load_token_from_env_or_file()
    if "tenant_id" not in st.session_state:
        st.session_state.tenant_id = "tenant-a"
    if "bearer_token_draft" not in st.session_state:
        st.session_state.bearer_token_draft = ""
    if "api_base_url_draft" not in st.session_state:
        st.session_state.api_base_url_draft = st.session_state.api_base_url


def _apply_credentials() -> None:
    st.session_state.bearer_token = str(st.session_state.bearer_token_draft).strip()
    st.session_state.api_base_url = str(st.session_state.api_base_url_draft).strip() or get_api_base_url()


def render_platform_sidebar() -> tuple[ServiceClient, str, str | None]:
    init_platform_session_state()
    load_css()
    sidebar_brand()
    st.sidebar.markdown("---")

    st.sidebar.text_input("API base URL", key="api_base_url_draft")
    st.sidebar.text_input(
        "Bearer token",
        key="bearer_token_draft",
        type="password",
        placeholder="Paste token, then click Apply credentials",
    )

    apply_col, reload_col = st.sidebar.columns(2)
    if apply_col.button("Apply credentials", type="primary", use_container_width=True):
        _apply_credentials()
        st.rerun()
    if reload_col.button("Reload token file", use_container_width=True):
        st.session_state.bearer_token = _load_token_from_env_or_file()
        st.rerun()

    bearer_token = str(st.session_state.bearer_token).strip()
    tenant_id: str | None = None
    if bearer_token:
        st.sidebar.success("API authenticated for this session.")
    else:
        st.sidebar.warning("No bearer token — API calls will fail while auth is enabled.")
        st.sidebar.text_input("Tenant (auth disabled only)", key="tenant_id")
        tenant_id = str(st.session_state.tenant_id).strip() or None

    api_base_url = str(st.session_state.api_base_url).strip() or get_api_base_url()
    client = ServiceClient(
        api_base_url,
        bearer_token=bearer_token or None,
    )
    auth_mode = "bearer token" if bearer_token else "not authenticated"
    st.sidebar.caption(f"Auth: {auth_mode}")
    return client, auth_mode, tenant_id
