# FocusFlow Architecture - Explained Like You're in First Year

**Imagine this:** You have a pile of PDF textbooks. You want to:
1. Upload them to an app
2. Have the app create a study plan automatically
3. Ask questions and get answers with exact page citations
4. Take auto-generated quizzes
5. Track your progress

**That's FocusFlow!**

---

## 🎯 The Big Picture (What We're Building)

```
┌──────────────────────────────────────────────────────────────┐
│                    WHAT THE USER SEES                        │
│                                                              │
│  📱 Web Interface (Streamlit)                               │
│  ├─ Upload PDFs                                             │
│  ├─ Generate study plan                                     │
│  ├─ Ask questions                                           │
│  ├─ Take quizzes                                            │
│  └─ View progress                                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
                           ↕️
┌──────────────────────────────────────────────────────────────┐
│                    WHAT HAPPENS BEHIND                       │
│                                                              │
│  🤖 AI Brain (LLM) - Understands and generates text         │
│  🔍 Search Engine (ChromaDB) - Finds relevant content       │
│  💾 Database (Supabase/SQLite) - Saves your progress        │
│  🔌 API Server (FastAPI) - Connects everything              │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 📚 Chapter 1: The Technology Stack (What We Use & Why)

### **1.1 Frontend (What You See)**

#### **Streamlit** 🎨
- **What it is:** A Python library that turns scripts into web apps
- **Why we use it:** 
  - No HTML/CSS/JavaScript knowledge needed
  - Write everything in Python
  - Built-in widgets (buttons, sliders, file uploaders)
  - Perfect for AI/ML apps
  
- **Alternative we could use:** React.js
  - **Why we didn't:** Too complicated - requires learning JavaScript, webpack, npm, etc.
  - **Streamlit advantage:** 5 lines of Python = a full interface

**Example:**
```python
# Streamlit - Easy!
import streamlit as st
uploaded_file = st.file_uploader("Upload PDF")
if st.button("Generate Plan"):
    st.write("Plan created!")

# React - Complex! (Need JavaScript, JSX, state management)
// Would need 50+ lines of code
```

---

### **1.2 Backend (The Brain)**

#### **FastAPI** 🚀
- **What it is:** A modern Python web framework for building APIs
- **Why we use it:**
  - Super fast (async support)
  - Auto-generates API documentation
  - Type checking built-in
  - Easy to learn

- **Alternative we could use:** Flask
  - **Why FastAPI is better:** Automatic validation, async support, faster

**What's an API?** Think of it like a waiter in a restaurant:
- Frontend (you) asks for something → API (waiter) → Backend (kitchen) makes it → API brings it back

**Example:**
```python
@app.post("/upload")  # This is an "endpoint" - a URL the frontend can call
def upload_pdf(file: UploadFile):
    # Process PDF
    return {"status": "success"}
```

When frontend calls `http://localhost:8000/upload`, this function runs!

---

### **1.3 The AI Brain (LLM - Large Language Model)**

We use **TWO different AI models** depending on where you run the app:

#### **For Local (Your Computer): Ollama + llama3.2**
- **What it is:** Ollama runs AI models on your computer (offline)
- **Model used:** llama3.2:1b (1 billion parameters - "small" but smart)
- **Why we use it:**
  - ✅ Completely private (no data sent to internet)
  - ✅ Free forever
  - ✅ Works offline
  - ❌ Requires powerful computer (8GB+ RAM)

#### **For Cloud (HuggingFace Spaces): HuggingFace API + Llama-3-8B**
- **What it is:** HuggingFace runs the AI on their servers
- **Model used:** Meta-Llama-3-8B-Instruct (8 billion parameters - smarter)
- **Why we use it:**
  - ✅ No setup needed
  - ✅ Faster (runs on powerful cloud servers)
  - ✅ Bigger, smarter model
  - ❌ Requires internet
  - ❌ Data goes to cloud

**What does the AI do?**
1. **Generate study plans** from your PDFs
2. **Answer questions** based on PDF content
3. **Create quizzes** with multiple-choice questions

**Example conversation with AI:**
```
User PDF: "Photosynthesis converts light into energy..."
User Question: "What is photosynthesis?"
AI Answer: "Photosynthesis is the process where plants convert 
           light into chemical energy. [Source: biology.pdf, page 42]"
```

---

### **1.4 The Memory System (Databases)**

We use **MULTIPLE** databases for different types of data:

#### **ChromaDB** 🔍 (Vector Database)
- **What it stores:** PDF text chunks + their "meaning" (embeddings)
- **Why we need it:** For semantic search

**What's semantic search?**
- **Keyword search:** Looks for exact words
  - Search "car" → finds "car" but NOT "vehicle" or "automobile"
- **Semantic search:** Understands meaning
  - Search "car" → finds "car", "vehicle", "automobile", "sedan"

**How it works:**
```
1. Upload PDF: "The mitochondria is the powerhouse of the cell"
                    ↓
2. Convert to "embedding" (a bunch of numbers representing meaning)
   [0.234, -0.456, 0.123, 0.789, ...] (384 numbers!)
                    ↓
3. Store in ChromaDB with original text
                    ↓
4. User asks: "What produces energy in cells?"
                    ↓
5. Convert question to embedding
   [0.245, -0.401, 0.134, 0.756, ...]
                    ↓
6. ChromaDB finds chunks with SIMILAR numbers (similar meaning)
                    ↓
7. Returns: "The mitochondria is the powerhouse..." ✅
```

**Why ChromaDB instead of regular database?**
- Regular database: Can only search exact text
- ChromaDB: Searches by **meaning** (perfect for AI!)

---

