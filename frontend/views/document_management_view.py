# frontend/views/document_management_view.py
import streamlit as st
from backend.db.db_handler import (
    get_session,
    get_documents_by_user,
    delete_document_by_id,
    rename_document # <-- Make sure this line is present
)

def render_document_management_view(user_id):
    st.title("📚 Document Management")
    st.markdown("Manage your uploaded PDF documents.")
    st.markdown("---")

    try:
        with get_session() as db:
            user_docs = get_documents_by_user(db, user_id)

        if not user_docs:
            st.info("You haven't uploaded any documents yet.")
            return # Exit if no documents

        st.subheader(f"Your Documents ({len(user_docs)})")

        # Display each document with options
        for doc in user_docs:
            with st.container(border=True):
                col1, col2, col3 = st.columns([4, 1, 1]) # Name | Rename | Delete

                with col1:
                    st.markdown(f"**{doc.filename}**")
                    st.caption(f"Uploaded: {doc.created_at.strftime('%Y-%m-%d %H:%M')}")

                with col2:
                    # Rename Popover
                    rename_popover = st.popover("✏️ Rename", use_container_width=True)
                    with rename_popover:
                        st.write(f"Rename '{doc.filename}':")
                        new_name = st.text_input(
                            "New filename (.pdf)",
                            value=doc.filename,
                            key=f"rename_text_input_{doc.id}", # Changed key
                            label_visibility="collapsed"
                        )
                        if st.button("Save Name", key=f"save_rename_button_{doc.id}"): # Changed key
                            if new_name and new_name.strip() and new_name != doc.filename:
                                with st.spinner("Renaming..."):
                                     with get_session() as db_action:
                                        success, message = rename_document(db_action, doc.id, user_id, new_name.strip())
                                if success:
                                    st.toast(message, icon="✅")
                                    st.rerun() # Refresh page
                                else:
                                    st.error(message) # Show error from backend
                            elif not new_name or not new_name.strip():
                                st.warning("Filename cannot be empty.")
                            else:
                                st.toast("Filename unchanged.", icon="ℹ️")

                with col3:
                    # Delete Popover (reused logic)
                    delete_popover = st.popover("🗑️ Delete", use_container_width=True)
                    with delete_popover:
                        st.error(f"Permanently delete '{doc.filename}'?")
                        if st.button("Confirm Delete", key=f"confirm_delete_button_{doc.id}", type="primary"): # Changed key and button text
                            with st.spinner("Deleting document and index..."):
                                with get_session() as db_action:
                                    success, message = delete_document_by_id(db_action, doc.id)
                            if success:
                                st.toast(message, icon="✅")
                                st.rerun()
                            else:
                                st.error(message)

    except Exception as e:
        st.error(f"An error occurred while fetching documents: {e}")