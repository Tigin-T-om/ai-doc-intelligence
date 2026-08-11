# AI Document Intelligence Platform

An AI-powered document analysis and RAG chat application built with
**Python, Streamlit, PostgreSQL, FAISS, and Google Gemini**.

Users can upload PDF documents, generate summaries, analyze document
insights, and ask questions using Retrieval-Augmented Generation (RAG).

## ✨ Features

-   🔐 User registration and login with bcrypt password hashing
-   📄 PDF text extraction using PyMuPDF
-   🧠 RAG-based document chat using FAISS and embeddings
-   🤖 Gemini 2.5 Flash with Ollama/Llama 2 fallback
-   📝 Map-Reduce document summarization
-   📊 Document insights:
    -   TF-IDF keyword extraction
    -   Word clouds
    -   Sentiment analysis
    -   Named Entity Recognition (NER)
    -   PDF statistics
-   💬 Chat history, message search, and transcript export
-   👨‍💼 Admin dashboard with user, document, and API/LLM statistics

## 🔄 How It Works

``` text
PDF Upload
    ↓
Text Extraction
    ↓
Text Chunking
    ↓
Embeddings
    ↓
FAISS Vector Store
    ↓
User Question
    ↓
Relevant Chunks Retrieved
    ↓
Gemini / Ollama
    ↓
AI Answer
```

## 🧠 RAG Pipeline

The application uses:

-   **PyMuPDF** --- PDF text extraction
-   **LangChain** --- text chunking and RAG utilities
-   **all-MiniLM-L6-v2** --- text embeddings
-   **FAISS** --- local vector similarity search
-   **Gemini 2.5 Flash** --- primary LLM
-   **Ollama / Llama 2** --- local fallback LLM

Current RAG configuration:

  Setting               Value
  --------------------- ----------------
  Chunk size            500 characters
  Chunk overlap         50 characters
  Embedding dimension   384
  Retrieved chunks      3

## 📝 Document Summarization

Large documents are processed using a **Map-Reduce** approach:

``` text
Document
   ↓
Split into chunks
   ↓
Summarize each chunk
   ↓
Combine summaries
   ↓
Generate final summary
```

Users can choose **Short, Medium, or Long** summaries.

## 📊 Document Insights

The application analyzes uploaded documents using:

-   **TF-IDF** for important keywords
-   **spaCy** for Named Entity Recognition
-   **NLTK VADER** for sentiment analysis
-   **Plotly** for interactive charts
-   **WordCloud** for keyword visualization

## 🏗️ Architecture

This is a **monolithic Streamlit application**, meaning the UI and
Python application logic run together in one Streamlit application.

``` text
User Browser
     ↓
Streamlit Application
     ├── Frontend Views
     ├── Document Processing
     ├── RAG Pipeline
     ├── NLP / Insights
     └── Authentication
          │
          ├── PostgreSQL
          ├── FAISS
          └── Gemini / Ollama
```

## 🛠️ Tech Stack

  Category              Technologies
  --------------------- ---------------------------
  Language              Python
  UI                    Streamlit
  Database              PostgreSQL, SQLAlchemy
  RAG / Vector Search   LangChain, FAISS
  Embeddings            Sentence Transformers
  LLM                   Google Gemini, Ollama
  NLP                   spaCy, NLTK, scikit-learn
  Visualization         Plotly, Pandas, WordCloud
  Authentication        Passlib / bcrypt
  Tools                 Git, GitHub, Postman

## 📁 Project Structure

``` text
ai_doc_intel_platform/
│
├── backend/
│   ├── db/
│   ├── vector_store/
│   ├── auth_service.py
│   ├── insights_extractor.py
│   ├── llm_client.py
│   ├── ollama_client.py
│   ├── rag_pipeline.py
│   └── summarizer.py
│
├── frontend/
│   ├── components/
│   ├── views/
│   └── app.py
│
├── documents/
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── test_db.py
```

## 📸 Screenshots

Create this folder:

``` text
docs/
└── screenshots/
```

Recommended screenshots for GitHub:

1.  Dashboard
2.  Document Upload
3.  Document Insights
4.  RAG Chat
5.  Document Summary
6.  Admin Dashboard

Then add them like this:

``` markdown
![Dashboard](docs/screenshots/01-dashboard.png)
```

### Dashboard

