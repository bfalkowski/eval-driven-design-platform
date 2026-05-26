import streamlit as st

st.set_page_config(
    page_title="Eval Driven Design",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Eval Driven Design Platform")
st.caption(
    "Control plane for eval-driven AI development. "
    "Use the sidebar to move through specs, cases, runs, and results."
)
