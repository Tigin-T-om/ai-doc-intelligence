from langchain.llms import Ollama
from langchain.chains.question_answering import load_qa_chain
from langchain.document_loaders import PyPDFLoader

# LangChain still uses Ollama directly (mistral works well for QA)
llm = Ollama(model="mistral")

def load_chain():
    return load_qa_chain(llm, chain_type="stuff")
