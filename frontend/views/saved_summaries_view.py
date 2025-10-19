# frontend/views/saved_summaries_view.py
import streamlit as st
from backend.db.db_handler import get_session, get_summaries_by_user, delete_summary_by_id

def render_saved_summaries_view(user_id):
    st.title("📌 Saved Summaries & Insights")
    st.markdown("Review summaries you've previously generated.")
    st.markdown("---")

    try:
        with get_session() as db:
            summaries = get_summaries_by_user(db, user_id)

        if not summaries:
            st.info("You haven't saved any summaries yet. Generate one from the 'Extracted Text' page.")
            return

        st.subheader(f"You have {len(summaries)} saved summaries:")

        for summary in summaries:
            with st.expander(f"**{summary.filename}** - {summary.level} Summary ({summary.created_at.strftime('%Y-%m-%d %H:%M')})"):
                st.markdown(summary.content)
                st.caption(f"Generated with: {summary.provider}")
                
                # Add delete button
                if st.button("Delete Summary", key=f"delete_summary_{summary.id}", type="secondary"):
                    with st.spinner("Deleting..."):
                        with get_session() as db_action:
                           delete_summary_by_id(db_action, summary.id)
                    st.rerun() # Refresh the list

    except Exception as e:
        st.error(f"An error occurred while fetching summaries: {e}")