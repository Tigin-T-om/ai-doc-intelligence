# frontend/app.py
import os, sys
import streamlit as st

# ----------------------------
# PATH SETUP
# ----------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.db.db_handler import get_session, get_documents_by_user, get_document_by_name_for_user, create_tables
from frontend.views.auth_view import render_auth_view
from frontend.views.upload_view import render_upload_view
from frontend.views.extract_view import render_extract_view
from frontend.views.chat_view import chat_view
from frontend.components.utils import init_session
from frontend.components.sidebar import sidebar_ui   # ✅ import new sidebar

# ----------------------------
# INIT DB
# ----------------------------
# ⚠️ Removed drop_tables() so data is not lost every rerun
create_tables()  # only creates tables if they don’t exist

# ----------------------------
# STREAMLIT PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="🖊️ PDF Intelligence Chatbot", page_icon="🧠", layout="wide")
init_session()

# ----------------------------
# AUTHENTICATION FLOW
# ----------------------------
if not st.session_state.auth["logged_in"]:
    render_auth_view()
    st.stop()

# ----------------------------
# MAIN APP
# ----------------------------
current_username = st.session_state.auth["username"]
current_user_id = st.session_state.auth["user_id"]

# --- SIDEBAR ---
with st.sidebar:
    st.title(f"Welcome, {current_username}")
    if st.button("Logout"):
        st.session_state.auth = {"logged_in": False, "username": None, "user_id": None}
        st.rerun()

    st.markdown("---")

    def set_view():
        st.session_state.current_view = st.session_state.navigation_radio

    st.radio(
        "Select Section",
        ("Document Upload", "Extracted Text", "Chat"),
        index=("Document Upload", "Extracted Text", "Chat").index(st.session_state.current_view),
        key="navigation_radio",
        on_change=set_view
    )

    # File uploader
    if st.session_state.current_view == "Document Upload":
        uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)
    else:
        uploaded_files = None

    # Document selector
    with get_session() as db:
        user_docs = get_documents_by_user(db, current_user_id)
    if user_docs:
        doc_options_list = [doc.filename for doc in user_docs] + ["🔎 All My Documents"]
        if st.session_state.active_doc not in doc_options_list:
            st.session_state.active_doc = doc_options_list[0]
        selected_doc_name = st.selectbox(
            "📂 Select Document",
            options=doc_options_list,
            index=doc_options_list.index(st.session_state.active_doc)
        )
        st.session_state.active_doc = selected_doc_name
    else:
        st.session_state.active_doc = None

    st.markdown("---")
    st.markdown("Developed by Tigin Tom")

# ✅ Add Chat Sessions Sidebar (below your existing sidebar content)
sidebar_ui(current_user_id)

# ----------------------------
# RENDER VIEWS
# ----------------------------
active_doc_obj = None
if st.session_state.active_doc and st.session_state.active_doc != "🔎 All My Documents":
    with get_session() as db:
        active_doc_obj = get_document_by_name_for_user(db, current_user_id, st.session_state.active_doc)

if st.session_state.current_view == "Document Upload":
    render_upload_view(current_user_id, uploaded_files)
elif st.session_state.current_view == "Extracted Text":
    render_extract_view(active_doc_obj)
elif st.session_state.current_view == "Chat":
    chat_view(active_doc_obj, current_user_id)
