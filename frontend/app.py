import os
import sys
import fitz  # PyMuPDF
import streamlit as st
import time

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.ollama_client import generate_response
from backend.rag_pipeline import split_text_into_chunks, create_vector_store, retrieve_relevant_chunks
from backend.summarizer import summarize_map_reduce  # now imported from backend

# ----------------------------
# UI CONFIGURATION
# ----------------------------
st.set_page_config(page_title="🖊️ PDF Intelligence Chatbot", page_icon="🧠")

# ----------------------------
# Simulate Typing Function
# ----------------------------
def simulate_typing(text, delay=0.02):
    placeholder = st.empty()
    typed = ""
    for char in text:
        typed += char
        placeholder.markdown(typed)
        time.sleep(delay)

# ----------------------------
# Session State Initialization
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = {}

if "active_doc" not in st.session_state:
    st.session_state.active_doc = None

if "current_view" not in st.session_state:
    st.session_state.current_view = "Document Upload"  # ✅ initialize

if "summary_cache" not in st.session_state:
    st.session_state.summary_cache = {}  # ✅ initialize summary cache here

# ----------------------------
# SIDEBAR
# ----------------------------
with st.sidebar:
    st.title("📄 PDF Intelligence")

    # Theme Toggle
    ms = st.session_state
    if "themes" not in ms:
        ms.themes = {
            "current_theme": "light",
            "refreshed": True,
            "light": {
                "theme.base": "light",
                "theme.backgroundColor": "#FFFFFF",
                "theme.primaryColor": "#6200EE",
                "theme.secondaryBackgroundColor": "#F5F5F5",
                "theme.textColor": "#000000",
                "button_face": "🌜"
            },
            "dark": {
                "theme.base": "dark",
                "theme.backgroundColor": "#121212",
                "theme.primaryColor": "#BB86FC",
                "theme.secondaryBackgroundColor": "#1F1B24",
                "theme.textColor": "#E0E0E0",
                "button_face": "🌞"
            },
        }

    def ChangeTheme():
        prev = ms.themes["current_theme"]
        new_theme = "dark" if prev == "light" else "light"
        for k, v in ms.themes[new_theme].items():
            if k.startswith("theme"):
                st._config.set_option(k, v)
        ms.themes["current_theme"] = new_theme
        ms.themes["refreshed"] = False

    btn_face = ms.themes[ms.themes["current_theme"]]["button_face"]
    st.button(btn_face, on_click=ChangeTheme)
    if not ms.themes["refreshed"]:
        ms.themes["refreshed"] = True
        st.rerun()

    # Navigation
    st.session_state.current_view = st.radio(
        "Select Section",
        ("Document Upload", "Extracted Text", "Chat"),
        index=("Document Upload", "Extracted Text", "Chat").index(st.session_state.current_view),
        key="navigation_radio"
    )

    if st.session_state.current_view == "Document Upload":
        uploaded_files = st.file_uploader(
            "Upload one or more PDF, DOCX, or TXT files",
            type=["pdf", "docx", "txt"],
            accept_multiple_files=True
        )
    else:
        uploaded_files = None

    # Document Selector (add All Documents option)
    if st.session_state.uploaded_docs:
        doc_options = list(st.session_state.uploaded_docs.keys()) + ["🔎 All Documents"]
        st.session_state.active_doc = st.selectbox(
            "📂 Select Active Document",
            options=doc_options,
            index=doc_options.index(st.session_state.active_doc)
            if st.session_state.active_doc in doc_options else 0
        )

    # Footer
    st.markdown("""
    ---
    Developed by Tigin Tom — 2025  
    [GitHub](https://github.com/your-profile)
    """, unsafe_allow_html=True)

# ----------------------------
# FILE HANDLING & MAIN LOGIC
# ----------------------------
os.makedirs("documents", exist_ok=True)

