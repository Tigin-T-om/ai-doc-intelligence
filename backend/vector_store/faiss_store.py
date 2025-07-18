from langchain.vectorstores import FAISS
from langchain.embeddings import OllamaEmbeddings

def get_vectorstore(documents):
    embedding = OllamaEmbeddings()
    return FAISS.from_documents(documents, embedding)
