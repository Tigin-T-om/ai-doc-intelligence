# frontend/views/insights_view.py
import streamlit as st
import pandas as pd
import plotly.express as px # Import plotly
from backend.db.db_handler import get_session, get_document_by_name_for_user
from backend.insights_extractor import extract_insights
from typing import Dict, List, Any

# Helper to render text with highlighted entities
def render_annotated_text(full_text: str, raw_entities_with_offsets: Dict[str, List[Dict[str, Any]]]):
    if not full_text or not raw_entities_with_offsets:
        return "No text or entities to display."

    # Flatten and sort all entities by their start offset
    all_flat_entities = []
    for label, entities_list in raw_entities_with_offsets.items():
        for ent in entities_list:
            all_flat_entities.append((ent["start"], ent["end"], ent["text"], label))
    all_flat_entities.sort(key=lambda x: x[0])

    annotated_html_parts = []
    last_idx = 0
    
    # Define some distinct colors for different entity types
    # This is a simple assignment; for more robust styling, a CSS class mapping would be better
    label_colors = {
        "PERSON": "background-color:#ffe0b2;",  # Light Orange
        "ORG": "background-color:#c8e6c9;",     # Light Green
        "GPE": "background-color:#bbdefb;",     # Light Blue
        "DATE": "background-color:#ffccbc;",    # Light Red
        "CARDINAL": "background-color:#f0f4c3;", # Light Yellow
        "NORP": "background-color:#d1c4e9;",     # Light Purple
        "LOC": "background-color:#b2ebf2;",      # Light Cyan
        "PRODUCT": "background-color:#f8bbd0;",  # Light Pink
        "EVENT": "background-color:#d7ccc8;",     # Light Brown
        "WORK_OF_ART": "background-color:#cfd8dc;", # Light Grey
        "LAW": "background-color:#a7ffeb;",       # Light Aqua
        "LANGUAGE": "background-color:#c5cae9;",  # Lavender
    }

    for start, end, text, label in all_flat_entities:
        # Add text before the current entity
        annotated_html_parts.append(full_text[last_idx:start])
        
        # Add the entity with highlighting and tooltip
        color_style = label_colors.get(label, "background-color: #ffeb3b;") # Default yellow
        annotated_html_parts.append(
            f'<span style="{color_style} padding: 2px 4px; border-radius: 3px; cursor: help;" '
            f'title="{label}">{text}</span>'
        )
        last_idx = end

    # Add any remaining text after the last entity
    annotated_html_parts.append(full_text[last_idx:])

    return " ".join(annotated_html_parts)

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
                
                # --- Bar Chart for Keywords and Scores ---
                keyword_scores = insights.get("keyword_scores")
                if keyword_scores:
                    df_keywords = pd.DataFrame(keyword_scores, columns=['Keyword', 'TF-IDF Score'])
                    fig_keywords = px.bar(
                        df_keywords,
                        x='TF-IDF Score',
                        y='Keyword',
                        orientation='h',
                        title="Keyword TF-IDF Scores",
                        labels={'TF-IDF Score':'Score', 'Keyword':'Keyword'},
                        hover_data={'TF-IDF Score':':.3f'}
                    )
                    fig_keywords.update_layout(yaxis={'categoryorder': 'total ascending'})
                    st.plotly_chart(fig_keywords, use_container_width=True)
                # ----------------------------------------

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
                
                # --- Sentiment Distribution Pie Chart ---
                sentiment_data = {'Sentiment': ['Positive', 'Neutral', 'Negative'],
                                  'Score': [sentiment['pos'], sentiment['neu'], sentiment['neg']]} # Fixed key names
                df_sentiment = pd.DataFrame(sentiment_data)

                fig_sentiment = px.pie(
                    df_sentiment,
                    values='Score',
                    names='Sentiment',
                    title='Sentiment Distribution',
                    hole=0.3,
                    color_discrete_map={'Positive':'#28a745', 'Neutral':'#6c757d', 'Negative':'#dc3545'}
                )
                fig_sentiment.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
                st.plotly_chart(fig_sentiment, use_container_width=True)
                # ----------------------------------------

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

            # --- Sentiment Trend Line Chart ---
            st.subheader("📈 Sentiment Trend Across Document")
            sentiment_trend = insights.get("sentiment_trend")
            if sentiment_trend:
                df_sentiment_trend = pd.DataFrame(sentiment_trend)
                fig_trend = px.line(
                    df_sentiment_trend,
                    x='segment',
                    y='compound',
                    title='Sentiment Score by Document Segment',
                    labels={'segment':'Document Segment', 'compound':'Compound Sentiment Score'},
                    hover_data={'pos':':.2f', 'neu':':.2f', 'neg':':.2f'}
                )
                fig_trend.update_yaxes(range=[-1, 1]) # Sentiment scores are typically between -1 and 1
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.caption("No sentiment trend data available (might need NLTK Vader).")
            # ----------------------------------

            # --- Annotated Text Display ---
            st.subheader("Highlighted Entities in Text")
            full_text = insights.get("full_text")
            raw_entities = insights.get("raw_entities_with_offsets")
            if full_text and raw_entities:
                annotated_html = render_annotated_text(full_text, raw_entities)
                st.markdown(annotated_html, unsafe_allow_html=True)
            else:
                st.caption("No document text or entities available for highlighting.")
            # ----------------------------

    else:
         st.info("Click the 'Generate Summary' button to summarize the document.")