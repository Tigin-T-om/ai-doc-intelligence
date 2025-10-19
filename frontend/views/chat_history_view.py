# frontend/views/chat_history_view.py
import streamlit as st
from backend.db.db_handler import get_session, get_chat_session

def render_chat_history_view(user_id):
    st.title("📜 Detailed Chat History")
    st.markdown("Review and manage your past chat sessions.")
    st.markdown("---")

    active_session_id = st.session_state.get("active_session")

    if not active_session_id:
        st.info("👈 Select a chat session from the sidebar to view its history.")
        return

    try:
        # --- Move message processing inside the session block ---
        with get_session() as db:
            session = get_chat_session(db, active_session_id)

            if not session:
                st.error("Selected chat session not found.")
                return

            st.subheader(f"Transcript for: {session.name}")
            st.caption(f"Created on: {session.created_at.strftime('%Y-%m-%d %H:%M')}")

            # --- Search Feature ---
            search_term = st.text_input("Search within this chat:", placeholder="Enter keyword...")
            search_term_lower = search_term.lower() if search_term else None

            # --- Access and Filter Messages INSIDE the 'with' block ---
            all_messages = session.messages # Load messages while session is active
            messages_to_display = all_messages
            if search_term_lower:
                messages_to_display = [
                    msg for msg in all_messages if search_term_lower in msg.content.lower()
                ]
                st.write(f"Found {len(messages_to_display)} messages matching '{search_term}':")
                if not messages_to_display:
                     st.warning("No messages found matching your search term.")

            # Prepare export data INSIDE the 'with' block as well
            export_data = ""
            if messages_to_display:
                export_data = f"Chat Session: {session.name}\n"
                export_data += f"Created: {session.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                export_data += "--------------------\n\n"
                for msg in messages_to_display:
                     export_data += f"[{msg.created_at.strftime('%H:%M:%S')}] {msg.role.upper()}:\n{msg.content}\n\n"

        # --- Display Messages (Outside the 'with' block is fine now) ---
        chat_container = st.container(height=500, border=False)
        with chat_container:
            for msg in messages_to_display:
                with st.chat_message(msg.role):
                    st.markdown(msg.content)

        st.markdown("---")

        # --- Export Feature ---
        st.subheader("Export Chat")
        if export_data: # Check if export_data was prepared
            safe_filename = "".join(c if c.isalnum() else "_" for c in session.name)
            export_filename = f"chat_history_{safe_filename}_{session.id}.txt"

            st.download_button(
                label="Download Transcript (.txt)",
                data=export_data,
                file_name=export_filename,
                mime="text/plain",
                use_container_width=True
            )
        else:
            st.caption("No messages found to export" + (f" matching '{search_term}'." if search_term else "."))


    except Exception as e:
        st.error(f"An error occurred while loading chat history: {e}")
        # Add more detailed error logging if needed for debugging
        # import traceback
        # st.error(traceback.format_exc())