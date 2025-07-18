import os
import sys
import fitz  # PyMuPDF
import streamlit as st

# Add backend to path for importing generate_response
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.ollama_client import generate_response

# ----------------------------
# UI CONFIGURATION
# ----------------------------
st.set_page_config(page_title="🖊️ PDF Intelligence Chatbot", page_icon="🧠")

# Theme toggle
ms = st.session_state
if "themes" not in ms:
    ms.themes = {
        "current_theme": "light",
        "refreshed": True,
        "light": {
            "theme.base": "dark",
            "theme.backgroundColor": "#FFFFFF",
            "theme.primaryColor": "#6200EE",
            "theme.secondaryBackgroundColor": "#F5F5F5",
            "theme.textColor": "#000000",
            "button_face": "🌜"
        },
        "dark": {
            "theme.base": "light",
            "theme.backgroundColor": "#121212",
            "theme.primaryColor": "#BB86FC",
            "theme.secondaryBackgroundColor": "#1F1B24",
            "theme.textColor": "#E0E0E0",
            "button_face": "🌞"
        },
    }

def ChangeTheme():
    previous_theme = ms.themes["current_theme"]
    tdict = ms.themes["light"] if ms.themes["current_theme"] == "light" else ms.themes["dark"]
    for k, v in tdict.items():
        if k.startswith("theme"): st._config.set_option(k, v)

    ms.themes["refreshed"] = False
    ms.themes["current_theme"] = "dark" if previous_theme == "light" else "light"

btn_face = ms.themes["light"]["button_face"] if ms.themes["current_theme"] == "light" else ms.themes["dark"]["button_face"]
st.button(btn_face, on_click=ChangeTheme)
if ms.themes["refreshed"] == False:
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
# PROCESS UPLOADED FILE
# ----------------------------
os.makedirs("documents", exist_ok=True)
doc_text = ""

if uploaded_file:
    file_path = os.path.join("documents", uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"✅ File uploaded and saved to {file_path}")

    # Extract text
    def extract_text_from_pdf(file_path):
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

    doc_text = extract_text_from_pdf(file_path)

    with st.expander("📄 Show Extracted Text"):
        st.write(doc_text[:2000] + "..." if len(doc_text) > 2000 else doc_text)

    # ----------------------------
    # DOCUMENT SUMMARIZATION
    # ----------------------------
    if st.button("🧠 Generate Summary"):
        with st.spinner("Summarizing with Mistral..."):
            prompt = f"Summarize this document in 5 bullet points:\n\n{doc_text}"
            summary = generate_response(prompt)

        st.subheader("📌 Summary")
        st.markdown(summary)

    # ----------------------------
    # DOCUMENT Q&A
    # ----------------------------
    st.subheader("❓ Ask a Question from Document")
    user_question = st.text_input("Type your question:")

    if user_question:
        with st.spinner("Thinking..."):
            qa_prompt = f"Answer the question based only on this document:\n\n{doc_text}\n\nQuestion: {user_question}"
            answer = generate_response(qa_prompt)

        st.markdown("**Answer:**")
        st.write(answer)
else:
    st.info("👈 Upload a document from the sidebar to begin")
