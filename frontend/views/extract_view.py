# frontend/views/extract_view.py
import streamlit as st
from backend.summarizer import summarize_map_reduce
from frontend.components.utils import simulate_typing

# ----------------------------
# EXTRACTED TEXT + SUMMARY
# ----------------------------
def render_extract_view(active_doc_obj):
    if active_doc_obj:
        doc_text = active_doc_obj.full_text
        st.subheader(f"📄 Extracted Text from {active_doc_obj.filename}")
        st.write(doc_text[:2000] + "..." if len(doc_text) > 2000 else doc_text)

        st.markdown("#### Summary Options")
        summary_level = st.radio("Choose summary level:", ("Short", "Medium", "Long"), index=0, horizontal=True)
        if st.button("🧠 Generate Summary (Map-Reduce)"):
            with st.spinner("Summarizing..."):
                final_summary, provider = summarize_map_reduce(doc_text, active_doc_obj.filename, summary_level)
                st.subheader("📌 Summary")
                simulate_typing(final_summary)
                st.caption(f"✅ Generated with {provider}")
    else:
        st.info("ℹ️ Select a specific document from the sidebar to view its text and generate insights.")
