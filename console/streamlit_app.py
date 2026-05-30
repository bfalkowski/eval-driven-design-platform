import streamlit as st

from components.layout import load_css
from navigation import build_navigation

st.set_page_config(
    page_title="Eval Driven Design",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()
build_navigation().run()
