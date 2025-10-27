# frontend/views/insights_view.py
import streamlit as st
import pandas as pd
from backend.db.db_handler import get_session, get_document_by_name_for_user
from backend.insights_extractor import extract_insights # Import the main function

def render_insights_view(user_id):
    st.title("💡 Document Insights")
    st.markdown("Generate and view key insights from your selected document.")
    st.markdown("---")

    # --- Document Selection ---
    active_doc_name = st.session_state.get("active_doc")
    active_doc_obj = None

    if not active_doc_name or active_doc_name == "🔎 All My Documents":
        st.warning("👈 Please select a specific document from the sidebar first.")
        return

    # Fetch the document object to get its text and path
    try:
        with get_session() as db:
            active_doc_obj = get_document_by_name_for_user(db, user_id, active_doc_name)
        if not active_doc_obj:
            st.error(f"Could not load document: {active_doc_name}")
            return
    except Exception as e:
        st.error(f"Error loading document: {e}")
        return

    st.subheader(f"Insights for: {active_doc_name}")

    # --- Summary Button ---
    if st.button("📝 Generate Summary", key="generate_summary_btn", type="primary"):
        # Use session state to store generated insights for the active doc
        cache_key = f"insights_{active_doc_obj.id}"
        with st.spinner("Analyzing document and extracting insights..."):
            try:
                # Pass both text and file path (if available)
                insights_data = extract_insights(active_doc_obj.full_text, active_doc_obj.filepath)
                st.session_state[cache_key] = insights_data
                st.success("Insights generated successfully!")
            except Exception as e:
                st.error(f"Failed to generate insights: {e}")
                if cache_key in st.session_state:
                     del st.session_state[cache_key] # Clear potentially partial results

    # --- Display Generated Insights ---
    cache_key = f"insights_{active_doc_obj.id}"
    if cache_key in st.session_state:
        insights = st.session_state[cache_key]
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            # Keywords & Word Cloud
            st.subheader("🔑 Keywords")
            if insights.get("keywords"):
                st.write(", ".join(insights["keywords"]))
            else:
                st.caption("No keywords extracted.")

            if insights.get("word_cloud_image"):
                 st.image(insights["word_cloud_image"], caption="Keyword Word Cloud", use_container_width=True)

            st.divider()
            # Document Stats
            st.subheader("📊 Document Stats")
            stats = insights.get("figures_tables", {})
            st.metric("Pages", stats.get("pages", "N/A"))
            st.metric("Total Images Found", stats.get("total_images", "N/A"))
            # st.metric("Likely Table Lines", stats.get("likely_table_lines", "N/A")) # Optional

        with col2:
            # Sentiment
            st.subheader("😊 Sentiment Overview")
            sentiment = insights.get("sentiment")
            if sentiment:
                sentiment_label = "Neutral"
                if sentiment['compound'] > 0.05: sentiment_label = "Positive"
                elif sentiment['compound'] < -0.05: sentiment_label = "Negative"
                st.metric("Overall Sentiment", sentiment_label, f"{sentiment['compound']:.2f} score")
                # Optional: Show detailed scores
                # st.progress(sentiment['pos'], text=f"Positive: {sentiment['pos']:.1%}")
                # st.progress(sentiment['neu'], text=f"Neutral: {sentiment['neu']:.1%}")
                # st.progress(sentiment['neg'], text=f"Negative: {sentiment['neg']:.1%}")
            else:
                st.caption("Sentiment analysis not available.")

            st.divider()
            # Named Entities
            st.subheader("👤 Named Entities")
            entities = insights.get("entities")
            if entities:
                 for label, items in entities.items():
                      if items: # Only show labels with found entities
                           st.markdown(f"**{label}:**")
                           # Create a mini-dataframe for cleaner display
                           df = pd.DataFrame(items, columns=['Entity', 'Count'])
                           st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                 st.caption("No named entities extracted or extraction failed.")

    else:
         st.info("Click the 'Generate Summary' button to summarize the document.")