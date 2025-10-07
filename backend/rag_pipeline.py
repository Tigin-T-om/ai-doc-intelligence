# backend/rag_pipeline.py
import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

# ----------------------------
# Shared embedding model
# ----------------------------
embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


# ----------------------------
# Split Text into Chunks
# ----------------------------
def split_text_into_chunks(text, chunk_size=500, overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
    )
    return splitter.split_documents([Document(page_content=text)])


# ----------------------------
# Create Vector Store for One Document
# ----------------------------
def create_vector_store(chunks, doc_name, base_path="backend/vector_store"):
    """
    Create and persist a FAISS vector store for a given document.
    """
    doc_index_path = os.path.join(base_path, f"faiss_index_{doc_name}")
    os.makedirs(doc_index_path, exist_ok=True)

    texts, metadatas = [], []
    for i, chunk in enumerate(chunks, start=1):
        texts.append(chunk.page_content)
        metadatas.append({"chunk": i})

    vectordb = FAISS.from_texts(texts, embedding_model, metadatas=metadatas)
    vectordb.save_local(doc_index_path)
    return vectordb, doc_index_path


# ----------------------------
# Load Vector Store
# ----------------------------
def load_vector_store(doc_name, base_path="backend/vector_store"):
    doc_index_path = os.path.join(base_path, f"faiss_index_{doc_name}")
    return FAISS.load_local(
        doc_index_path,
        embeddings=embedding_model,
        allow_dangerous_deserialization=True
    )


# ----------------------------
# Retrieve Chunks
# ----------------------------
def retrieve_relevant_chunks(query, doc_name, k=3, base_path="backend/vector_store"):
    if doc_name == "all":
        all_docs_results = []
        for folder in os.listdir(base_path):
            if folder.startswith("faiss_index_"):
                try:
                    vectordb = FAISS.load_local(
                        os.path.join(base_path, folder),
                        embeddings=embedding_model,
                        allow_dangerous_deserialization=True
                    )
                    results = vectordb.similarity_search(query, k=k)
                    all_docs_results.extend(results)
                except Exception as e:
                    print(f"⚠️ Could not load index {folder}: {e}")
        return all_docs_results[:k]
    else:
        vectordb = load_vector_store(doc_name, base_path)
        return vectordb.similarity_search(query, k=k)