#### **Supabase PostgreSQL** 💾 (Main Database - Cloud)
- **What it stores:** Your study plans, quiz scores, progress
- **Why we use it:**
  - ✅ Free cloud database (no setup)
  - ✅ Data persists forever
  - ✅ Multi-user support
  - ✅ Real-time updates

**Alternative:** MongoDB, MySQL, Firebase
- **Why Supabase:** Easier than AWS, more features than SQLite, free tier generous

**Example data structure:**
```json
{
  "student_id": "student_abc123",
  "profile_data": {
    "study_plan": {
      "topics": [
        {"day": 1, "title": "Intro to Python", "status": "completed"},
        {"day": 2, "title": "Functions", "status": "unlocked"}
      ]
    },
    "quiz_history": [
      {"topic": "Intro to Python", "score": 8, "total": 10}
    ],
    "mastery_tracker": {
      "Python": 80.0,
      "Math": 65.0
    }
  }
}
```

---

#### **SQLite** 📁 (Local Database)
- **What it stores:** Sources (uploaded PDFs), schedules
- **Why we use it:** 
  - ✅ No setup (just a file)
  - ✅ Built into Python
  - ✅ Perfect for small data

**Alternative:** PostgreSQL, MySQL
- **Why SQLite:** Simpler for local usage, zero configuration

---

### **1.5 The Connector (LangChain)**

#### **LangChain** 🔗
- **What it is:** A toolkit for building AI apps
- **Why we use it:**
  - Connects AI models with data sources
  - Built-in RAG (Retrieval-Augmented Generation) patterns
  - Handles chunking, embeddings, prompts

**Without LangChain (hard):**
```python
# You'd have to write 200+ lines:
1. Load PDF manually
2. Split into chunks manually
3. Generate embeddings manually
4. Store in vector DB manually
5. Query and rank results manually
6. Format prompt manually
7. Call LLM manually
8. Parse response manually
```

**With LangChain (easy):**
```python
from langchain.document_loaders import PyPDFLoader
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA

# Just 5 lines!
loader = PyPDFLoader("textbook.pdf")
docs = loader.load_and_split()
vectorstore = Chroma.from_documents(docs, embeddings)
qa_chain = RetrievalQA.from_chain_type(llm, vectorstore)
answer = qa_chain.run("What is photosynthesis?")
```

---

## 🏗️ Chapter 2: System Architecture (How It All Connects)

### **2.1 The Full Stack**

```
┌─────────────────────────────────────────────────────────────┐
│                    USER'S BROWSER                           │
│                                                             │
│  ┌──────────────────────────────────────────────────┐     │
│  │         Streamlit Frontend (Port 8501)           │     │
│  │  - Material Design UI                            │     │
│  │  - Calendar widget                               │     │
│  │  - Chat interface                                │     │
│  │  - Quiz display                                  │     │
│  └──────────────┬───────────────────────────────────┘     │
│                 │ HTTP Requests (API calls)                │
└─────────────────┼───────────────────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI Backend (Port 8000)                 │
│                                                             │
│  ┌───────────────────┐  ┌──────────────────────────────┐  │
│  │   API Endpoints   │  │    Student Profile Manager   │  │
│  │  /upload          │  │  - load_profile()            │  │
│  │  /query           │  │  - save_profile()            │  │
│  │  /generate_plan   │  │  - update_progress()         │  │
│  │  /generate_quiz   │  └──────────────────────────────┘  │
│  └───────────────────┘                                     │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              RAG Engine (rag_engine.py)              │  │
│  │  - ingest_document() - Process PDFs                 │  │
│  │  - query_knowledge_base() - Answer questions        │  │
│  │  - generate_lesson() - Create lessons               │  │
│  │  - generate_quiz() - Make quizzes                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────┬────────────────┬────────────────┬─────────────────────┘
      │                │                │
      ↓                ↓                ↓
┌──────────┐    ┌─────────────┐   ┌────────────────┐
│ ChromaDB │    │ LLM (AI)    │   │   Supabase     │
│          │    │             │   │  PostgreSQL    │
│ Store    │    │ Ollama or   │   │                │
│ PDF      │    │ HuggingFace │   │ Store study    │
│ chunks   │    │             │   │ plans/progress │
│          │    │ Generate    │   │                │
│ Search   │    │ answers     │   │ Multi-user     │
│ similar  │    │             │   │ support        │
│ content  │    │             │   │                │
└──────────┘    └─────────────┘   └────────────────┘
```

---

### **2.2 Data Flow (What Happens When You Do Something)**

#### **🔄 Flow 1: Uploading a PDF**

```
1. USER: Clicks "Upload PDF" button in Streamlit
              ↓
2. FRONTEND: File sent to FastAPI backend
   POST http://localhost:8000/upload
              ↓
3. BACKEND: Receives PDF file
   - Saves temporarily to /tmp/
              ↓
4. RAG ENGINE: Processes PDF
   - PyPDFLoader extracts text from PDF
   - RecursiveCharacterTextSplitter splits into chunks
     (1000 characters each, 200 overlap)
   
   Example:
   PDF: "Chapter 1: Python is a programming language..."
        (5000 characters)
                ↓
   Chunks: 
   1. "Chapter 1: Python is a programming..."
   2. "language. Python was created by..."
   3. "by Guido van Rossum. It is used..."
   4. "used for web development, AI..."
   5. "AI, data science and more..."
              ↓
5. EMBEDDINGS: Convert each chunk to numbers
   Chunk 1 → [0.234, -0.456, 0.789, ...] (384 numbers)
   Chunk 2 → [0.123, -0.234, 0.567, ...]
   ...
              ↓
6. CHROMADB: Store chunks + embeddings
   {
     text: "Chapter 1: Python is...",
     embedding: [0.234, -0.456, ...],
     metadata: {source: "python.pdf", page: 1}
   }
              ↓
7. SQLITE: Save source info
   INSERT INTO sources (filename, type, is_active)
   VALUES ('python.pdf', 'pdf', true)
              ↓
8. RESPONSE: Tell frontend "Success!"
              ↓
9. FRONTEND: Shows PDF in "Sources" list ✅
```

