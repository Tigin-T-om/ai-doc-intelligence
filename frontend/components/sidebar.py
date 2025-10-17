# frontend/components/sidebar.py
import streamlit as st
from backend.db.db_handler import get_session, get_documents_by_user, create_chat_session
from backend.db.db_handler import get_chat_sessions_by_user

def render_user_sidebar(current_user_id):
    """
    Renders the complete navigation and interaction sidebar for a regular user.
    Returns:
        uploaded_files: The result of the st.file_uploader, or None.
    """
    # --- This code was moved from app.py ---
    st.radio(
        "Select Section",
        ("Document Upload", "Extracted Text", "Chat"),
        key="current_view"
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
        st.selectbox("📂 Select Document", options=doc_options_list, key="active_doc")
    else:
        st.session_state.active_doc = None

    st.markdown("---")

    # --- This is your original chat history code ---
    st.title("💬 Chats")

    with get_session() as db:
        chat_sessions = get_chat_sessions_by_user(db, current_user_id)

    if st.button("➕ New Chat"):
        with get_session() as db:
            new_session = create_chat_session(db, current_user_id, name="New Chat")
            st.session_state.active_session = new_session.id
            st.rerun()

    session_labels = [f"Chat {s.id} ({s.created_at.strftime('%H:%M')})" for s in chat_sessions]
    session_ids = [s.id for s in chat_sessions]

    if session_ids:
        # Create a mapping from ID to label for the format_func
        session_dict = dict(zip(session_ids, session_labels))
        selected = st.selectbox(
            "Select a Chat Session", 
            session_ids, 
            format_func=lambda x: session_dict.get(x)
        )
        st.session_state.active_session = selected
    else:
        st.info("No chat history yet.")
        st.session_state.active_session = None
        
    return uploaded_files