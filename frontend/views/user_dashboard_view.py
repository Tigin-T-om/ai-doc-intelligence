# frontend/views/user_dashboard_view.py
import streamlit as st
from backend.db.db_handler import (
    get_session,
    count_documents_by_user,
    get_recent_documents_by_user,
    count_chat_sessions_by_user,
    get_recent_chat_sessions_by_user
)

def render_user_dashboard_view(user_id, username):
    st.title(f"Welcome back, {username}! 👋")
    st.markdown("Here's a quick overview of your account.")
    st.markdown("---")

    # --- 1. Key Metrics ---
    with get_session() as db:
        doc_count = count_documents_by_user(db, user_id)
        chat_count = count_chat_sessions_by_user(db, user_id)
    
    active_doc = st.session_state.get('active_doc', 'None')
    if active_doc == "🔎 All My Documents":
        active_doc = "All Documents"

    col1, col2, col3 = st.columns(3)
    col1.metric("📂 Total Documents", value=doc_count)
    col2.metric("💬 Total Chats", value=chat_count)
    col3.metric("📄 Active Document", value=active_doc)

    st.markdown("---")

    # --- 2. Quick Actions & Recent Activity ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚀 Quick Actions")
        if st.button("➕ Upload a New Document", use_container_width=True, type="primary"):
            st.session_state.current_view = "Document Upload"
            st.rerun()
        
        st.subheader("📄 Recent Documents")
        with get_session() as db:
            recent_docs = get_recent_documents_by_user(db, user_id, limit=5)
        
        if not recent_docs:
            st.info("You haven't uploaded any documents yet.")
        
        for doc in recent_docs:
            with st.container(border=True):
                st.markdown(f"**{doc.filename}**")
                st.caption(f"Uploaded: {doc.created_at.strftime('%Y-%m-%d %H:%M')}")
                if st.button("Go to Document", key=f"doc_{doc.id}", use_container_width=True):
                    st.session_state.active_doc = doc.filename
                    st.session_state.current_view = "Extracted Text"
                    st.rerun()

    with col2:
        st.subheader("💬 Recent Chats")
        with get_session() as db:
            recent_chats = get_recent_chat_sessions_by_user(db, user_id, limit=5)
            
        if not recent_chats:
            st.info("You haven't started any chats yet.")

        for chat in recent_chats:
            with st.container(border=True):
                st.markdown(f"**{chat.name}** (ID: {chat.id})")
                st.caption(f"Created: {chat.created_at.strftime('%Y-%m-%d %H:%M')}")
                if st.button("Go to Chat", key=f"chat_{chat.id}", use_container_width=True):
                    st.session_state.active_session = chat.id
                    st.session_state.current_view = "Chat"
                    st.rerun()