---

#### **🔄 Flow 2: Asking a Question**

```
1. USER: Types "What is Python?" in chat
              ↓
2. FRONTEND: Sends to backend
   POST /query {"question": "What is Python?"}
              ↓
3. BACKEND: RAG Engine processes
              ↓
4. EMBEDDINGS: Convert question to numbers
   "What is Python?" → [0.245, -0.401, 0.756, ...]
              ↓
5. CHROMADB: Similarity search
   - Compares question embedding with all stored embeddings
   - Finds top 4 most similar chunks
   
   Math (simplified):
   Question: [0.245, -0.401, 0.756]
   Chunk 1:  [0.234, -0.456, 0.789]  → Similarity: 0.95 ⭐
   Chunk 2:  [0.123, -0.234, 0.567]  → Similarity: 0.87
   Chunk 3:  [0.891, -0.123, 0.234]  → Similarity: 0.45
   ...
   
   Returns top 4: Chunk 1, 2, 8, 15
              ↓
6. CONTEXT: Build context from chunks
   Context = """
   Chunk 1: Python is a programming language...
   Chunk 2: Python was created by Guido van Rossum...
   Chunk 8: Python is used for web development...
   Chunk 15: Python syntax is simple and readable...
   """
              ↓
7. PROMPT: Create prompt for AI
   """
   Context from documents:
   {context}
   
   Question: What is Python?
   
   Answer based on the context above.
   Include citations.
   """
              ↓
8. LLM: Generate answer
   Ollama/HuggingFace processes prompt
              ↓
9. RESPONSE: AI returns answer
   "Python is a programming language created by Guido 
   van Rossum. It's used for web development, AI, and 
   data science. Python syntax is simple and readable.
   [Source: python.pdf, page 1]"
              ↓
10. FRONTEND: Display answer with citations ✅
```

---

#### **🔄 Flow 3: Generating a Study Plan**

```
1. USER: Types "Make a 5-day plan" in calendar
              ↓
2. FRONTEND: Sends request
   POST /generate_plan {"request_text": "Make a 5-day plan"}
              ↓
3. BACKEND: RAG Engine works
              ↓
4. CHROMADB: Get ALL document chunks
   - Queries vector DB for broad context
   - Gets 50+ chunks
              ↓
5. SUMMARIZE: Build content summary
   Content = "Documents contain: Python basics, functions,
              loops, data structures, OOP..."
              ↓
6. PROMPT: Ask AI to create plan
   """
   Content available: {content summary}
   
   Create a 5-day study plan in JSON format:
   [
     {"day": 1, "topic": "...", "subject": "..."},
     {"day": 2, "topic": "...", "subject": "..."},
     ...
   ]
   """
              ↓
7. LLM: Generate plan
   Returns JSON:
   [
     {"day": 1, "topic": "Python Basics", "subject": "Python"},
     {"day": 2, "topic": "Functions", "subject": "Python"},
     {"day": 3, "topic": "Loops", "subject": "Python"},
     {"day": 4, "topic": "Data Structures", "subject": "Python"},
     {"day": 5, "topic": "OOP Concepts", "subject": "Python"}
   ]
              ↓
8. VALIDATE: Check and fix plan
   - Ensure all days present
   - Set day 1 topics as "unlocked"
   - Other days as "locked"
   - Add IDs, status fields
              ↓
9. SAVE: Store in database
   Supabase (cloud) or JSON file (local)
   
   profile_data.study_plan = {
     plan_id: "plan_20260110_123456",
     topics: [...]
   }
              ↓
10. FRONTEND: Update calendar + show plan ✅
```

---

#### **🔄 Flow 4: Taking a Quiz**

```
1. USER: Clicks "Start Learning" → Views lesson → Clicks "Take Quiz"
              ↓
2. FRONTEND: Request quiz
   POST /generate_quiz {"topic": "Python Basics"}
              ↓
3. CHROMADB: Search for topic content
   - Finds 6 most relevant chunks about "Python Basics"
              ↓
4. PROMPT: Ask AI for quiz questions
   """
   Context: {6 chunks about Python Basics}
   
   Create 3 multiple-choice questions in JSON:
   [
     {
       "question": "What is Python?",
       "options": ["A) A snake", "B) A language", "C) A tool", "D) A framework"],
       "correct": "B"
     },
     ...
   ]
   """
              ↓
5. LLM: Generate quiz
   Returns 3 questions with answers
              ↓
6. FRONTEND: Display quiz
   - Shows questions with radio buttons
   - User selects answers
   - Clicks Submit
              ↓
7. SCORE: Calculate results
   - Compares user answers with correct answers
   - Score = 2/3 = 66.7%
              ↓
8. SAVE: Record quiz result
   POST /student/quiz_complete
   
   Saves to profile:
   quiz_history: [
     {
       topic: "Python Basics",
       score: 2,
       total: 3,
       percentage: 66.7,
       timestamp: "2026-01-10T20:30:00"
     }
   ]
              ↓
9. UPDATE MASTERY: Adjust skill level
   Old mastery: 70.0
   Quiz score: 66.7
   New mastery = 0.7 * 70.0 + 0.3 * 66.7 = 69.0
   
   (Exponential weighted average)
              ↓
10. UNLOCK: Check if should unlock next topic
    If score ≥ 70% → Mark topic complete + unlock next
    If score < 70% → Keep same topic unlocked
              ↓
11. FRONTEND: Show results + update progress ✅
```

