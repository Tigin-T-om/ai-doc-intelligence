# frontend/views/admin/dashboard_view.py
import streamlit as st
import pandas as pd
from backend.db.db_handler import (
    get_session, 
    count_total_users, 
    count_total_documents, 
    count_total_chat_sessions,
    get_all_users,
    get_all_documents,
    get_recent_users,
    get_recent_documents
)

def render_dashboard_view():
    st.title("👑 Admin Dashboard")
    st.markdown("---")
    
    # --- 1. Key Performance Indicators (KPIs) ---
    st.header("Platform Analytics")
    try:
        with get_session() as db:
            total_users = count_total_users(db)
            total_docs = count_total_documents(db)
            total_sessions = count_total_chat_sessions(db)

        col1, col2, col3 = st.columns(3)
        col1.metric(label="👥 Total Users", value=total_users)
        col2.metric(label="📂 Total Documents", value=total_docs)
        col3.metric(label="💬 Total Chat Sessions", value=total_sessions)
            
    except Exception as e:
        st.error(f"An error occurred while fetching KPIs: {e}")

    st.markdown("---")

    # --- 2. Activity Graphs ---
    st.header("Activity Over Time")
    try:
        with get_session() as db:
            all_users = get_all_users(db)
            all_docs = get_all_documents(db)

        # Process data for user signups chart
        if all_users:
            # Extract just the date from the datetime
            user_data = [{"date": user.created_at.date()} for user in all_users]
            user_df = pd.DataFrame(user_data)
            
            # Count signups per day
            user_signups = user_df.groupby('date').size().reset_index(name='Signups')
            user_signups = user_signups.set_index('date')
        else:
            user_signups = pd.DataFrame(columns=['Signups'])

        # Process data for document uploads chart
        if all_docs:
            doc_data = [{"date": doc.created_at.date()} for doc in all_docs]
            doc_df = pd.DataFrame(doc_data)
            
            # Count uploads per day
            doc_uploads = doc_df.groupby('date').size().reset_index(name='Uploads')
            doc_uploads = doc_uploads.set_index('date')
        else:
            doc_uploads = pd.DataFrame(columns=['Uploads'])

        # Display charts in columns
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("New User Signups")
            st.line_chart(user_signups)
        with col2:
            st.subheader("Document Uploads")
            st.line_chart(doc_uploads)

    except Exception as e:
        st.error(f"An error occurred while building charts: {e}")

    st.markdown("---")

    # --- 3. Recent Activity Feeds ---
    st.header("Recent Activity")
    try:
        with get_session() as db:
            recent_users = get_recent_users(db, limit=5)
            recent_docs = get_recent_documents(db, limit=5)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Newest Users")
            if recent_users:
                for user in recent_users:
                    st.container(border=True).markdown(
                        f"**{user.username}** (ID: {user.id})\n\n"
                        f"*Joined: {user.created_at.strftime('%Y-%m-%d %H:%M')}*"
                    )
            else:
                st.caption("No users have registered yet.")
        
        with col2:
            st.subheader("Recent Uploads")
            if recent_docs:
                for doc in recent_docs:
                    st.container(border=True).markdown(
                        f"**{doc.filename}** (User ID: {doc.user_id})\n\n"
                        f"*Uploaded: {doc.created_at.strftime('%Y-%m-%d %H:%M')}*"
                    )
            else:
                st.caption("No documents have been uploaded.")

    except Exception as e:
        st.error(f"An error occurred while fetching recent activity: {e}")