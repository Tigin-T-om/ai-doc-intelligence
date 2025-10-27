# backend/summarizer.py
import streamlit as st
from backend.llm_client import generate_text
from backend.rag_pipeline import split_text_into_chunks
# --- ADD THESE IMPORTS ---
from backend.db.db_handler import get_session, add_summary
# -------------------------

# --- FUNCTION SIGNATURE UPDATED ---
def summarize_map_reduce(text, doc_id, user_id, doc_name, level="Short", chunk_size=800, chunk_overlap=50):
# --------------------------------
    """
    Map-reduce summarization: splits, summarizes chunks, combines, and saves.
    Returns: (final_summary, provider)
    """
    cache_key = (doc_name, level) # Use doc_name for caching key still
    if cache_key in st.session_state.summary_cache:
        return st.session_state.summary_cache[cache_key]

    docs = split_text_into_chunks(text, chunk_size=chunk_size, overlap=chunk_overlap)
    if not docs:
        return "No content to summarize.", "None"

    # Instructions
    if level == "Short":
        map_instr = "Summarize the following chunk in 2 concise bullet points (very short)."
        reduce_instr = (
            "Combine the bullet points into a final concise summary. "
            "Return ~5 bullet points, ordered by importance."
        )
    elif level == "Medium":
        map_instr = "Summarize the following chunk in 3 short sentences."
        reduce_instr = (
            "Combine the chunk summaries into a cohesive 1-2 paragraph summary. "
            "Keep it factual and focused on main themes."
        )
    else:  # Long
        map_instr = "Summarize the following chunk in 4-6 detailed bullet points focusing on facts and key claims."
        reduce_instr = (
            "Combine the detailed chunk summaries into a thorough 3-5 paragraph summary. "
            "Include main themes, notable details, and any action points."
        )

    # Map step
    chunk_summaries = []
    provider_used = "Unknown" # Default provider
    progress_bar = st.progress(0, text="Summarizing chunks...")
    total = len(docs)
    for i, doc in enumerate(docs, start=1):
        chunk_text = doc.page_content
        prompt = f"{map_instr}\n\nChunk:\n{chunk_text}"
        try:
            chunk_summary, provider_used_chunk = generate_text(prompt)
            # Store the first successful provider found
            if provider_used == "Unknown": provider_used = provider_used_chunk
        except Exception as map_e:
            st.warning(f"Chunk summarization failed: {map_e}. Using truncated text.")
            chunk_summary = chunk_text[:400] + ("..." if len(chunk_text) > 400 else "")
            # Keep provider_used as Unknown or the last successful one

        chunk_summaries.append(chunk_summary)
        progress_bar.progress(int((i / total) * 0.8), text=f"Summarizing chunk {i}/{total}...") # Map step is 80%

    # Reduce step
    progress_bar.progress(85, text="Combining summaries...")
    combined_input = "\n\n---\n\n".join(chunk_summaries)
    reduce_prompt = f"{reduce_instr}\n\nBelow are chunk-level summaries:\n\n{combined_input}"
    try:
        final_summary, provider_used_reduce = generate_text(reduce_prompt)
        # Use the provider from the reduce step if possible
        provider_used = provider_used_reduce
    except Exception as reduce_e:
        st.error(f"Final summary generation failed: {reduce_e}. Combining raw chunk summaries.")
        final_summary = "\n\n".join(chunk_summaries)
        provider_used = "Fallback: Summarized by combining chunk summaries"

    progress_bar.progress(100, text="Finalizing...")

    # --- SAVE TO DATABASE ---
    try:
        with get_session() as db:
            add_summary(
                db=db,
                user_id=user_id,
                document_id=doc_id,
                filename=doc_name, # Use doc_name here
                level=level,
                content=final_summary,
                provider=provider_used
            )
        # st.toast("Summary saved!", icon="✅") # Optional feedback - maybe too noisy
    except Exception as e:
        st.error(f"Failed to save summary to database: {e}")
    # --- END SAVE ---

    progress_bar.empty() # Clear progress bar on completion

    # Cache result
    st.session_state.summary_cache[cache_key] = (final_summary, provider_used)
    return final_summary, provider_used