---

## 🎨 Chapter 3: Why These Specific Choices?

### **3.1 Why Streamlit + FastAPI (Not MERN/Django/etc.)?**

**Alternatives:**
- **MERN Stack** (MongoDB, Express, React, Node.js)
- **Django** (Python full-stack framework)
- **Flask** + React

**Why our stack is better for AI apps:**

| Feature | Our Stack | MERN | Django |
|---------|-----------|------|--------|
| **Language** | 100% Python | JavaScript + Python hassle | Python |
| **AI/ML Support** | ✅ Native | ❌ Need Python backend anyway | ✅ OK |
| **Speed to build UI** | ✅ Very fast | ❌ Slow (component hell) | ⚠️ Medium |
| **Learning curve** | ✅ Easy | ❌ Hard (JS, React, etc.) | ⚠️ Medium |
| **AI integrations** | ✅ Perfect | ❌ Limited | ⚠️ OK |

**Real example:** The entire Streamlit UI is ~1500 lines. Same in React would be 5000+ lines!

---

### **3.2 Why ChromaDB (Not PostgreSQL for everything)?**

**Question:** Why not just store PDF text in regular database?

**Answer:** Semantic search is IMPOSSIBLE in regular databases!

**Example:**

**Regular Database (PostgreSQL with LIKE):**
```sql
-- User asks: "How do cells produce energy?"
SELECT * FROM documents 
WHERE text LIKE '%produce energy%';

-- ❌ Misses: "mitochondria", "ATP synthesis", "cellular respiration"
-- Only finds exact phrase "produce energy"
```

**Vector Database (ChromaDB):**
```python
# User asks: "How do cells produce energy?"
results = chroma.similarity_search("How do cells produce energy?", k=4)

# ✅ Finds:
# - "The mitochondria is the powerhouse..."
# - "ATP is synthesized through..."
# - "Cellular respiration converts glucose..."
# - "Energy production in eukaryotic cells..."

# All related by MEANING, not exact words!
```

**Why this matters:**
- Students don't ask questions using exact textbook phrases
- Need AI to understand context and meaning
- Vector search makes RAG possible

---

### **3.3 Why Supabase (Not AWS/Firebase/Own server)?**

**Alternatives:**
- **AWS RDS** - Complex, expensive
- **Firebase** - Good but limited free tier
- **Own server** - Too much work

**Why Supabase:**
```
AWS RDS:
- ❌ Complex setup (VPC, security groups, IAM)
- ❌ Expensive ($30+/month minimum)
- ❌ Overkill for our need

Firebase:
- ⚠️ Good but NoSQL (we want SQL)
- ⚠️ Expensive for storage
- ✅ Easy to use

Supabase:
- ✅ PostgreSQL (powerful SQL)
- ✅ 500MB free forever
- ✅ Built-in authentication (future use)
- ✅ Real-time subscriptions
- ✅ 2 clicks to set up
```

---

### **3.4 Why Two LLM Modes (Ollama + HuggingFace)?**

**The Problem:** 
- **Cloud-only apps** → No privacy (data goes to OpenAI, Google, etc.)
- **Local-only apps** → Hard to demo (need Ollama installed)

**Our Solution:** Support both!

```python
# backend/config.py
def get_llm():
    provider = os.getenv("LLM_PROVIDER")  # "ollama" or "huggingface"
    
    if provider == "ollama":
        return Ollama(model="llama3.2:1b")  # Local
    else:
        return HuggingFaceEndpoint(model="meta-llama/Llama-3-8B")  # Cloud
```

**Benefits:**
- **For users:** Choose privacy (local) vs convenience (cloud)
- **For demos:** Just share HuggingFace link
- **For students:** Learn locally without API costs

---

## 🔧 Chapter 4: How Components Talk (The Communication Layer)

### **4.1 Frontend ↔ Backend Communication**

**Technology:** HTTP REST API

**What's REST?** 
- **RE**presentational **S**tate **T**ransfer
- Fancy way of saying: "Send data using URLs"

**Example:**
```
Frontend wants to upload PDF:

1. Package file as HTTP POST request
2. Send to: http://localhost:8000/upload
3. Backend receives, processes, returns JSON
4. Frontend shows success message
```

**Why not WebSockets?**
- REST is simpler
- Most operations don't need real-time
- WebSockets = overkill for this app

---

### **4.2 Backend ↔ LLM Communication**

**For Ollama (Local):**
```python
# Direct connection to local server
from langchain.llms import Ollama
llm = Ollama(base_url="http://localhost:11434")
response = llm.invoke("What is Python?")
```

**For HuggingFace (Cloud):**
```python
# API call to HF servers
from langchain_huggingface import ChatHuggingFace
llm = ChatHuggingFace(
    huggingfacehub_api_token="hf_xxx",
    model="meta-llama/Llama-3-8B-Instruct"
)
response = llm.invoke("What is Python?")
```

**Why ChatHuggingFace wrapper?**
- Llama-3 is a "chat model" (conversational)
- Needs special message formatting
- Wrapper handles format conversion automatically

---

### **4.3 Multi-User System (How Each User Gets Their Own Data)**

**The Challenge:** On cloud (HF Spaces), multiple people use the app simultaneously. How to keep data separate?

**Solution:** Session-based student IDs

