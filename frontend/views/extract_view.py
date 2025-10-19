# frontend/views/extract_view.py
import streamlit as st
from backend.summarizer import summarize_map_reduce
from frontend.components.utils import simulate_typing

def render_extract_view(active_doc_obj, user_id):
    if active_doc_obj:
        doc_text = active_doc_obj.full_text
        doc_id = active_doc_obj.id # Get document ID
        doc_name = active_doc_obj.filename # Get document name

        st.subheader(f"📄 Extracted Text from {doc_name}")
        # Display a preview of the text
        st.text_area(
            "Document Content (Preview)",
            doc_text[:3000] + ("..." if len(doc_text) > 3000 else ""), # Show more text
            height=300,
            disabled=True # Make it read-only
        )

        st.markdown("---") # Add a divider
        st.subheader("🧠 Generate Insights") # Changed subheader

        # --- Summary Options ---
        st.markdown("#### Summary Options")
        summary_level = st.radio(
            "Choose summary level:",
            ("Short", "Medium", "Long"), # <-- THIS WAS MISSING
            index=0, # Default to 'Short'
            horizontal=True,
            key="summary_level_radio" # Added a key
        )

        if st.button("✨ Generate Summary (Map-Reduce)", type="primary"): # Added emoji and type
            with st.spinner("Summarizing... Please wait."):
                final_summary, provider = summarize_map_reduce(
                    text=doc_text,
                    doc_id=doc_id,
                    user_id=user_id,
                    doc_name=doc_name,
                    level=summary_level
                )
                st.subheader("📌 Summary")
                # Use a container with border for the summary
                with st.container(border=True):
                    simulate_typing(final_summary) # Typing effect inside container
                st.caption(f"✅ Generated with {provider}")

    else:
        st.info("ℹ️ Select a specific document from the sidebar to view its text and generate insights.")