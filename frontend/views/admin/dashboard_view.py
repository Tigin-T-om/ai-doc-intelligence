# frontend/views/admin/dashboard_view.py
import streamlit as st
import pandas as pd
import plotly.express as px # Import Plotly
from itertools import product # Import product
from backend.db.db_handler import (
    get_session,
    count_total_users,
    count_total_documents,
    count_total_chat_sessions,
    get_all_users,
    get_all_documents,
    get_recent_users,
    get_recent_documents,
    count_users_by_role,
    count_recent_chat_sessions,
    get_all_summaries, # New: Fetches all summary objects
    get_all_chat_sessions, # New: Fetches all chat sessions
    get_recent_chat_sessions # New: Fetches recent chat sessions
)
# --- Need Models for data processing ---
from backend.db.models import User, Document, ChatSession, Summary
from datetime import datetime, timedelta, timezone # Ensure timezone is imported

# Helper function to create safe dataframes for charting
def create_chart_df(data, date_col='created_at', type_col=None):
    """
    Creates a Pandas DataFrame suitable for time-series charting
    from a list of SQLAlchemy objects OR dictionaries.
    Ensures the output DataFrame has 'date', 'count', and (optionally) 'type' columns.
    """
    if not data:
        cols = ['date', 'count']
        if type_col:
            cols.append('type')
        return pd.DataFrame(columns=cols)

    df_data = []
    is_dict = isinstance(data[0], dict)

    for item in data:
        try:
            date_value = item[date_col] if is_dict else getattr(item, date_col)
            record = {'date': pd.to_datetime(date_value).date()} # Ensure date only here
            if type_col:
                record['type'] = item[type_col] if is_dict else getattr(item, type_col)
            df_data.append(record)
        except (AttributeError, KeyError) as e:
            continue
        except Exception as e:
            continue

    if not df_data:
        cols = ['date', 'count']
        if type_col:
            cols.append('type')
        return pd.DataFrame(columns=cols)

    df = pd.DataFrame(df_data)
    # Ensure the date column is a datetime object and normalize it to remove time component
    df['date'] = pd.to_datetime(df['date']).dt.normalize() # Normalize to start of day

    if type_col:
        # Group by date and type, and count occurrences
        grouped_counts = df.groupby(['date', 'type']).size().reset_index(name='count')

        if not grouped_counts.empty:
            min_date, max_date = grouped_counts['date'].min(), grouped_counts['date'].max()
            full_dates = pd.date_range(min_date, max_date, freq='D')
            all_types = grouped_counts['type'].unique()

            # Create a full DataFrame for all dates and types
            from itertools import product
            full_df = pd.DataFrame([
                {'date': date, 'type': type_val}
                for date, type_val in product(full_dates, all_types)
            ])
            # Merge with actual counts
            final_df = pd.merge(full_df, grouped_counts, on=['date', 'type'], how='left').fillna(0)
            final_df['count'] = final_df['count'].astype(int) # Ensure count is int
            # Convert date to string for explicit categorical X-axis in Plotly
            final_df['date'] = final_df['date'].dt.strftime('%Y-%m-%d')
            return final_df
        else:
            return pd.DataFrame(columns=['date', 'count', 'type'])
    else:
        # Simple count per day
        grouped_counts = df.groupby('date').size().reset_index(name='count')

        if not grouped_counts.empty:
            min_date, max_date = grouped_counts['date'].min(), grouped_counts['date'].max()
            full_dates = pd.date_range(min_date, max_date, freq='D')

            # Create a DataFrame with all dates, then merge with actual counts
            full_df = pd.DataFrame(full_dates, columns=['date'])
            # Merge on 'date', filling NaN counts with 0
            final_df = pd.merge(full_df, grouped_counts, on='date', how='left').fillna(0)
            final_df['count'] = final_df['count'].astype(int) # Ensure count is int
            # Convert date to string for explicit categorical X-axis in Plotly
            final_df['date'] = final_df['date'].dt.strftime('%Y-%m-%d')
            return final_df
        else:
            return pd.DataFrame(columns=['date', 'count'])