```
User A opens app → Gets student_id = "student_abc123"
User B opens app → Gets student_id = "student_xyz789"

When User A saves plan:
  POST /student/save_plan
  Header: X-Student-Id: student_abc123
  
  Backend:
  - Loads profile for "student_abc123"
  - Saves to Supabase with this ID
  
When User B saves plan:
  POST /student/save_plan
  Header: X-Student-Id: student_xyz789
  
  Backend:
  - Loads profile for "student_xyz789"
  - Completely separate data!
```

**Database structure:**
```
student_profiles table:
┌─────────────┬──────────────────────┐
│ student_id  │ profile_data         │
├─────────────┼──────────────────────┤
│ abc123      │ {study_plan: {...}} │
│ xyz789      │ {study_plan: {...}} │
│ def456      │ {study_plan: {...}} │
└─────────────┴──────────────────────┘

Each row = one user's data!
```

---

## 🚀 Chapter 5: Deployment (Getting It Online)

### **5.1 Local Deployment (Run on Your Computer)**

**What happens:**
```
Your Computer:
┌────────────────────────────────┐
│  Terminal 1:                   │
│  $ ollama serve                │  ← Starts AI server
│  Listening on :11434...        │
└────────────────────────────────┘

┌────────────────────────────────┐
│  Terminal 2:                   │
│  $ uvicorn backend.main:app    │  ← Starts API server
│  Running on :8000...           │
└────────────────────────────────┘

┌────────────────────────────────┐
│  Terminal 3:                   │
│  $ streamlit run app.py        │  ← Starts web interface
│  Running on :8501...           │
└────────────────────────────────┘

Your browser:
Go to http://localhost:8501 ✅
```

**File locations:**
- PDFs chunks: `./chroma_db/` (permanent)
- Study plans: `~/.focusflow/student_profile.json` (permanent)
- Sources DB: `data/focusflow.db` (permanent)

---

### **5.2 Cloud Deployment (HuggingFace Spaces)**

**What happens:**
```
HuggingFace Server:
┌──────────────────────────────────────────┐
│  Docker Container                        │
│                                          │
│  1. Reads Dockerfile                     │
│  2. Installs Python 3.10                 │
│  3. Installs all requirements.txt        │
│  4. Copies our code                      │
│  5. Runs /app/start.sh:                  │
│                                          │
│     #!/bin/bash                          │
│     # Start backend                      │
│     uvicorn backend.main:app &           │
│                                          │
│     # Wait for backend health check      │
│     curl http://localhost:8000/health    │
│                                          │
│     # Start frontend                     │
│     streamlit run app.py                 │
│                                          │
│  6. Exposes port 8501 to internet        │
│                                          │
│  URL: https://huggingface.co/spaces/     │
│       SivaRohith69/focusflow             │
└──────────────────────────────────────────┘
```

**Environment variables (secrets in HF Spaces settings):**
```bash
LLM_PROVIDER=huggingface         # Use HF API, not Ollama
USE_SUPABASE=true                # Use cloud DB, not local
HUGGINGFACE_API_TOKEN=hf_xxx     # For LLM access
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
```

**File locations:**
- PDFs chunks: `/app/chroma_db/` (❌ ephemeral - deleted on restart!)
- Study plans: Supabase (✅ permanent)
- Sources DB: `/app/data/focusflow.db` (❌ ephemeral)

---

## 🧠 Chapter 6: The RAG System (How AI Answers Questions)

**RAG = Retrieval-Augmented Generation**

**Simple explanation:**
- **Without RAG:** AI only knows what it learned during training (outdated, generic)
- **With RAG:** AI reads your PDFs first, then answers (accurate, specific)

### **6.1 The Three Steps**

```
┌─────────────────────────────────────────────────────┐
│         STEP 1: RETRIEVAL (Find relevant info)      │
└─────────────────────────────────────────────────────┘
User asks: "What is mitochondria?"
            ↓
Convert to embedding: [0.234, -0.567, ...]
            ↓
Search ChromaDB for similar chunks
            ↓
Returns: 
  1. "The mitochondria is the powerhouse..." (similarity: 0.95)
  2. "Mitochondria have two membranes..." (similarity: 0.88)
  3. "ATP synthesis occurs in mitochondria..." (similarity: 0.85)
  4. "Cellular respiration in mitochondria..." (similarity: 0.82)

┌─────────────────────────────────────────────────────┐
│         STEP 2: AUGMENTATION (Add context)          │
└─────────────────────────────────────────────────────┘
Build prompt:
"""
Context from documents:
1. The mitochondria is the powerhouse...
2. Mitochondria have two membranes...
3. ATP synthesis occurs in mitochondria...
4. Cellular respiration in mitochondria...

Question: What is mitochondria?

Answer the question using ONLY the context above.
Include citations to source.
"""

┌─────────────────────────────────────────────────────┐
│         STEP 3: GENERATION (AI creates answer)      │
└─────────────────────────────────────────────────────┘
Send prompt to LLM (Ollama or HuggingFace)
            ↓
LLM generates answer:
"The mitochondria is the powerhouse of the cell, 
responsible for ATP synthesis through cellular 
respiration. It has two membranes that facilitate 
energy production. [Source: biology.pdf, page 42]"
```

---

### **6.2 Why RAG is Powerful**

**Traditional AI (ChatGPT without RAG):**
```
You: What did the textbook say about photosynthesis?
AI: I don't have access to your specific textbook. But generally,
    photosynthesis is... [generic answer]
```

**Our RAG System:**
```
You: What did the textbook say about photosynthesis?
AI: According to your textbook (biology.pdf, page 67),
    "Photosynthesis converts light energy into chemical 
    energy through the reaction: 6CO2 + 6H2O + light → 
    C6H12O6 + 6O2. This process occurs in chloroplasts..."
    [Exact quote from YOUR PDF!]
```

**The magic:** RAG makes AI "read" your documents before answering!

