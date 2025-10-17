# frontend/views/admin/admin_sidebar.py
import streamlit as st
from backend.db.db_handler import get_session, count_total_users

def render_admin_sidebar():
    """
    Renders a button-based navigation sidebar for the admin user.
    """
    st.sidebar.title("👑 Admin Panel")

    # Get user count for the button
    try:
        with get_session() as db:
            user_count = count_total_users(db)
    except Exception:
        user_count = "N/A"

    # Get the current active view
    active_view = st.session_state.get("admin_view", "Dashboard")

    # --- Button Navigation ---
    
    # Dashboard Button
    if st.sidebar.button(
        "📊 Dashboard",
        type="primary" if active_view == "Dashboard" else "secondary",
        use_container_width=True
    ):
        st.session_state.admin_view = "Dashboard"
        st.session_state.is_admin_view = True
        st.rerun() # Rerun to ensure the button type updates

    # User Management Button
    if st.sidebar.button(
        f"👥 User Management ({user_count})",
        type="primary" if active_view == "User Management" else "secondary",
        use_container_width=True
    ):
        st.session_state.admin_view = "User Management"
        st.session_state.is_admin_view = True
        st.rerun()
