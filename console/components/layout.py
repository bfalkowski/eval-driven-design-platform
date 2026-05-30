from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

_PILL_STATUSES = frozenset({"green", "yellow", "red", "blue"})


def load_css() -> None:
    css_path = Path(__file__).resolve().parents[1] / "styles" / "dashboard.css"
    css = css_path.read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def page_shell(title: str, subtitle: str | None = None) -> None:
    subtitle_html = (
        f'<div class="edd-hero-subtitle">{html.escape(subtitle)}</div>' if subtitle else ""
    )
    st.markdown(
        f"""
        <div class="edd-hero">
          <div class="edd-hero-title">{html.escape(title)}</div>
          {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, meta: str | None = None) -> None:
    meta_html = f'<div class="edd-page-meta">{html.escape(meta)}</div>' if meta else ""
    st.markdown(
        f"""
        <div class="edd-page-header">
          <div class="edd-page-title">{html.escape(title)}</div>
          {meta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def sidebar_brand() -> None:
    st.sidebar.markdown(
        """
        <div class="edd-sidebar-brand">
          <div class="edd-sidebar-title">Eval Driven Design</div>
          <div class="edd-sidebar-caption">Control plane for eval-driven AI development</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def edd_lifecycle_strip() -> None:
    st.markdown(
        """
        <div class="edd-loop">
          <div class="edd-loop-step">
            <div class="edd-loop-number">1</div>
            <div class="edd-loop-title">Design</div>
            <div class="edd-loop-text">Target, rules, eval contract, and tool requirements.</div>
          </div>
          <div class="edd-loop-step">
            <div class="edd-loop-number">2</div>
            <div class="edd-loop-title">Build</div>
            <div class="edd-loop-text">Graph versions, tool bindings, and mock or live integrations.</div>
          </div>
          <div class="edd-loop-step">
            <div class="edd-loop-number">3</div>
            <div class="edd-loop-title">Evaluate</div>
            <div class="edd-loop-text">Run scenarios, capture failure packets, and compare versions.</div>
          </div>
          <div class="edd-loop-step">
            <div class="edd-loop-number">4</div>
            <div class="edd-loop-title">Promote</div>
            <div class="edd-loop-text">Gate on behavior, tool readiness, and production blockers.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def workflow_loop() -> None:
    st.markdown(
        """
        <div class="edd-loop">
          <div class="edd-loop-step">
            <div class="edd-loop-number">1</div>
            <div class="edd-loop-title">Observe</div>
            <div class="edd-loop-text">Inspect traces and identify behavior worth testing.</div>
          </div>
          <div class="edd-loop-step">
            <div class="edd-loop-number">2</div>
            <div class="edd-loop-title">Create Case</div>
            <div class="edd-loop-text">Turn failures or examples into reusable eval cases.</div>
          </div>
          <div class="edd-loop-step">
            <div class="edd-loop-number">3</div>
            <div class="edd-loop-title">Run Candidate</div>
            <div class="edd-loop-text">Evaluate prompt, model, or workflow versions.</div>
          </div>
          <div class="edd-loop-step">
            <div class="edd-loop-number">4</div>
            <div class="edd-loop-title">Score</div>
            <div class="edd-loop-text">Apply deterministic checks and evaluator scoring.</div>
          </div>
          <div class="edd-loop-step">
            <div class="edd-loop-number">5</div>
            <div class="edd-loop-title">Decide</div>
            <div class="edd-loop-text">Pass, fail, promote, or create regression cases.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, help_text: str | None = None) -> None:
    help_html = (
        f'<div class="edd-metric-help">{html.escape(help_text)}</div>' if help_text else ""
    )
    st.markdown(
        f"""
        <div class="edd-metric">
          <div class="edd-metric-label">{html.escape(label)}</div>
          <div class="edd-metric-value">{html.escape(value)}</div>
          {help_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_pill(label: str, status: str = "blue") -> str:
    safe_status = status if status in _PILL_STATUSES else "blue"
    return (
        f'<span class="edd-pill edd-pill-{safe_status}">{html.escape(label)}</span>'
    )


def run_card(title: str, subtitle: str, status_label: str, status: str = "blue") -> None:
    st.markdown(
        f"""
        <div class="edd-card">
          <div class="edd-card-title">{html.escape(title)} {status_pill(status_label, status)}</div>
          <div class="edd-card-subtitle">{html.escape(subtitle)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def integration_card(title: str, subtitle: str, status_label: str, status: str = "blue") -> None:
    run_card(title, subtitle, status_label, status)