---

## 📊 Chapter 7: The Frontend Architecture (What You See)

### **7.1 The Three-Column Layout**

```
┌─────────────────────────────────────────────────────────────────┐
│                        FocusFlow                                │
├───────────┬──────────────────────────────┬─────────────────────┤
│  CONTROL  │   INTELLIGENT WORKSPACE      │  CALENDAR & PLAN    │
│  CENTER   │                              │                     │
│           │                              │                     │
│ ┌───────┐ │  Welcome Screen / Lesson /   │  📅 Calendar Widget │
│ │ Timer │ │  Chat / Quiz                 │                     │
│ │ 25:00 │ │                              │  📋 Study Plan      │
│ │ START │ │                              │      - Day 1        │
│ └───────┘ │                              │      - Day 2        │
│           │                              │      - Day 3        │
│ Sources   │                              │                     │
│ ◉ pdf1    │                              │  Today's Topics     │
│ ◉ pdf2    │                              │  ▶ Topic 1 (Start)  │
│           │                              │  🔒 Topic 2         │
│ + Upload  │                              │                     │
│           │                              │  📊 Analytics       │
└───────────┴──────────────────────────────┴─────────────────────┘
     ^                   ^                          ^
     |                   |                          |
   150px              Flexible                    300px
                     (rest of space)
```

**Why this layout?**
- **Left:** Quick access to timer, sources (always visible)
- **Center:** Main focus area (largest space)
- **Right:** Plan overview, quick navigation

**Implemented with:**
```python
col1, col2, col3 = st.columns([0.15, 0.55, 0.3])

with col1:
    st.header("Control Center")
    # Timer, sources, etc.

with col2:
    st.header("Workspace")
    # Lessons, chat, quiz

with col3:
    st.header("Calendar")
    # Calendar, plan, analytics
```

---

### **7.2 Material Design Principles**

**What we use:**
- **Elevation shadows** - Cards float above background
- **Color system** - Primary (blue), accent (purple), surface
- **Typography** - Inter font, hierarchical sizes
- **Animations** - Smooth transitions (150ms)

**Example CSS:**
```css
/* Material Design Card */
.material-card {
    background: white;
    border-radius: 8px;
    padding: 16px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);  /* Elevation-2 */
    transition: box-shadow 150ms ease;
}

.material-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.15);  /* Elevation-3 */
}
```

**Why Material Design?**
- **Professional look** - Looks like Google apps
- **Proven UX patterns** - Users already know how to use it
- **Accessibility** - Good color contrast, clear hierarchy

---

## 🔐 Chapter 8: Data Privacy & Security

### **8.1 What Data We Collect**

**Local Mode:**
- ✅ Everything stays on your computer
- ❌ ZERO data sent to internet
- Your PDFs never uploaded anywhere

**Cloud Mode:**
| Data Type | Stored Where | Private? |
|-----------|-------------|----------|
| PDF content | ChromaDB (ephemeral) | Yes - deleted on restart |
| Study plans | Supabase | ⚠️ In cloud database |
| Quiz scores | Supabase | ⚠️ In cloud database |
| Your questions/answers | Not stored | Yes - processed in-memory |
| PDFs themselves | Not stored | Yes - only processed, not saved |

### **8.2 How We Protect Your Data**

```
1. Session Isolation
   - Each browser tab = unique student_id
   - User A cannot see User B's data
   - Database enforces separation

2. No PDF Storage
   - PDFs processed in-memory
   - Chunks stored, but not original file
   - Even we can't recover your original PDF

3. HTTPS
   - HuggingFace Spaces uses HTTPS
   - Data encrypted in transit

4. Environment Variables
   - API keys stored as secrets
   - Not in code (can't be leaked)

5. Local-First Option
   - Paranoid about privacy? Use local mode!
   - 100% offline, no cloud needed
```

---

## 🎯 Chapter 9: Unique Features (What Makes This Special)

### **9.1 Hybrid Architecture**

**What it means:** Same codebase works both offline AND online

**How:**
```python
# Single config switch changes entire behavior
if os.getenv("LLM_PROVIDER") == "ollama":
    # Local mode: Use Ollama
    llm = Ollama(model="llama3.2:1b")
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    storage = JSONFileStorage()  # Save to local file
else:
    # Cloud mode: Use HuggingFace
    llm = HuggingFaceEndpoint(model="Llama-3-8B")
    embeddings = HuggingFaceEmbeddings(model="all-MiniLM-L6-v2")
    storage = SupabaseStorage()  # Save to cloud DB
```

**Why this is rare:**
- Most apps are cloud-only (no privacy) OR local-only (hard to demo)
- We get best of both worlds!

---

### **9.2 Auto Study Plan Generation**

**Traditional study apps:**
```
User manually creates plan:
- Day 1: Topic A
- Day 2: Topic B
- Day 3: Topic C
(Takes 20 minutes of manual work!)
```

**FocusFlow:**
```
User: "Make a 7-day plan"
AI: *reads all PDFs*
AI: *creates structured plan based on content*

Generated plan:
- Day 1: Python Basics (from intro chapter)
- Day 2: Variables & Data Types (from ch 2-3)
- Day 3: Control Flow (from ch 4)
...

(Done in 10 seconds!)
```

**How:**
1. ChromaDB retrieves all chunk summaries
2. LLM analyzes content
3. Creates logical progression
4. Assigns topics to days
5. Sets prerequisites (unlocking order)

---

### **9.3 Exact Source Citations**

**Traditional chatbots:**
```
User: What is photosynthesis?
Bot: Photosynthesis is the process where plants convert
     light into energy.
     
User: Where did you get this info?
Bot: ¯\_(ツ)_/¯ (can't tell you)
```

