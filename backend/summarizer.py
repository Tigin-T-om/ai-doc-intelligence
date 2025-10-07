import streamlit as st
from backend.llm_client import generate_text
from backend.rag_pipeline import split_text_into_chunks

# ----------------------------
# Map-Reduce Summarizer
# ----------------------------
def summarize_map_reduce(text, doc_name, level="Short", chunk_size=800, chunk_overlap=50):
    """
    Map-reduce summarization:
      - splits text into chunks
      - summarizes each chunk (map)
      - combines summaries (reduce)
    Returns: (final_summary, provider)
    """

    cache_key = (doc_name, level)
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
    provider_used = None
    progress_bar = st.progress(0)
    total = len(docs)
    for i, doc in enumerate(docs, start=1):
        chunk_text = doc.page_content
        prompt = f"{map_instr}\n\nChunk:\n{chunk_text}"
        try:
            chunk_summary, provider_used = generate_text(prompt)
        except Exception:
            chunk_summary, provider_used = (
                chunk_text[:400] + ("..." if len(chunk_text) > 400 else ""),
                "Fallback: Truncated Text"
            )
        chunk_summaries.append(chunk_summary)
        progress_bar.progress(int(i / total * 100))
    progress_bar.empty()

    # Reduce step
    combined_input = "\n\n---\n\n".join(chunk_summaries)
    reduce_prompt = f"{reduce_instr}\n\nBelow are chunk-level summaries:\n\n{combined_input}"
    try:
        final_summary, provider_used = generate_text(reduce_prompt)
    except Exception:
        final_summary, provider_used = "\n\n".join(chunk_summaries), "Fallback: Combined chunks"

    # Cache result
    st.session_state.summary_cache[cache_key] = (final_summary, provider_used)
    return final_summary, provider_used
