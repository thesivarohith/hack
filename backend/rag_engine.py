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

# In backend/rag_engine.py

def query_knowledge_base(question: str, history: list = []):
    llm = Ollama(model="llama3.2:1b")
    
    # --- PART 1: CONTEXT REWRITING (The Manual Fix) ---
    standalone_question = question
    if history:
        # We confirm history exists, so we rewrite the query
        try:
            # Format history into a string for the AI
            history_text = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in history[-4:]])
            
            rewrite_prompt = f"""
            Rewrite the following question to be a standalone sentence that includes context from the chat history. 
            Do NOT answer the question. Just rewrite it.
            
            Chat History:
            {history_text}
            
            User's Follow-up: {question}
            
            Rewritten Question:"""
            
            # Get the smarter question from the AI
            standalone_question = llm.invoke(rewrite_prompt).strip()
            # Clean up if the AI adds quotes
            standalone_question = standalone_question.replace('"', '').replace("Here is the rewritten question:", "")
            print(f"🔄 LOGIC FIX: Rewrote '{question}' -> '{standalone_question}'")
        except Exception as e:
            print(f"⚠️ Rewrite failed: {e}")

    # --- PART 2: THE "ROUTER" (Search or Chat?) ---
    # If the rewritten question is just a greeting, skip the PDF search
    is_greeting = False
    if len(standalone_question.split()) < 5:
        greetings = ["hi", "hello", "thanks", "good morning", "hey"]
        if any(g in standalone_question.lower() for g in greetings):
            is_greeting = True

    if is_greeting:
        return {
            "answer": "Hello! I am your FocusFlow assistant. I can help you compare topics or explain concepts from your PDFs.",
            "sources": []
        }

    # --- PART 3: SEARCH & ANSWER ---
    # Use the 'standalone_question' (the smart one) for the search
    docs = vector_store.similarity_search(standalone_question, k=3)
    
    # (The rest of your existing answer generation logic goes here...)
    # Ensure you pass 'standalone_question' to your answer chain, not the raw 'question'
    
    # ... [Keep your existing LLM chain call here] ...
    
    # TEMPORARY: If you don't have the chain code handy, use this simple one:
    final_prompt = f"Context: {docs}\n\nQuestion: {standalone_question}\n\nAnswer:"
    answer = llm.invoke(final_prompt)
    
    return {"answer": answer, "sources": [doc.page_content for doc in docs]}