**FocusFlow:**
```
User: What is photosynthesis?
Bot: Photosynthesis is the process where plants convert
     light into energy through the reaction 6CO2 + 6H2O 
     + light → C6H12O6 + 6O2.
     
     [Source: biology.pdf, page 67]
     [Source: textbook.pdf, page 142]
     
User: *can verify by opening those exact pages!*
```

**How we do it:**
- Every chunk stored with metadata
- When answering, append source info
- Links are clickable (future: open PDF to exact page)

---

## 🛠️ Chapter 10: The Code Structure

### **10.1 File Organization**

```
focusflow/
│
├── app.py (1457 lines)
│   └── Entire Streamlit frontend
│       - UI layout
│       - Calendar widget
│       - Chat interface
│       - Quiz display
│       - Material Design CSS
│
├── backend/
│   ├── main.py (335 lines)
│   │   └── FastAPI app
│   │       - 15 API endpoints
│   │       - Health check
│   │       - Dependency injection
│   │
│   ├── rag_engine.py (492 lines)
│   │   └── Core RAG logic
│   │       - ingest_document()
│   │       - query_knowledge_base()
│   │       - generate_lesson()
│   │       - generate_quiz()
│   │
│   ├── student_data.py (315 lines)
│   │   └── Profile management
│   │       - load_profile()
│   │       - save_profile()
│   │       - Supports JSON & Supabase
│   │
│   ├── config.py (94 lines)
│   │   └── Configuration
│   │       - LLM provider switching
│   │       - get_llm()
│   │       - get_embeddings()
│   │
│   ├── supabase_storage.py (139 lines)
│   │   └── Supabase adapter
│   │       - Cloud DB operations
│   │       - Error handling
│   │
│   └── database.py (100 lines)
│       └── SQLite models
│           - Sources, Schedules, Mastery
│
├── Dockerfile (44 lines)
│   └── Container configuration
│       - Multi-service startup
│       - Health checks
│
├── requirements.txt (25 packages)
│   ├── streamlit
│   ├── fastapi
│   ├── langchain
│   ├── chromadb
│   ├── supabase
│   └── ...
│
├── README.md
├── TECHNICAL_SUMMARY.json
└── ARCHITECTURE_EXPLAINED.md (this file!)
```

---

### **10.2 Code Flow Example**

**Let's trace: User uploads PDF**

```
1. app.py (Line ~998)
   uploaded_file = st.file_uploader("Upload PDF")
   if uploaded_file:
       files = {"file": uploaded_file}
       resp = requests.post(f"{API_URL}/upload", files=files)
                              ↓
2. backend/main.py (Line ~50)
   @app.post("/upload")
   def upload_file(file: UploadFile, db: Session = Depends(get_db)):
       temp_path = save_temp_file(file)
       result = ingest_document(temp_path, db)
                              ↓
3. backend/rag_engine.py (Line ~40)
   def ingest_document(file_path, db):
       loader = PyPDFLoader(file_path)
       docs = loader.load_and_split(
           text_splitter=RecursiveCharacterTextSplitter(
               chunk_size=1000,
               chunk_overlap=200
           )
       )
                              ↓
4. backend/rag_engine.py (Line ~55)
       embeddings = get_embeddings()  # From config.py
       vector_store = Chroma.from_documents(
           documents=docs,
           embedding=embeddings,
           persist_directory="./chroma_db"
       )
                              ↓
5. backend/database.py (Line ~30)
       new_source = Source(
           filename=file_path,
           type="pdf",
           is_active=True
       )
       db.add(new_source)
       db.commit()
                              ↓
6. backend/main.py (Line ~65)
       return {"status": "success", "chunks": len(docs)}
                              ↓
7. app.py (Line ~1005)
       if resp.status_code == 200:
           st.success("PDF uploaded!")
           # Refresh sources list
```

**Every feature follows similar flow:**
Frontend → API endpoint → RAG/DB logic → Return result → Update UI

---

## 🚨 Chapter 11: Known Issues & Future Improvements

### **11.1 Current Limitations**

1. **ChromaDB Ephemeral on Cloud**
   - **Problem:** Vector DB resets on container restart
   - **Impact:** Must re-upload PDFs after restart
   - **Why:** HF Spaces free tier doesn't support persistent volumes
   - **Solution:** Upgrade to persistent storage OR use S3/external volume

2. **Frontend Doesn't Send Student ID Header**
   - **Problem:** All API calls missing `X-Student-Id` header
   - **Impact:** Cloud users might share profile (bug!)
   - **Fix needed:** Update all `requests.post()` calls to include `get_headers()`
   - **Lines to change:** ~15 API calls in app.py

3. **No User Authentication**
   - **Problem:** Anyone with link can access
   - **Impact:** Not production-ready
   - **Solutions:**
     - Add Streamlit auth
     - Use Supabase authentication
     - Add OAuth (Google, GitHub)

4. **Quiz Questions Not Always Perfect**
   - **Problem:** AI sometimes generates unclear questions
   - **Why:** LLM hallucination, limited context
   - **Solutions:**
     - Increase k (retrieve more chunks)
     - Better prompt engineering
     - Add question validation

---

### **11.2 Future Enhancements**

**Short-term (1-2 weeks):**
- ✅ Fix student ID header issue
- ✅ Add persistent ChromaDB (external volume)
- ✅ Improve quiz prompts
- ✅ Add loading spinners

**Medium-term (1-2 months):**
- 🔄 User authentication (Supabase Auth)
- 🔄 PDF annotation support
- 🔄 Spaced repetition algorithm
- 🔄 Export study plan to calendar (.ics)
- 🔄 Mobile-responsive design

