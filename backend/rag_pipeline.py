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
# Create Vector Store with FAISS
# ----------------------------
def create_vector_store(text_chunks, index_path="backend/vector_store"):
    from langchain_community.vectorstores import FAISS
    from langchain.embeddings import HuggingFaceEmbeddings

    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # Ensure the vector store directory exists
    os.makedirs(index_path, exist_ok=True)

    # Create FAISS vector store and save under "faiss_index"
    vectordb = FAISS.from_documents(text_chunks, embedding_model)
    vectordb.save_local(os.path.join(index_path, "faiss_index"))
    return vectordb


# ----------------------------
# Load Existing Vector Store
# ----------------------------
def load_vector_store(index_path="backend/vector_store"):
    from langchain_community.vectorstores import FAISS
    from langchain.embeddings import HuggingFaceEmbeddings

    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # ✅ THIS is what fixes the error
    return FAISS.load_local(
        os.path.join(index_path, "faiss_index"),
        embeddings=embedding_model,
        allow_dangerous_deserialization=True  # <-- this line is 100% required
    )


# ----------------------------
# Perform Similarity Search
# ----------------------------
def retrieve_relevant_chunks(query, k=3, index_path="backend/vector_store"):
    vectordb = load_vector_store(index_path)
    return vectordb.similarity_search(query, k=k)
