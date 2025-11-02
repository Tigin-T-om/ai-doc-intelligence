# frontend/app.py
import sys
import os
import streamlit as st

# ----------------------------
# PATH SETUP
# ----------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- DB & View Imports ---
from backend.db.db_handler import get_session, get_document_by_name_for_user, create_tables
from frontend.views.auth_view import render_auth_view
from frontend.views.upload_view import render_upload_view
from frontend.views.extract_view import render_extract_view
from frontend.views.chat_view import chat_view
from frontend.views.saved_summaries_view import render_saved_summaries_view
from frontend.views.user_dashboard_view import render_user_dashboard_view # <-- ADD THIS
from frontend.views.document_management_view import render_document_management_view
from frontend.views.chat_history_view import render_chat_history_view
from frontend.views.insights_view import render_insights_view
from frontend.components.utils import init_session

# --- NEW: Import Sidebar Components ---
from frontend.views.admin.admin_sidebar import render_admin_sidebar
from frontend.components.sidebar import render_user_sidebar

# --- NEW: Import Admin Views ---
from frontend.views.admin.dashboard_view import render_dashboard_view
from frontend.views.admin.user_management_view import render_user_management_view
from frontend.views.admin.api_management_view import render_api_management_view
# -----------------------------

# ----------------------------
# INIT DB
# ----------------------------
create_tables()

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
current_user_role = st.session_state.auth.get("role")

uploaded_files = None

# --- NEW: Refactored Sidebar ---
with st.sidebar:
    st.title(f"Welcome, {current_username}")
    if st.button("Logout"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    st.markdown("---")

    if current_user_role == "admin":
        # --- ★★★ THIS IS THE FIX ★★★ ---
        # On first login, 'is_admin_view' won't exist.
        # This block sets the admin view to 'True' by default for admins.
        if "is_admin_view" not in st.session_state:
            st.session_state.is_admin_view = True
        # --- ★★★ END OF FIX ★★★ ---
        render_admin_sidebar()
    else:
        uploaded_files = render_user_sidebar(current_user_id)

    st.markdown("---")
    st.markdown("Developed by Tigin Tom")
# --- End of Sidebar ---

# ----------------------------
# RENDER MAIN CONTENT
# ----------------------------
if st.session_state.get("is_admin_view", False):
    # Render Admin Views
    if st.session_state.admin_view == "Dashboard":
        render_dashboard_view()
    elif st.session_state.admin_view == "User Management":
        render_user_management_view()
    elif st.session_state.admin_view == "API Management":
        render_api_management_view()
else:
    # Render Regular User Views
    active_doc_obj = None
    if st.session_state.get('active_doc') and st.session_state.active_doc != "🔎 All My Documents":
        with get_session() as db:
            active_doc_obj = get_document_by_name_for_user(db, current_user_id, st.session_state.active_doc)

    view = st.session_state.get("current_view", "Dashboard")
    
    if view == "Dashboard":
        render_user_dashboard_view(current_user_id, current_username)
    elif view == "Document Upload":
        render_upload_view(current_user_id, uploaded_files)
    elif view == "Document Management":
         render_document_management_view(current_user_id)
    elif view == "Saved Summaries":
         render_saved_summaries_view(current_user_id)
    # --- NEW ROUTE ADDED ---
    elif view == "Insights":
         render_insights_view(current_user_id)
    # --- END NEW ROUTE ---
    elif view == "Extracted Text":
        render_extract_view(active_doc_obj, current_user_id)
    elif view == "Chat":
        chat_view(active_doc_obj, current_user_id)
    elif view == "Chat History":
         render_chat_history_view(current_user_id)