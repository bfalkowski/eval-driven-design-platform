from __future__ import annotations

import streamlit as st


def render_page_header(title: str, *, client_base_url: str, auth_mode: str) -> None:
    st.header(title)
    st.caption(f"{client_base_url} · {auth_mode}")


def show_api_error(exc: Exception) -> None:
    st.error(str(exc))
