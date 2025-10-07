import streamlit as st
from backend.db.db_handler import get_session, get_chat_sessions_by_user, create_chat_session

def sidebar_ui(current_user_id):
    with st.sidebar:
        st.title("📂 Documents")
        # existing doc upload/selection here

        st.markdown("---")
        st.title("💬 Chats")

        with get_session() as db:
            chat_sessions = get_chat_sessions_by_user(db, current_user_id)

        if st.button("➕ New Chat"):
            with get_session() as db:
                new_session = create_chat_session(db, current_user_id, name="New Chat")
                st.session_state.active_session = new_session.id
                st.rerun()

        session_labels = [f"{s.name} ({s.created_at.strftime('%H:%M')})" for s in chat_sessions]
        session_ids = [s.id for s in chat_sessions]

        if session_ids:
            selected = st.selectbox("Select a Chat Session", session_ids, format_func=lambda x: session_labels[session_ids.index(x)])
            st.session_state.active_session = selected
        else:
            st.info("No chat history yet. Start a new one!")
            st.session_state.active_session = None

        st.markdown("---")
        st.title("⚙️ Settings")
        st.toggle("🌙 Dark Mode")
