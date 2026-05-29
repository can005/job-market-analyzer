import streamlit as st

from agents.graph import build_graph, run
from core.schemas import InvalidSeamInputError, NoResultsError
from ui.profile_form import render_profile_form
from ui.results import render_results

st.set_page_config(page_title="Job Market Analyzer", layout="wide")


@st.cache_resource
def _graph():
    return build_graph()


st.title("Job Market Analyzer")

profile = render_profile_form()

st.subheader("Ask about the job market")
question = st.text_input(
    "Question",
    key="question",
    label_visibility="collapsed",
    placeholder="e.g. Which roles fit me, and how's the C++ market trending?",
)

running = st.session_state.get("running", False)
form_ready = profile is not None and bool(question.strip())

if st.button("Run analysis", disabled=not form_ready or running):
    st.session_state.running = True
    try:
        with st.spinner("Searching postings and scoring candidates — usually takes 30–60s"):
            try:
                result = run(_graph(), question, profile, trace=True, surface="ui")
                st.session_state.result = result
                st.session_state.last_run_failed = False
            except (InvalidSeamInputError, NoResultsError) as e:
                st.error(str(e))
                st.session_state.last_run_failed = True
    finally:
        st.session_state.running = False
        st.rerun()

if "result" in st.session_state:
    render_results(
        st.session_state.result,
        stale=st.session_state.get("last_run_failed", False),
    )