# --- Main Render Function ---
def render_dashboard_view():
    st.set_page_config(layout="wide") # Use wide layout for dashboards
    st.title("👑 Admin Dashboard")
    st.markdown("Comprehensive overview of platform activity and usage trends.")
    st.divider()

    @st.cache_data(ttl=5) # Cache data for 5 seconds to ensure freshness while maintaining performance
    def get_dashboard_data():
        with get_session() as db:
            total_users = count_total_users(db)
            total_docs = count_total_documents(db)
            total_sessions = count_total_chat_sessions(db)
            role_counts_list = count_users_by_role(db)
            chats_last_24h = count_recent_chat_sessions(db, hours=24)
            all_users = get_all_users(db)
            all_docs = get_all_documents(db)
            all_summaries = get_all_summaries(db)
            all_chat_sessions = get_all_chat_sessions(db)
            recent_users = get_recent_users(db, limit=5)
            recent_docs = get_recent_documents(db, limit=5)
            recent_chats = get_recent_chat_sessions(db, limit=5)
        return (
            total_users, total_docs, total_sessions, role_counts_list,
            chats_last_24h, all_users, all_docs, all_summaries,
            all_chat_sessions, recent_users, recent_docs, recent_chats
        )

    try:
        (
            total_users, total_docs, total_sessions, role_counts_list,
            chats_last_24h, all_users, all_docs, all_summaries,
            all_chat_sessions, recent_users, recent_docs, recent_chats
        ) = get_dashboard_data()

        avg_docs_per_user = (total_docs / total_users) if total_users > 0 else 0
        total_summaries = len(all_summaries)

    except Exception as e:
        st.error(f"Failed to load dashboard data: {e}")
        # Uncomment for detailed debugging:
        # import traceback
        # st.exception(e) # This will print the full traceback in the UI
        return # Stop rendering if data fails

    # --- Create Tabs ---
    tab_overview, tab_users, tab_docs, tab_insights, tab_chatbot = st.tabs([
        "📊 Overview", "👥 Users", "📂 Documents", "💡 Insights", "💬 Chatbot"
    ])

    # === Overview Tab ===
    with tab_overview:
        st.subheader("Key Performance Indicators")
        cols_kpi = st.columns(5) # 5 columns for main KPIs
        cols_kpi[0].metric(label="👥 Total Users", value=total_users)
        cols_kpi[1].metric(label="📂 Total Documents", value=total_docs)
        cols_kpi[2].metric(label="📌 Total Summaries", value=total_summaries)
        cols_kpi[3].metric(label="💬 Total Chats", value=total_sessions)
        cols_kpi[4].metric(label="⏰ Chats (Last 24h)", value=chats_last_24h)
        st.divider()

        st.subheader("Overall Platform Activity Trends")
        # Combine data for overview chart - passing lists of dictionaries
        user_chart_data = [{'created_at': u.created_at, 'type': 'Signup'} for u in all_users]
        doc_chart_data = [{'created_at': d.created_at, 'type': 'Upload'} for d in all_docs]
        chat_chart_data = [{'created_at': c.created_at, 'type': 'Chat'} for c in all_chat_sessions]

        df_overview_activity = create_chart_df(user_chart_data + doc_chart_data + chat_chart_data, type_col='type')
        # st.dataframe(df_overview_activity, use_container_width=True) # DEBUG

        if not df_overview_activity.empty:
            fig_overview = px.bar(
                df_overview_activity,
                x='date',
                y='count',
                color='type',
                title="Daily Activity: Signups, Uploads, & Chats",
                labels={'count':'Count', 'date':'Date', 'type':'Activity Type'},
                # line_shape="spline" # Removed for bar chart
            )
            fig_overview.update_layout(hovermode="x unified") # Enhanced hover
            st.plotly_chart(fig_overview, use_container_width=True)
        else:
            st.info("No activity data to display yet.")

        st.divider()
        st.subheader("Recent Platform Activity")
        col_recent1, col_recent2, col_recent3 = st.columns(3)
        with col_recent1:
            st.markdown("##### Newest Users")
            if recent_users:
                 for user in recent_users:
                     st.container(border=True).markdown(f"**{user.username}** - *Joined: {user.created_at.strftime('%Y-%m-%d')}*")
            else: st.caption("No users have registered yet.")
        with col_recent2:
            st.markdown("##### Recent Uploads")
            if recent_docs:
                user_ids = {doc.user_id for doc in recent_docs}
                users_dict = {}
                if user_ids:
                    with get_session() as db_users:
                        doc_owners = db_users.query(User).filter(User.id.in_(user_ids)).all()
                        users_dict = {owner.id: owner.username for owner in doc_owners}
                for doc in recent_docs:
                    owner = users_dict.get(doc.user_id, "Unknown")
                    st.container(border=True).markdown(f"**{doc.filename}** by *{owner}*")
            else: st.caption("No documents have been uploaded.")
        with col_recent3:
            st.markdown("##### Recent Chat Sessions")
            if recent_chats:
                user_ids_chats = {chat.user_id for chat in recent_chats}
                users_dict_chats = {}
                if user_ids_chats:
                     with get_session() as db_users_chats:
                          chat_owners = db_users_chats.query(User).filter(User.id.in_(user_ids_chats)).all()
                          users_dict_chats = {owner.id: owner.username for owner in chat_owners}
                for chat in recent_chats:
                     owner = users_dict_chats.get(chat.user_id, "Unknown")
                     st.container(border=True).markdown(f"**{chat.name}** by *{owner}*")
            else: st.caption("No chat sessions started.")


    # === Users Tab ===
    with tab_users:
        st.subheader("User Analytics")
        col_growth, col_role_pie = st.columns(2)

        with col_growth:
            st.markdown("##### User Signups Over Time")
            # Passing SQLAlchemy objects directly
            df_user_signups = create_chart_df(all_users)
            if not df_user_signups.empty:
                 fig_users = px.bar(
                    df_user_signups,
                    x='date',
                    y='count',
                    title="User Signups Daily",
                    labels={'count':'New Users', 'date':'Date'},
                    # line_shape="spline" # Removed for bar chart
                 )
                 fig_users.update_layout(hovermode="x unified")
                 st.plotly_chart(fig_users, use_container_width=True)
            else: st.info("No user signup data yet.")

        with col_role_pie:
             st.markdown("##### User Role Distribution")
             if role_counts_list:
                  roles_df = pd.DataFrame(role_counts_list, columns=['Role', 'Count'])
                  fig_roles = px.pie(
                      roles_df,
                      names='Role',
                      values='Count',
                      title="Admin vs. Regular Users",
                      hole=0.3, # Donut chart
                      color_discrete_sequence=px.colors.sequential.RdBu
                  )
                  fig_roles.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
                  st.plotly_chart(fig_roles, use_container_width=True)
             else: st.info("No user role data yet.")

        st.markdown("---")
        st.markdown("##### Additional User Metrics")
        col_user_metrics = st.columns(2)
        col_user_metrics[0].metric(label="Avg Documents per User", value=f"{avg_docs_per_user:.1f}")

    # === Documents Tab ===
    with tab_docs:
        st.subheader("Document Analytics")
        col_doc_trends, col_doc_dist = st.columns(2)

        with col_doc_trends:
            st.markdown("##### Document Uploads Over Time")
            # Passing SQLAlchemy objects directly
            df_doc_uploads = create_chart_df(all_docs)
            if not df_doc_uploads.empty:
                fig_docs = px.bar(
                    df_doc_uploads,
                    x='date',
                    y='count',
                    title="Daily Document Uploads",
                    labels={'count':'Uploads', 'date':'Date'},
                    # line_shape="spline"
                )
                fig_docs.update_layout(hovermode="x unified")
                st.plotly_chart(fig_docs, use_container_width=True)
            else: st.info("No document upload data yet.")

        with col_doc_dist:
            st.markdown("##### File Type Distribution")
            if all_docs:
                file_types = [doc.filename.split('.')[-1].lower() for doc in all_docs if '.' in doc.filename]
                df_file_types = pd.DataFrame({'File Type': file_types})
                type_counts = df_file_types['File Type'].value_counts().reset_index()
                type_counts.columns = ['File Type', 'Count']
                fig_file_types = px.pie(
                    type_counts,
                    names='File Type',
                    values='Count',
                    title="Uploaded File Type Breakdown",
                    hole=0.3,
                    color_discrete_sequence=px.colors.sequential.Aggrnyl
                )
                fig_file_types.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
                st.plotly_chart(fig_file_types, use_container_width=True)
            else: st.info("No document data for file type analysis.")

        st.markdown("---")
        # st.markdown("##### Most Accessed Documents (Placeholder)") # Removed placeholder
        # st.info("This feature would require tracking document access events in the backend.") # Removed placeholder


    # === Insights Tab ===
    with tab_insights:
        st.subheader("Summary & Insights Analytics")
        col_sum_metric, col_sum_pie = st.columns(2)
        col_sum_metric.metric("📌 Total Summaries Generated", value=total_summaries)

        if all_summaries:
             summary_levels = [s.level for s in all_summaries]
             df_levels = pd.DataFrame({'Level': summary_levels})
             level_counts = df_levels['Level'].value_counts().reset_index()
             level_counts.columns = ['Level', 'Count']

             with col_sum_pie:
                 fig_levels = px.pie(
                     level_counts,
                     names='Level',
                     values='Count',
                     title="Summary Length Distribution",
                     hole=0.3,
                     color_discrete_sequence=px.colors.sequential.Blues
                 )
                 fig_levels.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
                 st.plotly_chart(fig_levels, use_container_width=True)
        else:
             col_sum_pie.info("No summary data to display.")

        st.markdown("---")
        # st.markdown("##### Top Keywords Extracted / Sentiment Distribution (Placeholders)") # Removed placeholder
        # st.info("Visualizing aggregated keywords or sentiment across all documents would require storing/processing this data in the backend.") # Removed placeholder


    # === Chatbot Tab ===
    with tab_chatbot:
        st.subheader("Chatbot Usage Analytics")
        col_chat_trends, col_chat_metrics = st.columns(2)

        with col_chat_trends:
            st.markdown("##### Chat Sessions Over Time")
            # Passing SQLAlchemy objects directly
            df_chat_sessions = create_chart_df(all_chat_sessions)
            if not df_chat_sessions.empty:
                fig_chats = px.bar(
                    df_chat_sessions,
                    x='date',
                    y='count',
                    title="Daily Chat Sessions Started",
                    labels={'count':'Sessions', 'date':'Date'},
                    # line_shape="spline"
                )
                fig_chats.update_layout(hovermode="x unified")
                st.plotly_chart(fig_chats, use_container_width=True)
            else: st.info("No chat session data yet.")

        with col_chat_metrics:
            st.metric("Total Chat Sessions", value=total_sessions)


    # Removed System Performance tab as it's optional and requires more backend tracking
    # If you want to add it later, you'd need to implement:
    # - Logging of processing times for documents/summaries
    # - Tracking of LLM response times
    # - Error logging