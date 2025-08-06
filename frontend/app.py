import os
import sys
import fitz  # PyMuPDF
import streamlit as st
import time

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.ollama_client import generate_response
from backend.rag_pipeline import split_text_into_chunks, create_vector_store, retrieve_relevant_chunks

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
# Theme Toggle Setup
# ----------------------------
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

# ----------------------------
# SIDEBAR
# ----------------------------
with st.sidebar:
    st.title("📄 PDF Intelligence")
    uploaded_file = st.file_uploader("Upload a PDF, DOCX, or TXT file", type=["pdf", "docx", "txt"])
    st.markdown("""
    Developed by Tigin Tom — 2025  
    [GitHub](https://github.com/your-profile)
    """, unsafe_allow_html=True)

# ----------------------------
# FILE HANDLING & MAIN LOGIC
# ----------------------------
os.makedirs("documents", exist_ok=True)
doc_text = ""

if uploaded_file:
    file_path = os.path.join("documents", uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ File uploaded and saved to `{file_path}`")

    # Extract text from PDF
    def extract_text_from_pdf(path):
        doc = fitz.open(path)
        return "".join([page.get_text() for page in doc])

    doc_text = extract_text_from_pdf(file_path)

    with st.expander("📄 Show Extracted Text"):
        st.write(doc_text[:2000] + "..." if len(doc_text) > 2000 else doc_text)

    # ----------------------------
    # DOCUMENT CHUNKING & FAISS INDEX
    # ----------------------------
    with st.spinner("Indexing document for retrieval..."):
        chunks = split_text_into_chunks(doc_text)
        create_vector_store(chunks)

    # ----------------------------
    # DOCUMENT SUMMARIZATION
    # ----------------------------
    if st.button("🧠 Generate Summary"):
        with st.spinner("Summarizing with LLaMA 2..."):
            MAX_CHARS = 2000
            trimmed_text = doc_text[:MAX_CHARS]
            prompt = f"Summarize the following document in 5 bullet points:\n\n{trimmed_text}"

            start = time.time()
            summary = generate_response(prompt, model="llama2")
            end = time.time()

            # Minimum spinner time
            thinking_time = 5
            time.sleep(max(0, thinking_time - (end - start)))

        st.subheader("📌 Summary")
        simulate_typing(summary, delay=0.015)

    # ----------------------------
    # DOCUMENT Q&A (RAG-Based)
    # ----------------------------
    st.subheader("❓ Ask a Question from Document")
    user_question = st.text_input("Type your question:")

    if user_question:
        with st.spinner("Thinking..."):
            retrieved_docs = retrieve_relevant_chunks(user_question)
            context = "\n\n".join([doc.page_content for doc in retrieved_docs])
            prompt = f"Answer the question based on the context below:\n\n{context}\n\nQuestion: {user_question}"

            start = time.time()
            answer = generate_response(prompt, model="llama2")
            end = time.time()

            # Simulate thinking
            thinking_time = 5
            time.sleep(max(0, thinking_time - (end - start)))

        st.markdown("**Answer:**")
        simulate_typing(answer, delay=0.02)

else:
    st.info("👈 Upload a document from the sidebar to begin")