**Long-term (3-6 months):**
- 📅 Collaborative study rooms (multi-user sessions)
- 📅 Video lecture ingestion (YouTube transcripts)
- 📅 Voice input/output
- 📅 Advanced analytics (learning curves, predictions)
- 📅 Plugin system (custom quiz types, etc.)

---

## 📊 Chapter 12: Performance & Scalability

### **12.1 Current Performance**

**Local Mode:**
- PDF upload (10 pages): ~5 seconds
- Study plan generation: ~30 seconds
- Question answering: ~3-5 seconds
- Quiz generation: ~15 seconds

**Bottleneck:** LLM inference (slowest part)

**Cloud Mode:**
- PDF upload (10 pages): ~8 seconds (network latency)
- Study plan generation: ~45 seconds (API rate limits)
- Question answering: ~5-7 seconds
- Quiz generation: ~20 seconds

**Bottleneck:** HuggingFace API rate limits (free tier)

---

### **12.2 Scalability**

**Current limits:**

| Component | Limit | Notes |
|-----------|-------|-------|
| Supabase | 500MB storage | Free tier |
| HF Inference API | ~1000 requests/day | Free tier |
| PDF upload size | 250MB | Streamlit limit |
| Chunks in ChromaDB | ~100K chunks | Memory limit |

**How to scale:**

1. **More users:**
   - Current: ~100 concurrent users (free HF Spaces)
   - Upgrade: ~1000+ users (paid HF Spaces)
   - Better: Deploy to AWS/GCP with auto-scaling

2. **Bigger PDFs:**
   - Current: ~100 pages max (4-5 PDFs)
   - Upgrade: Use external ChromaDB (persistent volume)
   - Better: Distributed vector DB (Pinecone, Weaviate)

3. **Faster responses:**
   - Current: 3-5 sec per query
   - Use GPU for local Ollama: 1-2 sec
   - Use larger HF models: Same speed, better quality

---

## 🎓 Chapter 13: Learning Journey

### **13.1 What You Learned Building This**

By building FocusFlow, you've learned:

**Frontend:**
- ✅ Streamlit for rapid UI development
- ✅ CSS for styling (Material Design)
- ✅ State management (session_state)

**Backend:**
- ✅ FastAPI for building APIs
- ✅ HTTP request/response cycle
- ✅ Dependency injection pattern

**AI/ML:**
- ✅ How LLMs work (prompting, context)
- ✅ Vector embeddings and similarity search
- ✅ RAG (Retrieval-Augmented Generation)
- ✅ LangChain framework

**Databases:**
- ✅ Vector databases (ChromaDB)
- ✅ Relational databases (PostgreSQL, SQLite)
- ✅ JSONB storage patterns

**DevOps:**
- ✅ Docker containerization
- ✅ Multi-service orchestration
- ✅ Cloud deployment (HuggingFace Spaces)
- ✅ Environment variables and secrets

**Architecture:**
- ✅ Microservices pattern (frontend + backend)
- ✅ API design
- ✅ Data modeling
- ✅ Hybrid cloud/local architecture

---

### **13.2 Skills That Transfer to Other Projects**

**This architecture applies to:**
- 📄 Document Q&A systems (legal docs, research papers)
- 🏥 Medical diagnosis assistants (symptom → diagnosis)
- 🛒 E-commerce product search (natural language)
- 📚 Educational platforms (coursework, tutorials)
- 💼 Internal company knowledge bases
- 🤖 Customer support chatbots with context

**The pattern is always:**
1. Ingest documents → Vector DB
2. User query → Similarity search
3. Retrieved context → LLM
4. Generated answer → Show with citations

---

## 🎯 Final Summary

**FocusFlow in 3 sentences:**

1. **Upload PDFs** → AI chunks them and stores embeddings in ChromaDB
2. **Ask questions** → RAG retrieves relevant chunks, LLM generates answers with citations
3. **Study systematically** → AI creates multi-day plans, adaptive quizzes, tracks mastery

**Technology stack:**
- **Frontend:** Streamlit (Python-only, rapid dev)
- **Backend:** FastAPI (async, fast, modern)
- **AI:** Ollama/HuggingFace + LangChain (hybrid local/cloud)
- **Vector DB:** ChromaDB (semantic search)
- **Database:** Supabase (cloud) / SQLite (local)

**Deployment:**
- **Local:** 100% private, offline, powerful
- **Cloud:** Accessible, multi-user, easy to demo

**Unique features:**
- Auto study plan generation from PDFs
- RAG with exact source citations
- Hybrid architecture (works offline AND online)
- Session-based multi-user support
- Material Design professional UI

---

## 🚀 What's Next?

**Now that you understand the architecture:**

1. **Try modifying it:**
   - Change UI colors
   - Add new quiz types
   - Improve prompts
   - Add features

2. **Apply to other domains:**
   - Medical Q&A from research papers
   - Legal document analysis
   - Code documentation assistant

3. **Scale it up:**
   - Add authentication
   - Deploy with persistent storage
   - Use faster LLMs (GPT-4, Claude)

4. **Contribute:**
   - Fix the student ID header bug
   - Add persistent ChromaDB
   - Improve quiz quality

---

**Remember:** Every complex system is just simple parts connected together. You've now seen how ALL the parts work! 🎉

**Questions to test your understanding:**
1. Why do we use ChromaDB instead of just PostgreSQL?
2. What's the difference between `llm.invoke()` in Ollama vs HuggingFace?
3. How does RAG make AI answers more accurate?
4. Why is the frontend separate from the backend?
5. What happens when a PDF is uploaded (step-by-step)?

If you can answer these, you **truly understand** the architecture! 🧠✨