```{=html}
<!-- Add screenshot here: docs/screenshots/01-dashboard.png -->
```
![Dashboard](docs/screenshots/01-dashboard.png)

### Document Upload

```{=html}
<!-- Add screenshot here: docs/screenshots/02-document-upload.png -->
```
![Document Upload](docs/screenshots/02-document-upload.png)

### Document Insights

```{=html}
<!-- Add screenshot here: docs/screenshots/03-document-insights.png -->
```
![Document Insights](docs/screenshots/03-document-insights.png)

### RAG Chat

```{=html}
<!-- Add screenshot here: docs/screenshots/04-rag-chat.png -->
```
![RAG Chat](docs/screenshots/04-rag-chat.png)

### Document Summary

```{=html}
<!-- Add screenshot here: docs/screenshots/05-summary.png -->
```
![Document Summary](docs/screenshots/05-summary.png)

### Admin Dashboard

```{=html}
<!-- Add screenshot here: docs/screenshots/06-admin-dashboard.png -->
```
![Admin Dashboard](docs/screenshots/06-admin-dashboard.png)

## ⚙️ Installation

### 1. Clone the repository

``` bash
git clone https://github.com/Tigin-T-om/ai_doc_intel_platform.git
cd ai_doc_intel_platform
```

### 2. Create a virtual environment

**Windows:**

``` bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

## 🔐 Environment Setup

Create a `.env` file in the project root:

``` env
DATABASE_URL=postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/pdf_chatbot
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
SECRET_KEY=YOUR_SECRET_KEY
```

**Never commit the real `.env` file to GitHub.**

Recommended:

``` text
.env          → local only
.env.example  → safe template for GitHub
```

## 🗄️ PostgreSQL Setup

Create the database:

``` sql
CREATE DATABASE pdf_chatbot;
```

Then make sure your `.env` contains the correct PostgreSQL connection.

## 🤖 Optional: Ollama

Ollama provides a local fallback when Gemini is unavailable.

Install Ollama and run:

``` bash
ollama pull llama2
```

Check:

``` bash
ollama list
```

## ▶️ Run the Application

From the project root:

``` bash
streamlit run frontend/app.py
```

Then open:

``` text
http://localhost:8501
```

## 👤 How to Use

1.  Register a user account.
2.  Log in.
3.  Upload a PDF.
4.  Open the document dashboard.
5.  Generate a summary.
6.  Explore document insights.
7.  Start a RAG chat.
8.  Ask questions about the document.
9.  View retrieved source fragments.
10. Search or export chat history.

## 🗃️ Database

PostgreSQL stores application data such as:

-   Users
-   Documents
-   Chat sessions
-   Chat messages
-   Summaries
-   API/LLM logs

PDF files and FAISS indexes are stored locally.

## ⚠️ Current Limitations

This project is primarily a portfolio/learning application and has some
known limitations:

-   OCR is not implemented for scanned PDFs.
-   Chat history is stored but previous messages are not sent to the LLM
    as conversation memory.
-   Local FAISS storage is not designed for large-scale production
    deployments.
-   Multi-document retrieval requires stronger user-level isolation
    before production use.
-   There is no separate FastAPI/Flask backend.
-   Ollama fallback requires a locally running Ollama installation.

## 🚀 Future Improvements

-   Add OCR for scanned PDFs
-   Improve multi-user document isolation
-   Add conversational memory
-   Improve RAG grounding and citations
-   Add automated tests
-   Add Docker support
-   Add FastAPI backend for production architecture
-   Add CI/CD with GitHub Actions
-   Improve vector-store scalability

## 💡 What I Learned

Through this project, I worked with:

-   Python application development
-   Streamlit
-   PostgreSQL and SQLAlchemy
-   RAG pipelines
-   Text embeddings and vector search
-   FAISS
-   LLM API integration
-   Map-Reduce summarization
-   NLP with spaCy and NLTK
-   TF-IDF
-   Authentication and session management
-   Git and GitHub

## 👨‍💻 Author

**Tigin Tom**

MCA Graduate \| Python \| Backend Development \| AI/LLM Applications

-   GitHub: https://github.com/Tigin-T-om
-   LinkedIn: https://www.linkedin.com/in/tigintom/

------------------------------------------------------------------------

⭐ If you find this project useful, feel free to explore the code and
give it a star.
