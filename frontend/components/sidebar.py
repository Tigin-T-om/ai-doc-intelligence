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
    # (Keep Dashboard, Upload, Extract, Chat buttons as before)
    if st.sidebar.button("🏠 Dashboard", type="primary" if active_view == "Dashboard" else "secondary", use_container_width=True):
        st.session_state.current_view = "Dashboard"; st.rerun()
    if st.sidebar.button("⬆️ Document Upload", type="primary" if active_view == "Document Upload" else "secondary", use_container_width=True):
        st.session_state.current_view = "Document Upload"; st.rerun()
    if st.sidebar.button("📄 Extracted Text", type="primary" if active_view == "Extracted Text" else "secondary", use_container_width=True):
        st.session_state.current_view = "Extracted Text"; st.rerun()
    if st.sidebar.button("💬 Chat", type="primary" if active_view == "Chat" else "secondary", use_container_width=True):
        st.session_state.current_view = "Chat"; st.rerun()
    st.sidebar.divider()

    # --- 2. Interactive Elements ---
    uploaded_files = None
    if st.session_state.current_view == "Document Upload":
        st.sidebar.subheader("Upload Files")
        uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True, key="file_uploader", label_visibility="collapsed")
        st.sidebar.divider()

    if st.session_state.current_view in ["Extracted Text", "Chat"]:
        st.sidebar.subheader("📂 Select Document")
        with get_session() as db:
            user_docs = get_documents_by_user(db, current_user_id)
        if user_docs:
            doc_options_list = [doc.filename for doc in user_docs] + ["🔎 All My Documents"]
            current_active_doc = st.session_state.get("active_doc")
            if current_active_doc not in doc_options_list: st.session_state.active_doc = doc_options_list[0]
            st.selectbox("Select Document", options=doc_options_list, key="active_doc", index=doc_options_list.index(st.session_state.active_doc), label_visibility="collapsed")
        else:
            st.session_state.active_doc = None; st.info("No documents uploaded yet.")
        st.sidebar.divider()

    # --- 3. Chat History Panel (Icons for Active Chat) ---
    st.sidebar.subheader("💬 Chats")

    if st.sidebar.button("➕ New Chat", use_container_width=True):
        with get_session() as db:
            first_message = f"Chat {datetime.now().strftime('%H:%M')}"
            new_session = create_chat_session(db, current_user_id, name=first_message)
            st.session_state.active_session = new_session.id
            st.session_state.current_view = "Chat"
            st.rerun()

    with get_session() as db:
        chat_sessions = get_chat_sessions_by_user(db, current_user_id)

    if not chat_sessions:
        st.info("No chat history yet.")
        st.session_state.active_session = None
    else:
        session_ids = [s.id for s in chat_sessions]
        if st.session_state.get("active_session") not in session_ids:
             st.session_state.active_session = session_ids[0] if session_ids else None

        st.sidebar.caption("Your recent chats:")

        # Use a container for potential scrolling
        with st.container(height=300):
            for session in chat_sessions:
                is_active = (session.id == st.session_state.active_session)
                display_text = f"{session.name}" # Keep it clean

                # --- ★★★ CHANGE IS HERE ★★★ ---
                # Use columns: Main button | Rename Icon (if active) | Delete Icon (if active)
                col1, col2, col3 = st.columns([5, 1, 1])

                with col1:
                    # Main button to select the chat
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
                        # Rename popover triggered by icon
                        rename_popover = st.popover("✏️", help="Rename Chat", use_container_width=True)
                        with rename_popover:
                            new_name = st.text_input("New chat name:", value=session.name, key=f"rename_input_{session.id}")
                            if st.button("Save Name", key=f"save_rename_{session.id}"):
                                if new_name and new_name.strip() and new_name != session.name:
                                    with get_session() as db_action:
                                        update_chat_session_name(db_action, session.id, new_name.strip())
                                    st.rerun()
                                elif not new_name or not new_name.strip(): st.warning("Name cannot be empty.")
                                else: st.toast("Name unchanged.", icon="ℹ️")

                    with col3:
                        # Delete popover triggered by icon
                        delete_popover = st.popover("🗑️", help="Delete Chat", use_container_width=True)
                        with delete_popover:
                            st.error(f"Delete chat '{session.name}'?")
                            if st.button(f"Confirm Delete Chat {session.id}", type="primary"):
                                with get_session() as db_action:
                                    delete_chat_session_by_id(db_action, session.id)
                                st.session_state.active_session = None
                                st.rerun()
                else:
                    # Keep columns aligned for non-active items
                    col2.write("")
                    col3.write("")
                # --- ★★★ END OF CHANGE ★★★ ---

    return uploaded_files