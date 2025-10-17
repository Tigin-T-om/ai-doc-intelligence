# frontend/components/utils.py
import time
import streamlit as st

# ----------------------------
# SESSION STATE INIT
# ----------------------------
def init_session():
    if "auth" not in st.session_state:
        st.session_state.auth = {"logged_in": False, "username": None, "user_id": None, "role": None}
    if "summary_cache" not in st.session_state:
        st.session_state.summary_cache = {}
    if "active_doc" not in st.session_state:
        st.session_state.active_doc = None
    if "current_view" not in st.session_state:
        st.session_state.current_view = "Document Upload"
    if "admin_view" not in st.session_state: # <- ADD THIS LINE
        st.session_state.admin_view = "Dashboard" # <- ADD THIS LINE

# ----------------------------
# TYPING EFFECT
# ----------------------------
def simulate_typing(text, delay=0.01):
    placeholder = st.empty()
    typed = ""
    for char in text:
        typed += char
        placeholder.markdown(typed)
        time.sleep(delay)
