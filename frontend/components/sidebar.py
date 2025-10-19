# frontend/components/sidebar.py
import streamlit as st
from backend.db.db_handler import (
    get_session,
    get_documents_by_user,
    create_chat_session,
    get_chat_sessions_by_user,
    update_chat_session_name,
    delete_chat_session_by_id
)
from datetime import datetime

def render_user_sidebar(current_user_id):
    """
    Renders the user sidebar with improved chat history UI
    showing icons only for the active chat.
    """

    active_view = st.session_state.get("current_view", "Dashboard")

    # --- 1. Button-Based Navigation ---
    st.sidebar.subheader("Navigation")
    nav_options = ["Dashboard", "Document Upload", "Document Management", "Saved Summaries", "Extracted Text", "Chat", "Chat History"]
    icons = ["🏠", "⬆️", "📚", "📌", "📄", "💬", "📜"]

    for i, option in enumerate(nav_options):
        if st.sidebar.button(
            f"{icons[i]} {option}",
            type="primary" if active_view == option else "secondary",
            use_container_width=True
        ):
            st.session_state.current_view = option
            st.rerun()

    st.sidebar.divider()

    # --- 2. Interactive Elements ---
    uploaded_files = None
    if st.session_state.current_view == "Document Upload":
        st.sidebar.subheader("Upload Files")
        uploaded_files = st.file_uploader(
            "Upload PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            key="file_uploader",
            label_visibility="collapsed"
        )
        st.sidebar.divider()

    # Show Doc Selector only on Extract, Chat, and Saved Summaries pages
    # Doc selector is NOT shown on Dashboard, Upload, Doc Management, Chat History
    if st.session_state.current_view in ["Extracted Text", "Chat", "Saved Summaries"]:
        st.sidebar.subheader("📂 Select Document")
        with get_session() as db:
            user_docs = get_documents_by_user(db, current_user_id)
        if user_docs:
            doc_options_list = [doc.filename for doc in user_docs] + ["🔎 All My Documents"]
            current_active_doc = st.session_state.get("active_doc")
            # Set default if current selection is invalid
            if current_active_doc not in doc_options_list:
                st.session_state.active_doc = doc_options_list[0]
            st.selectbox(
                "Select Document",
                options=doc_options_list,
                key="active_doc",
                index=doc_options_list.index(st.session_state.active_doc),
                label_visibility="collapsed"
            )
        else:
            st.session_state.active_doc = None
            st.info("No documents uploaded yet.")
        st.sidebar.divider()

    # --- 3. Chat History Panel ---
    # Show chat list ONLY if NOT on the main Chat History page
    if st.session_state.current_view != "Chat History":
        st.sidebar.subheader("💬 Chats")

        if st.sidebar.button("➕ New Chat", use_container_width=True):
            with get_session() as db:
                first_message = f"Chat {datetime.now().strftime('%H:%M')}"
                new_session = create_chat_session(db, current_user_id, name=first_message)
                st.session_state.active_session = new_session.id
                st.session_state.current_view = "Chat" # Switch to chat view
                st.rerun()

        with get_session() as db:
            chat_sessions = get_chat_sessions_by_user(db, current_user_id)

        if not chat_sessions:
            st.info("No chat history yet.")
            st.session_state.active_session = None
        else:
            session_ids = [s.id for s in chat_sessions]
            # Ensure active_session is valid, default if needed
            if st.session_state.get("active_session") not in session_ids:
                 st.session_state.active_session = session_ids[0] if session_ids else None

            st.sidebar.caption("Your recent chats:")

            # Use a container for potential scrolling
            with st.container(height=300): # Adjust height if needed
                for session in chat_sessions:
                    is_active = (session.id == st.session_state.active_session)
                    display_text = f"{session.name}" # Show only name

                    col1, col2, col3 = st.columns([5, 1, 1]) # Main button | Rename | Delete

                    with col1:
                        # Main button selects the chat
                        if st.button(
                            display_text,
                            key=f"select_{session.id}",
                            use_container_width=True,
                            type="primary" if is_active else "secondary"
                        ):
                            st.session_state.active_session = session.id
                            st.session_state.current_view = "Chat"
                            st.rerun()

                    # Show icons ONLY for the active chat
                    if is_active:
                        with col2:
                            rename_popover = st.popover("✏️", help="Rename Chat", use_container_width=True)
                            with rename_popover:
                                new_name = st.text_input("New chat name:", value=session.name, key=f"rename_input_{session.id}")
                                if st.button("Save Name", key=f"save_rename_{session.id}"):
                                    if new_name and new_name.strip() and new_name != session.name:
                                        with get_session() as db_action:
                                            update_chat_session_name(db_action, session.id, new_name.strip())
                                        st.rerun() # Refresh sidebar
                                    elif not new_name or not new_name.strip():
                                        st.warning("Name cannot be empty.")
                                    else:
                                        st.toast("Name unchanged.", icon="ℹ️")

                        with col3:
                            delete_popover = st.popover("🗑️", help="Delete Chat", use_container_width=True)
                            with delete_popover:
                                st.error(f"Delete chat '{session.name}'?")
                                if st.button(f"Confirm Delete Chat {session.id}", type="primary"):
                                    with get_session() as db_action:
                                        delete_chat_session_by_id(db_action, session.id)
                                    # Reset active session and refresh
                                    st.session_state.active_session = None
                                    st.rerun()
                    else:
                        # Keep columns aligned for non-active items
                        col2.write("")
                        col3.write("")

    return uploaded_files