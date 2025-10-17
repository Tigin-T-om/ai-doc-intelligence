# frontend/views/admin/user_management_view.py
import streamlit as st
from backend.db.db_handler import (
    get_session, 
    get_all_users, 
    delete_user_by_id, 
    get_documents_by_user,
    update_user_role,
    delete_document_by_id
)

def render_user_management_view():
    st.title("👥 User Management")
    st.markdown("---")

    current_admin_id = st.session_state.auth.get("user_id")

    # --- Helper function for role change callback ---
    def handle_role_change(user_id):
        new_role = st.session_state[f"role_select_{user_id}"]
        with get_session() as db:
            update_user_role(db, user_id, new_role)
        st.toast(f"Updated role for user {user_id} to {new_role}.", icon="✅")

    # --- Helper function for document deletion ---
    def handle_doc_delete(doc_id, doc_name):
        with get_session() as db:
            success, message = delete_document_by_id(db, doc_id)
        if success:
            st.toast(message, icon="✅")
            st.rerun() 
        else:
            st.error(message)

    try:
        with get_session() as db:
            all_users = get_all_users(db)
            
        st.subheader(f"Total Registered Users: {len(all_users)}")

        # --- Table Headers ---
        cols = st.columns([1, 2, 2, 2, 1])
        cols[0].markdown("**User ID**")
        cols[1].markdown("**Username**")
        cols[2].markdown("**Joined On**")
        cols[3].markdown("**Role**")
        cols[4].markdown("**Actions**")
        st.divider()

        # --- User List ---
        for user in all_users:
            is_current_admin = (user.id == current_admin_id)

            cols = st.columns([1, 2, 2, 2, 1])
            
            cols[0].write(user.id)
            cols[1].write(user.username)
            cols[2].write(user.created_at.strftime("%Y-%m-%d %H:%M"))
            
            # --- Role Selectbox ---
            with cols[3]:
                if not is_current_admin:
                    st.selectbox(
                        "Role",
                        options=["user", "admin"],
                        index=["user", "admin"].index(user.role),
                        key=f"role_select_{user.id}",
                        label_visibility="collapsed",
                        on_change=handle_role_change,
                        args=(user.id,)
                    )
                else:
                    st.markdown(f"**👑 {user.role}**") 

            # --- Delete User Button ---
            with cols[4]:
                if not is_current_admin:
                    # --- ★★★ BUG FIX IS HERE ★★★ ---
                    # We create the popover first...
                    popover = st.popover("Delete", use_container_width=True)
                    # ...then we add content to it using 'with'.
                    # This stops it from opening by default.
                    with popover:
                        st.error(f"Delete user '{user.username}'? This is permanent.")
                        if st.button(f"Confirm Delete {user.id}", type="primary"):
                            with get_session() as db_action:
                                delete_user_by_id(db_action, user.id)
                            st.rerun()
                    # --- ★★★ END OF FIX ★★★ ---
                else:
                    st.caption("(You)")

            # --- Expander for Document Management ---
            with st.expander(f"Manage {user.username}'s Documents"):
                with get_session() as db_docs:
                    user_docs = get_documents_by_user(db_docs, user.id)
                
                if not user_docs:
                    st.info("This user has not uploaded any documents.")
                else:
                    st.write(f"**{len(user_docs)} document(s):**")
                    for doc in user_docs:
                        doc_cols = st.columns([4, 1])
                        doc_cols[0].code(doc.filename, language=None)
                        
                        # --- ★★★ BUG FIX IS HERE ★★★ ---
                        # Applied the same fix for the document remove button
                        doc_popover = doc_cols[1].popover("Remove")
                        with doc_popover:
                            st.error(f"Delete '{doc.filename}'?")
                            if st.button(f"Confirm Delete Doc {doc.id}", type="primary"):
                                handle_doc_delete(doc.id, doc.filename)
                        # --- ★★★ END OF FIX ★★★ ---
            
            st.divider()

    except Exception as e:
        st.error(f"An error occurred while fetching users: {e}")