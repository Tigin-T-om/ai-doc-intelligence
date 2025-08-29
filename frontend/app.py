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
# Session State Initialization
# ----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "uploaded_docs" not in st.session_state:
    st.session_state.uploaded_docs = {}   # {filename: text}

if "active_doc" not in st.session_state:
    st.session_state.active_doc = None

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
        index=0,
        key="navigation_radio"
    )

    if st.session_state.current_view == "Document Upload":
        uploaded_file = st.file_uploader(
            "Upload a PDF, DOCX, or TXT file",
            type=["pdf", "docx", "txt"]
        )
    else:
        uploaded_file = None

    # Document Selector
    if st.session_state.uploaded_docs:
        st.session_state.active_doc = st.selectbox(
            "📂 Select Active Document",
            options=list(st.session_state.uploaded_docs.keys()),
            index=list(st.session_state.uploaded_docs.keys()).index(st.session_state.active_doc)
            if st.session_state.active_doc else 0
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

if uploaded_file:
    file_path = os.path.join("documents", uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ File uploaded and saved to `{file_path}`")

    # Extract text
    def extract_text_from_pdf(path):
        doc = fitz.open(path)
        return "".join([page.get_text() for page in doc])

    doc_text = extract_text_from_pdf(file_path)
    st.session_state.uploaded_docs[uploaded_file.name] = doc_text

    with st.spinner("Indexing document for retrieval..."):
        chunks = split_text_into_chunks(doc_text)
        create_vector_store(chunks, doc_name=uploaded_file.name)

    # Set as active doc if none selected
    if not st.session_state.active_doc:
        st.session_state.active_doc = uploaded_file.name

# ----------------------------
# DISPLAY CONTENT BASED ON VIEW
# ----------------------------
if st.session_state.current_view == "Extracted Text":
    if st.session_state.active_doc:
        doc_name = st.session_state.active_doc
        doc_text = st.session_state.uploaded_docs[doc_name]

        st.subheader(f"📄 Extracted Text from {doc_name}")
        st.write(doc_text[:2000] + "..." if len(doc_text) > 2000 else doc_text)

        # Document Summarization
        if st.button("🧠 Generate Summary"):
            with st.spinner("Summarizing with LLaMA 2..."):
                MAX_CHARS = 2000
                trimmed_text = doc_text[:MAX_CHARS]
                prompt = f"Summarize the following document in 5 bullet points:\n\n{trimmed_text}"

                start = time.time()
                summary = generate_response(prompt, model="llama2")
                end = time.time()

                thinking_time = 5
                time.sleep(max(0, thinking_time - (end - start)))

            st.subheader("📌 Summary")
            simulate_typing(summary, delay=0.015)

    else:
        st.info("No document uploaded yet. Please go to 'Document Upload' to upload a file.")

elif st.session_state.current_view == "Chat":
    st.subheader("💬 Chat with Document")

    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if st.session_state.active_doc:
        doc_name = st.session_state.active_doc
        if user_question := st.chat_input("Ask a question about the document:"):
            st.session_state.messages.append({"role": "user", "content": user_question})
            with st.chat_message("user"):
                st.markdown(user_question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    retrieved_docs = retrieve_relevant_chunks(user_question, doc_name=doc_name)
                    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
                    prompt = f"Answer the question based on the context below:\n\n{context}\n\nQuestion: {user_question}"

                    start = time.time()
                    answer = generate_response(prompt, model="llama2")
                    end = time.time()

                    thinking_time = 5
                    time.sleep(max(0, thinking_time - (end - start)))
                simulate_typing(answer, delay=0.02)
                st.session_state.messages.append({"role": "assistant", "content": answer})
    else:
        st.info("Please upload and select a document to start chatting.")

else:  # Default view when no file uploaded
    if not uploaded_file and not st.session_state.uploaded_docs:
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
