"""Streamlit lifecycle navigation (HLD-011 MVP subset)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

_CONSOLE_ROOT = Path(__file__).resolve().parent

LIFECYCLE_SECTIONS: tuple[str, ...] = ("Overview", "Design", "Build", "Evaluate", "Promote")


@dataclass(frozen=True)
class PageSpec:
    relative_path: str
    title: str
    icon: str
    default: bool = False


LIFECYCLE_PAGE_SPECS: dict[str, list[PageSpec]] = {
    "Overview": [
        PageSpec("pages/1_Overview.py", "Overview", "🏠", default=True),
    ],
    "Design": [
        PageSpec("pages/9_Agent_Target.py", "Target", "🎯"),
        PageSpec("pages/10_Behavior_Rules.py", "Rules", "📏"),
        PageSpec("pages/11_Eval_Contract.py", "Eval Contract", "📋"),
        PageSpec("pages/13_Information_Requirements.py", "Information", "ℹ️"),
        PageSpec("pages/14_Tool_Requirements.py", "Tool Requirements", "🔧"),
        PageSpec("pages/15_Tool_Feasibility.py", "Tool Feasibility", "🧪"),
    ],
    "Build": [
        PageSpec("pages/12_Graph_Design.py", "Graph Design", "🕸️"),
    ],
    "Evaluate": [
        PageSpec("pages/2_Eval_Specs.py", "Eval Specs", "📝"),
        PageSpec("pages/3_Eval_Cases.py", "Eval Cases", "🗂️"),
        PageSpec("pages/4_Runs.py", "Runs", "▶️"),
        PageSpec("pages/5_Results_Explorer.py", "Results", "📊"),
        PageSpec("pages/6_Quality_Gates.py", "Gates", "🚦"),
        PageSpec("pages/7_Langfuse.py", "Traces", "🔍"),
        PageSpec("pages/16_Failure_Packets.py", "Failure Packets", "⚠️"),
        PageSpec("pages/17_Fix_Plans.py", "Fix Plans", "🛠️"),
    ],
    "Promote": [
        PageSpec("pages/18_Compare_Versions.py", "Compare Versions", "📈"),
        PageSpec("pages/8_Operations.py", "Operations", "🏭"),
    ],
}


def page_path(relative: str) -> Path:
    return _CONSOLE_ROOT / relative


def _to_streamlit_page(spec: PageSpec) -> st.Page:
    return st.Page(
        str(page_path(spec.relative_path)),
        title=spec.title,
        icon=spec.icon,
        default=spec.default,
    )


def lifecycle_pages() -> dict[str, list[st.Page]]:
    return {
        section: [_to_streamlit_page(spec) for spec in specs]
        for section, specs in LIFECYCLE_PAGE_SPECS.items()
    }


def build_navigation() -> st.navigation:
    return st.navigation(lifecycle_pages())
