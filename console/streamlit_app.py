import streamlit as st

from components.layout import load_css

st.set_page_config(
    page_title="Eval Driven Design",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()
st.switch_page("pages/1_Overview.py")
