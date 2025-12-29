import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.llms import Ollama

CACHE_DIR = "./chroma_db"

def ingest_document(file_path: str):
    """
    Ingests a PDF document into the vector database.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Load PDF
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    # Split text
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)
    
    # Store in ChromaDB
    # Note: Chroma will automatically persist to disk in newer versions when persist_directory is set
    Chroma.from_documents(
        documents=splits,
        embedding=OllamaEmbeddings(model="nomic-embed-text"),
        persist_directory=CACHE_DIR
    )
    print(f"Ingested {len(splits)} chunks from {file_path}")

def query_knowledge_base(question: str):
    """
    Queries the knowledge base and returns an answer with sources.
    """
    # Initialize DB with same embedding function
    db = Chroma(persist_directory=CACHE_DIR, embedding_function=OllamaEmbeddings(model="nomic-embed-text"))
    
    # Retrieve top 3 chunks
    results = db.similarity_search(question, k=3)
    
    if not results:
        return {"answer": "No relevant information found.", "sources": []}

    # Format context
    context_str = "\n\n".join([f"Source: {doc.metadata.get('source', 'Unknown')}, Page: {doc.metadata.get('page', 'Unknown')}\nContent: {doc.page_content}" for doc in results])
    
    # Generate answer using Ollama
    llm = Ollama(model="llama3.2:1b")
    prompt = f"""You are an intelligent study assistant.
    Answer the question using the provided context, but explain it in your own words.
    Make it sound natural and easy to understand, like a teacher explaining to a student.
    
    Context:
    {context_str}
    
    Question: {question}
    """
    
    response = llm.invoke(prompt)
    
    # Format sources for return
    sources = [
        {
            "source": os.path.basename(doc.metadata.get('source', '')),
            "page": doc.metadata.get('page', 0)
        } 
        for doc in results
    ]
    
    return {
        "answer": response,
        "sources": sources
    }
