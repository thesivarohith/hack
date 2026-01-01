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

def ingest_url(url: str):
    """
    Ingests content from a URL (YouTube or Web).
    """
    from langchain_community.document_loaders import YoutubeLoader, WebBaseLoader
    
    docs = []
    try:
        if "youtube.com" in url or "youtu.be" in url:
            print(f"Loading YouTube Video: {url}")
            try:
                # Try with metadata first (requires pytube, often flaky)
                loader = YoutubeLoader.from_youtube_url(url, add_video_info=True)
                docs = loader.load()
            except Exception as e:
                print(f"⚠️ Metadata fetch failed ({e}). Retrying with transcript only...")
                # Fallback: Transcript only (no title/author)
                loader = YoutubeLoader.from_youtube_url(url, add_video_info=False)
                docs = loader.load()
        else:
            print(f"Loading Website: {url}")
            loader = WebBaseLoader(url)
            docs = loader.load()
            
        # Generic processing
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = splitter.split_documents(docs)
        
        if not splits:
            raise ValueError("No content found to ingest")
            
        # Store in ChromaDB
        Chroma.from_documents(
            documents=splits,
            embedding=OllamaEmbeddings(model="nomic-embed-text"),
            persist_directory=CACHE_DIR
        )
        
        title = docs[0].metadata.get("title", url) if docs else url
        print(f"Ingested {len(splits)} chunks from {title}")
        return title
        
    except Exception as e:
        print(f"Error ingesting URL: {e}")
        raise e

def delete_document(source_path: str):
    """
    Removes a document from the vector database by its source path.
    """
    vector_store = Chroma(
        persist_directory=CACHE_DIR,
        embedding_function=OllamaEmbeddings(model="nomic-embed-text")
    )
    
    # Delete based on metadata 'source'
    try:
        # Accessing the underlying chroma collection to delete by metadata
        vector_store._collection.delete(where={"source": source_path})
        print(f"Deleted vectors for source: {source_path}")
    except Exception as e:
        print(f"Error deleting from ChromaDB: {e}")

# In backend/rag_engine.py

def query_knowledge_base(question: str, history: list = []):
    llm = Ollama(model="llama3.2:1b")
    
    vector_store = Chroma(
        persist_directory=CACHE_DIR,
        embedding_function=OllamaEmbeddings(model="nomic-embed-text")
    )
    
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

    # --- PART 3: SEARCH & ANSWER (Tutor Mode) ---
    
    # 1. Search the PDF (Increased k=5 and added debug)
    # 1. Search the PDF (Increased k=6 and added debug)
    docs = vector_store.similarity_search(standalone_question, k=6)
    print(f"🔎 Found {len(docs)} relevant chunks")
    
    # Construct context with explicit Source Labels
    context_parts = []
    for doc in docs:
        # Get a clean source name (e.g., "DSA.pdf" or "Video Title")
        src = doc.metadata.get("title") or doc.metadata.get("source", "Unknown").split("/")[-1]
        context_parts.append(f"SOURCE: {src}\nCONTENT: {doc.page_content}")
    
    context_text = "\n\n---\n\n".join(context_parts)
    
    # 2. The "Tutor Persona" Prompt
    final_prompt = f"""
    You are FocusFlow, a friendly and expert AI Tutor.
    Your goal is to explain concepts from the provided PDF content clearly and simply.

    GUIDELINES:
    - Tone: Encouraging, professional, and educational.
    - Format: Use **Bold** for key terms and Bullet points for lists.
    - Strategy: Don't just copy the text. Read the context, understand it, and explain it to the student.
    - If the context lists problems (like DSA), summarize the types of problems found.
    - Source Check: The context now includes 'SOURCE:' labels. If the user asks about a specific file (like 'the PDF' or 'the Video'), ONLY use information from that specific source.

    CONTEXT FROM PDF:
    {context_text}

    STUDENT'S QUESTION:
    {standalone_question}

    YOUR LESSON:
    """
    
    # 3. Generate Answer
    answer = llm.invoke(final_prompt)
    
    # 4. Smart Source Formatting
    sources_list = []
    for doc in docs:
        # Check if it's a Video (YoutubeLoader adds 'title')
        if "title" in doc.metadata:
            source_label = f"📺 {doc.metadata['title']}"
            loc_label = "Transcript"
        else:
            # Fallback for PDFs
            source_label = doc.metadata.get("source", "Unknown").split("/")[-1]
            loc_label = f"Page {doc.metadata.get('page', 0) + 1}"

        sources_list.append({
            "source": source_label,
            "location": loc_label
        })

    return {
        "answer": answer,
        "sources": sources_list
    }

def generate_study_plan(user_request: str) -> dict:
    print(f"🚀 STARTING PLAN GENERATION for: {user_request}")
    import json
    import time
    
    # 1. Setup Retrieval & LLM
    vector_store = Chroma(
        persist_directory=CACHE_DIR,
        embedding_function=OllamaEmbeddings(model="nomic-embed-text")
    )
    llm = Ollama(model="llama3.2:1b")

    # --- 1. THE BACKUP PLAN (Guaranteed to work) ---
    backup_plan = {
        "days": [
            {"id": 1, "day": 1, "topic": "Fundamentals of the Subject", "details": "Core definitions and basic laws.", "locked": False, "quiz_passed": False},
            {"id": 2, "day": 2, "topic": "Advanced Theories", "details": "Applying the laws to complex systems.", "locked": True, "quiz_passed": False},
            {"id": 3, "day": 3, "topic": "Practical Applications", "details": "Real-world case studies and problems.", "locked": True, "quiz_passed": False}
        ]
    }

    # --- 2. TRY THE AI ---
    try:
        # Limit context to be very fast
        docs = vector_store.similarity_search("Syllabus topics", k=2)
        if not docs:
            context_text = "General syllabus topics."
        else:
            context_text = "\n".join([d.page_content[:200] for d in docs]) 
        
        prompt = f"""
        Context: {context_text}
        Task: Create a 3-day study plan (JSON).
        Format: {{"days": [{{"id": 1, "day": 1, "topic": "...", "details": "...", "locked": false}}]}}
        Output JSON only.
        """
        
        print("🤖 Asking AI (with 15s timeout expectation)...")
        # In a real production app we would wrap this in a thread timeout, 
        # but for now we rely on the try/except block catching format errors.
        raw_output = llm.invoke(prompt)
        print("✅ AI Responded.")
        
        # Clean & Parse
        clean_json = raw_output.replace("```json", "").replace("```", "").strip()
        plan = json.loads(clean_json)
        
        # Validate Keys (The "Sanitizer")
        for i, task in enumerate(plan.get("days", [])):
            if "id" not in task: task["id"] = i + 1
            if "topic" not in task: task["topic"] = f"Day {i+1} Topic"
            task["quiz_passed"] = False
            
        return plan

    except Exception as e:
        print(f"⚠️ AI FAILED ({e}). SWITCHING TO BACKUP PLAN.")
        return backup_plan