from __future__ import annotations

import streamlit as st

from components.layout import page_header, page_shell


def render_page_header(title: str, *, client_base_url: str, auth_mode: str) -> None:
    page_header(title, f"{client_base_url} · {auth_mode}")


def render_overview_header(*, client_base_url: str, auth_mode: str) -> None:
    page_shell(
        "Eval Driven Design Platform",
        (
            "Define success criteria, turn traces into eval cases, run candidate workflows, "
            f"and enforce quality gates before shipping AI changes. {client_base_url} · {auth_mode}"
        ),
    )


def show_api_error(exc: Exception) -> None:
    st.error(str(exc))
