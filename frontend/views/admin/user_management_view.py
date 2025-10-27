# frontend/views/admin/user_management_view.py
import streamlit as st
from backend.db.db_handler import (
    get_session,
    get_all_users, # This function now eagerly loads documents/sessions
    delete_user_by_id,
    # get_documents_by_user, # Not strictly needed if using eager loading
    update_user_role,
    delete_document_by_id
)
# We might need User model if accessing attributes directly not covered by eager load, but likely okay now
# from backend.db.models import User

def render_user_management_view():
    st.title("👥 User Management")
    st.markdown("View, manage roles, and delete users.") # Updated description
    st.divider() # Use divider for better spacing

    current_admin_id = st.session_state.auth.get("user_id")

    # --- Helper functions ---
    def handle_role_change(user_id):
        new_role = st.session_state[f"role_select_{user_id}"]
        with get_session() as db:
            update_user_role(db, user_id, new_role)
        st.toast(f"Updated role for user ID {user_id} to '{new_role}'.", icon="✅")
        # No rerun needed, selectbox updates visually

    def handle_doc_delete(doc_id, doc_name):
        # Add spinner for user feedback during deletion
        with st.spinner(f"Deleting '{doc_name}'..."):
            with get_session() as db:
                success, message = delete_document_by_id(db, doc_id)
        if success:
            st.toast(message, icon="✅")
            st.rerun() # Rerun needed to refresh the document list within expander
        else:
            st.error(message)

    try:
        # Fetch users with eagerly loaded documents/sessions
        with get_session() as db:
            all_users = get_all_users(db)

        st.subheader(f"Total Registered Users: {len(all_users)}")

        # --- Table Headers ---
        # Adjusted column widths for better spacing
        cols = st.columns([0.5, 1.2, 1.2, 1.2, 1.8, 1.5, 0.8, 0.8])
        header_map = ["ID", "Username", "First Name", "Last Name", "Email", "Joined On", "Role", "Actions"]
        for col, header in zip(cols, header_map):
            col.markdown(f"**{header}**")
        st.divider()

        # --- User List ---
        if not all_users:
             st.info("No users found.")
        else:
            for user in all_users:
                is_current_admin = (user.id == current_admin_id)

                cols = st.columns([0.5, 1.2, 1.2, 1.2, 1.8, 1.5, 0.8, 0.8]) # Match header columns

                # Display user data
                cols[0].write(user.id)
                cols[1].write(user.username)
                cols[2].write(user.first_name)
                cols[3].write(user.last_name)
                cols[4].write(user.email)
                # Use a slightly more compact date format
                cols[5].write(user.created_at.strftime("%Y-%m-%d %H:%M"))

                # --- Role Selectbox ---
                with cols[6]:
                    if not is_current_admin:
                        st.selectbox(
                            "Role", options=["user", "admin"],
                            index=["user", "admin"].index(user.role),
                            key=f"role_select_{user.id}", label_visibility="collapsed",
                            on_change=handle_role_change, args=(user.id,)
                        )
                    else:
                        st.markdown(f"**👑 {user.role}**") # Indicate Admin role visually

                # --- Delete User Button ---
                with cols[7]:
                    if not is_current_admin:
                        popover = st.popover("Delete", use_container_width=True, help="Delete this user")
                        with popover:
                            st.error(f"Delete user '{user.username}'? This action includes all their documents, chats, and summaries and cannot be undone.")
                            if st.button(f"Confirm Delete User {user.id}", type="primary"):
                                with st.spinner("Deleting user and associated data..."):
                                     with get_session() as db_action:
                                        delete_user_by_id(db_action, user.id)
                                st.toast(f"User '{user.username}' deleted.", icon="🗑️")
                                st.rerun() # Refresh the user list
                    else:
                        st.caption("(You)") # Indicate the currently logged-in admin

                # --- Expander for Document Management ---
                # Accessing user.documents is now safe due to eager loading in get_all_users
                doc_count = len(user.documents) if hasattr(user, 'documents') else 0
                with st.expander(f"Manage {user.username}'s Documents ({doc_count})"):
                    # Use the already loaded documents
                    user_docs = user.documents

                    if not user_docs:
                        st.info("This user has not uploaded any documents.")
                    else:
                        st.write(f"**{len(user_docs)} document(s):**")
                        for doc in user_docs:
                            doc_cols = st.columns([4, 1])
                            doc_cols[0].code(doc.filename, language=None)

                            doc_popover = doc_cols[1].popover("Remove")
                            with doc_popover:
                                st.error(f"Delete '{doc.filename}'?")
                                if st.button(f"Confirm Delete Doc {doc.id}", type="primary"):
                                    # Pass doc_id and doc_name to handler
                                    handle_doc_delete(doc.id, doc.filename)

                st.divider() # Divider between users

    except Exception as e:
        st.error(f"An error occurred while rendering user management: {e}")
        # import traceback # Uncomment for detailed debugging
        # st.exception(e)