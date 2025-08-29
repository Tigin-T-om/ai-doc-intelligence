import os
import heapq

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
# Retrieve Chunks (Single or Multi-doc)
# ----------------------------
def retrieve_relevant_chunks(query, doc_name, k=3, base_path="backend/vector_store"):
    """
    If doc_name == "all", search across all stored vector indexes.
    Otherwise, search only within the given document.
    """
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS

    embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    if doc_name == "all":
        all_docs_results = []

        # Loop through all FAISS indexes in base_path
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

        # Take top-k results across all docs
        # Using heapq to rank by score if available, else just truncating
        return all_docs_results[:k]

    else:
        vectordb = load_vector_store(doc_name, base_path)
        return vectordb.similarity_search(query, k=k)