if uploaded_files:
    for uploaded_file in uploaded_files:
        file_path = os.path.join("documents", uploaded_file.name)
        with open(file_path, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"✅ File uploaded and saved to `{file_path}`")

        # Extract text
        def extract_text_from_pdf(path):
            doc = fitz.open(path)
            return "".join([page.get_text() for page in doc])

        doc_text = extract_text_from_pdf(file_path)
        st.session_state.uploaded_docs[uploaded_file.name] = {"text": doc_text, "path": file_path}

        with st.spinner(f"Indexing {uploaded_file.name} for retrieval..."):
            chunks = split_text_into_chunks(doc_text)
            create_vector_store(chunks, doc_name=uploaded_file.name)

        if not st.session_state.active_doc:
            st.session_state.active_doc = uploaded_file.name

# ----------------------------
# DISPLAY CONTENT BASED ON VIEW
# ----------------------------
if st.session_state.current_view == "Extracted Text":
    if st.session_state.active_doc and st.session_state.active_doc != "🔎 All Documents":
        doc_name = st.session_state.active_doc
        doc_record = st.session_state.uploaded_docs[doc_name]
        doc_text = doc_record["text"]

        st.subheader(f"📄 Extracted Text from {doc_name}")
        st.write(doc_text[:2000] + "..." if len(doc_text) > 2000 else doc_text)

        # Document Summarization (Map-Reduce)
        st.markdown("#### Summary Options")
        summary_level = st.radio("Choose summary level:", ("Short", "Medium", "Long"), index=0, horizontal=True)
        if st.button("🧠 Generate Summary (Map-Reduce)"):
            if summary_level == "Short":
                cs = 1200
            elif summary_level == "Medium":
                cs = 900
            else:
                cs = 600
            with st.spinner("Summarizing document (map-reduce)..."):
                final_summary = summarize_map_reduce(
                    doc_text,
                    doc_name=doc_name,
                    level=summary_level,
                    model="llama2",
                    chunk_size=cs,
                    chunk_overlap=50
                )
            st.subheader("📌 Summary")
            simulate_typing(final_summary, delay=0.015)

        # Insight Extractor
        if st.button("🔍 Extract Key Insights"):
            with st.spinner("Extracting insights with LLaMA 2..."):
                insight_prompt = (
                    "Extract key insights, main themes, and action points from the following document. "
                    "Return structured bullet points under headings: MAIN THEMES, KEY FINDINGS, ACTIONS.\n\n"
                    f"{doc_text[:20000]}"
                )
                insights = generate_response(insight_prompt, model="llama2")
            st.subheader("💡 Key Insights")
            simulate_typing(insights, delay=0.015)

    elif st.session_state.active_doc == "🔎 All Documents":
        st.info("ℹ️ 'Extracted Text' and per-document insights are only available for a single document. Select a specific document to summarize.")
    else:
        st.info("No document uploaded yet. Please go to 'Document Upload' to upload a file.")

elif st.session_state.current_view == "Chat":
    st.subheader("💬 Chat with Document(s)")

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if st.session_state.active_doc:
        if user_question := st.chat_input("Ask a question about the document(s):"):
            st.session_state.messages.append({"role": "user", "content": user_question})
            with st.chat_message("user"):
                st.markdown(user_question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    if st.session_state.active_doc == "🔎 All Documents":
                        retrieved_docs = retrieve_relevant_chunks(user_question, doc_name="all")
                    else:
                        retrieved_docs = retrieve_relevant_chunks(user_question, doc_name=st.session_state.active_doc)

                    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
                    prompt = f"Answer the question based on the context below:\n\n{context}\n\nQuestion: {user_question}"

                    answer = generate_response(prompt, model="llama2")
                simulate_typing(answer, delay=0.02)
                st.session_state.messages.append({"role": "assistant", "content": answer})
    else:
        st.info("Please upload and select a document to start chatting.")

else:
    if not uploaded_files and not st.session_state.uploaded_docs:
        st.info("👈 Upload a document from the sidebar to begin")

# ----------------------------
# FOOTER STYLING
# ----------------------------
st.markdown("""
<style>
.stApp { padding-bottom: 50px; }
footer { 
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #f0f2f6;
    padding: 10px;
    text-align: center;
    z-index: 999;
}
</style>
""", unsafe_allow_html=True)
