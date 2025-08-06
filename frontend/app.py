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

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

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
        index=0, # Default to Document Upload
        key="navigation_radio"
    )

    if st.session_state.current_view == "Document Upload":
        uploaded_file = st.file_uploader("Upload a PDF, DOCX, or TXT file", type=["pdf", "docx", "txt"])
    else:
        uploaded_file = None # Ensure uploaded_file is None if not in Document Upload view

    # Footer in sidebar
    st.markdown("""
    ---
    Developed by Tigin Tom — 2025  
    [GitHub](https://github.com/your-profile)
    """, unsafe_allow_html=True)

# ----------------------------
# FILE HANDLING & MAIN LOGIC
# ----------------------------
os.makedirs("documents", exist_ok=True)

# Initialize session state for doc_text and uploaded_file_name if not already present
if "doc_text" not in st.session_state:
    st.session_state.doc_text = ""
if "uploaded_file_name" not in st.session_state:
    st.session_state.uploaded_file_name = ""

# Handle file upload
if uploaded_file:
    file_path = os.path.join("documents", uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ File uploaded and saved to `{file_path}`")
    st.session_state.uploaded_file_name = uploaded_file.name # Store file name
    
    # Extract text from PDF
    def extract_text_from_pdf(path):
        doc = fitz.open(path)
        return "".join([page.get_text() for page in doc])

    doc_text = extract_text_from_pdf(file_path)
    st.session_state.doc_text = doc_text # Store doc_text in session state

    with st.spinner("Indexing document for retrieval..."):
        chunks = split_text_into_chunks(doc_text)
        create_vector_store(chunks)

# Display content based on navigation selection
if st.session_state.current_view == "Extracted Text":
    if st.session_state.doc_text:
        st.subheader(f"📄 Extracted Text from {st.session_state.uploaded_file_name}")
        st.write(st.session_state.doc_text[:2000] + "..." if len(st.session_state.doc_text) > 2000 else st.session_state.doc_text)
    else:
        st.info("No document uploaded yet. Please go to 'Document Upload' to upload a file.")

    # ----------------------------
    # DOCUMENT SUMMARIZATION
    # ----------------------------
    if st.button("🧠 Generate Summary"):
        if st.session_state.doc_text:
            with st.spinner("Summarizing with LLaMA 2..."):
                MAX_CHARS = 2000
                trimmed_text = st.session_state.doc_text[:MAX_CHARS]
                prompt = f"Summarize the following document in 5 bullet points:\n\n{trimmed_text}"

                start = time.time()
                summary = generate_response(prompt, model="llama2")
                end = time.time()

                # Minimum spinner time
                thinking_time = 5
                time.sleep(max(0, thinking_time - (end - start)))

            st.subheader("📌 Summary")
            simulate_typing(summary, delay=0.015)
        else:
            st.warning("Please upload a document first to generate a summary.")

elif st.session_state.current_view == "Chat":
    st.subheader("💬 Chat with Document")
    
    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if st.session_state.doc_text:
        if user_question := st.chat_input("Ask a question about the document:"):
            st.session_state.messages.append({"role": "user", "content": user_question})
            with st.chat_message("user"):
                st.markdown(user_question)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    retrieved_docs = retrieve_relevant_chunks(user_question)
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
        st.info("Please upload a document in the 'Document Upload' section to start chatting.")

else: # Default view for "Document Upload" when no file is uploaded yet
    if not uploaded_file and not st.session_state.doc_text:
        st.info("👈 Upload a document from the sidebar to begin")

# Custom CSS for footer at the bottom
st.markdown("""
<style>
/* Adjust the main content area to allow space for the footer */
.stApp { padding-bottom: 50px; } /* Add padding at the bottom equal to footer height */

/* Position the footer at the bottom */
footer { 
    position: fixed;
    bottom: 0;
    left: 0;
    width: 100%;
    background-color: #f0f2f6; /* Adjust as needed */
    padding: 10px;
    text-align: center;
    z-index: 999; /* Ensure footer is above other content */
}
</style>
""", unsafe_allow_html=True)
