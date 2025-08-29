# rag_pipeline.py

import os

# ----------------------------
# Split Text into Chunks
# ----------------------------
def split_text_into_chunks(text, chunk_size=500, overlap=50):
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.docstore.document import Document

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
    )
    return splitter.split_documents([Document(page_content=text)])


# ----------------------------
# Create Vector Store for One Document
# ----------------------------
def create_vector_store(text_chunks, doc_name, base_path="backend/vector_store"):
    from langchain_community.vectorstores import FAISS
    from langchain.embeddings import HuggingFaceEmbeddings

    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Directory for this document's index
    doc_index_path = os.path.join(base_path, f"faiss_index_{doc_name}")
    os.makedirs(doc_index_path, exist_ok=True)

    # Create FAISS vector store
    vectordb = FAISS.from_documents(text_chunks, embedding_model)
    vectordb.save_local(doc_index_path)
    return vectordb, doc_index_path


# ----------------------------
# Load Vector Store for One Document
# ----------------------------
def load_vector_store(doc_name, base_path="backend/vector_store"):
    from langchain_community.vectorstores import FAISS
    from langchain.embeddings import HuggingFaceEmbeddings

    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    doc_index_path = os.path.join(base_path, f"faiss_index_{doc_name}")

    return FAISS.load_local(
        doc_index_path,
        embeddings=embedding_model,
        allow_dangerous_deserialization=True
    )


# ----------------------------
# Retrieve Chunks for One Document
# ----------------------------
def retrieve_relevant_chunks(query, doc_name, k=3, base_path="backend/vector_store"):
    vectordb = load_vector_store(doc_name, base_path)
    return vectordb.similarity_search(query, k=k)
