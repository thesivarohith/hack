# FocusFlow - Technical Documentation

## 📋 Project Overview

### Problem Statement

Students face significant challenges in managing self-paced learning:

- **Information Overload**: PDFs, videos, and notes scattered across sources make it difficult to create coherent study plans
- **Lack of Personalization**: Generic study materials don't adapt to individual learning pace or mastery level
- **No Progress Tracking**: Students can't easily measure improvement or identify knowledge gaps
- **Verification Gap**: No way to trace AI-generated answers back to source materials

### Solution Description

FocusFlow is an **intelligent, local-first study companion** that transforms unstructured learning materials into personalized, adaptive study experiences. It combines RAG (Retrieval-Augmented Generation) with synthetic student profiling to create customized learning paths that evolve based on performance.

**Key Innovation**: Synthetic student profiles enable the app to "remember" progress across sessions and dynamically adjust difficulty, review frequency, and content depth based on demonstrated mastery.

### Target Users

- **Self-paced learners** preparing for exams or certifications
- **Students** managing multiple subjects with varied materials
- **Knowledge workers** building expertise in new domains
- **Anyone** seeking structured, verifiable learning from diverse sources

---

## 🎯 Core Features

### 1. Multi-Subject Study Roadmap Generation

- **Automated topic extraction** from uploaded PDFs and documents
- **Multi-day planning** with topics distributed across subjects
- **Subject identification** from document content and metadata
- **Round-robin scheduling** ensures balanced coverage across all subjects
- **Progressive unlocking** - topics unlock as previous ones are completed

**Example**: Upload 3 PDFs → Get 5-day plan with 3 topics/day (one from each subject)

### 2. RAG-Based Q&A System

- **Context-aware retrieval** using ChromaDB vector search
- **Conversational memory** with chat history rewriting for follow-up questions
- **Multi-source search** across all uploaded documents
- **Streaming responses** with source citation
- **Focus Mode** for distraction-free studying with side-by-side lesson/chat

### 3. Adaptive Quiz Generation

- **Context-based questions** generated from actual course material
- **Realistic distractors** using common misconceptions
- **Guaranteed 3-question format** with intelligent fallbacks
- **Score-based adaptation**:
  - Perfect score (3/3) → Future topics marked "Advanced"
  - Low score (1-2/3) → Future topics include review materials
- **Automatic unlocking** of next topic upon quiz completion

### 4. Knowledge Tracking & Mastery System

- **Subject-level mastery tracking** (High/Medium/Low)
- **Historical quiz performance** with timestamps
- **Average score calculation** across all attempts
- **Mastery-based difficulty adjustment** for future content
- **Analytics dashboard** with performance classification

### 5. Synthetic Student Profiles

- **Persistent JSON storage** in `~/.focusflow/student_profile.json`
- **Comprehensive tracking**:
  - Study plan with topic metadata
  - Quiz history with scores and timestamps
  - Mastery levels per subject
  - Time tracking per topic
  - Incomplete task queue
- **Atomic writes** with backup for data integrity
- **Thread-safe operations** for concurrent access

### 6. Data Persistence & Session Resumption

- **Auto-save on key events**:
  - Plan generation
  - Quiz completion
  - Topic transitions
- **Auto-load on startup** restores:
  - Active study plan
  - Quiz scores and progress
  - Mastery levels
  - Current position
- **Toast notifications** for save/load feedback

### 7. Citations & Source Verification

- **Expandable source references** with every AI response
- **File + page number** for each citation
- **Lesson content references** section at bottom
- **Inline citation prompts** to LLM for accurate attribution
- **Numbered citation format** for easy lookup

---

## 🏗️ Technical Architecture

### Frontend Components (Streamlit)

```
┌─────────────────────────────────────────────────┐
│  Control Center  │  Workspace  │   Calendar     │
│  (Sidebar)       │  (Main)     │   (Sidebar)    │
├──────────────────┼─────────────┼────────────────┤
│ - Study Timer    │ - Chat UI   │ - Date Picker  │
│ - Sources List   │ - Lessons   │ - Plan View    │
│ - File Upload    │ - Analytics │ - Today's      │
│ - Plan Gen       │ - Quizzes   │   Topics       │
└──────────────────┴─────────────┴────────────────┘
```

**Key UI Panels**:
- **Control Center**: Timer, source management, plan generation
- **Intelligent Workspace**: RAG chat, lesson viewer, analytics modal
- **Calendar**: Date-based topic navigation, today's task list
- **Focus Mode**: Immersive 2-column layout (chat | lesson)

**Chat Interface**:
- Message history with role differentiation (user/assistant)
- Source citation expandables
- Streaming/static responses
- Contained scrollable area (600px height)

**Lesson Viewer**:
- Markdown rendering with references section
- Scrollable document container (650px height)
- Inline citations and code examples

### Backend Logic (FastAPI)

**Planning Engine** (`generate_study_plan`):
1. Query vector store for topic-related content
2. Group documents by source (each source = subject)
3. Extract subject names from content/metadata
4. Round-robin topic selection across subjects
5. Generate multi-day schedule with metadata

**Retrieval System** (`query_knowledge_base`):
1. Context rewriting for multi-turn conversations
2. Similarity search across vector database
3. LLM synthesis with retrieved context
4. Source metadata extraction and return

**Quiz Generator** (`generate_quiz_data`):
1. Retrieve relevant content chunks for topic
2. Prompt LLM for context-based questions
3. Fallback question generation from raw content
4. Ensure exact 3-question output
5. Return structured quiz data

**Lesson Generator** (`generate_lesson_content`):
1. Retrieve 8 context chunks (500 chars each)
2. Extract source citations from metadata
3. Prompt for structured lesson (600-800 words)
4. Append references section with file + page
5. Return formatted Markdown

### Data Storage

**Vector Database (ChromaDB)**:
- Local storage at `./chroma_db`
- Nomic-embed-text embeddings
- Metadata: source path, page number
- Persistent across sessions

**Student Profiles (JSON)**:
```json
{
  "student_id": "student_20260105_233537",
  "study_plan": {
    "plan_id": "plan_...",
    "topics": [...],
    "num_days": 5
  },
  "quiz_history": [...],
  "mastery_tracker": {...},
  "time_tracking": {...},
  "incomplete_tasks": [...]
}
```

**File Storage**:
- Uploaded PDFs in `./data/`
- Profile at `~/.focusflow/student_profile.json`
- Backup at `~/.focusflow/student_profile.backup.json`

### Agentic Behaviors

**Multi-Step Planning**:
- Query → Retrieval → Topic Extraction → Subject Grouping → Schedule Generation
- 5+ steps with intermediate reasoning

**Tool Use**:
- Vector DB search
- LLM generation
- Profile read/write
- PDF ingestion

**Memory**:
- Chat history (5 last messages)
- Student profile persistence
- Quiz performance tracking
- Mastery levels

**Reflection**:
- Score-based plan adaptation
- Context quality assessment
- Fallback strategies for generation failures

---

## 💻 Tech Stack

### Languages & Frameworks

- **Frontend**: Python + Streamlit 1.x
- **Backend**: FastAPI + Uvicorn
- **Vector DB**: ChromaDB
- **LLM Orchestration**: LangChain

### Libraries & APIs

**Core Dependencies**:
```python
streamlit              # Frontend UI
fastapi               # Backend API
uvicorn              # ASGI server
langchain            # LLM orchestration
chromadb             # Vector database
ollama               # Local LLM inference
requests             # API communication
pydantic             # Data validation
```

**Document Processing**:
```python
pypdf                # PDF parsing
beautifulsoup4       # Web scraping
youtube-transcript-api  # Video transcripts
```

**Data & Visualization**:
```python
pandas               # Data manipulation
plotly               # Analytics charts
```

### Models

- **Embedding**: `nomic-embed-text` (local via Ollama)
- **Generation**: `llama3.2:1b` (local via Ollama)

### Storage Methods

- **Vector Store**: ChromaDB (local, persistent)
- **Profiles**: JSON files (atomic writes)
- **PDF Files**: Local filesystem (`./data/`)
- **Session State**: Streamlit session storage

---

## 🔄 Key Workflows

### Workflow 1: Study Plan Generation

```
User uploads PDFs
      ↓
Backend ingests → Chunks → Embeds → Stores in ChromaDB
      ↓
User: "Create 5-day plan"
      ↓
retrieve_topics(k=20)
      ↓
group_by_source() → identify_subjects()
      ↓
round_robin_schedule(num_days=5)
      ↓
save_to_profile() → Return plan
      ↓
Frontend displays Today's Topics (Day 1 unlocked)
```

### Workflow 2: RAG Retrieval

```
User asks: "What is encapsulation?"
      ↓
history_exists? → rewrite_query()  [Context rewriting]
      ↓
similarity_search(question, k=3)
      ↓
build_prompt(context + history + question)
      ↓
llm.invoke() → extract_sources()
      ↓
Return {answer: str, sources: [{file, page}]}
      ↓
Frontend displays answer + expandable citations
```

### Workflow 3: Adaptive Quiz Flow

```
User unlocks Topic
      ↓
load_lesson() → display_markdown()
      ↓
User clicks "Take Quiz"
      ↓
retrieve_context(topic, k=8)
      ↓
generate_quiz(3_questions)
      ↓
fallback if < 3? → context_based_fallback()
      ↓
User answers → calculate_score()
      ↓
score==3? → mark_advanced()
score<3?  → mark_review()
      ↓
update_mastery_tracker() → save_profile()
      ↓
unlock_next_topic() → rerun()
```

### Workflow 4: Mastery Tracking Adaptation

```
Quiz completed with score X
      ↓
update_subject_mastery({
  scores: [..., X],
  avg_score: calculate_average(),
  mastery_level: determine_level()  // High: ≥75%, Medium: ≥50%, Low: <50%
})
      ↓
mastery_level==HIGH?
  → Future topics: Faster pace, advanced examples
mastery_level==LOW?
  → Future topics: More review, foundational content
      ↓
save_to_profile()
      ↓
Next plan generation uses mastery data for difficulty
```

---

## 📊 Evaluation Metrics

### 1. Plan Quality Assessment

**Metrics**:
- **Subject Coverage**: % of uploaded subjects represented daily
- **Balance Score**: Standard deviation of topics per subject
- **Unlocking Logic**: % of topics that unlock correctly after quiz

**Target**:
- 100% subject coverage (all PDFs represented)
- StdDev < 0.5 (even distribution)
- 100% unlock success rate

### 2. Answer Accuracy Measurement

**Metrics**:
- **Source Relevance**: Cosine similarity of retrieved chunks
- **Citation Accuracy**: % of answers with valid file+page citations
- **Hallucination Rate**: Manual review of 50 Q&A pairs

**Target**:
- Avg similarity > 0.7
- 95%+ citation accuracy
- <5% hallucination rate

### 3. Quiz Discrimination

**Metrics**:
- **Question Validity**: % of questions answerable from provided context
- **Distractor Quality**: % of students choosing incorrect options
- **Difficulty Spread**: Distribution across easy/medium/hard

**Target**:
- 100% context-answerable
- 25-40% distractor selection rate (not too easy/hard)
- Balanced difficulty distribution

### 4. User Mastery Gains

**Metrics**:
- **Score Progression**: Δ average score from Day 1 to Day N
- **Mastery Level Changes**: % of subjects moving from Low → Medium → High
- **Retention Rate**: Quiz score on repeated topics after 1 week

**Target**:
- +15% average score improvement over 5 days
- 60%+ mastery level improvement
- 80%+ retention on repeated topics

### 5. System Performance

**Metrics**:
- **Plan Generation Time**: Seconds to generate 5-day plan
- **Query Response Time**: Seconds from question to answer
- **Profile Save Latency**: Milliseconds for atomic write

**Target**:
- Plan gen: <10 seconds
- Query response: <5 seconds
- Save latency: <100ms

---

## 🚀 Future Enhancements

- **Spaced Repetition**: Intelligent review scheduling using SM-2 algorithm
- **Multi-User Support**: Authentication + isolated student profiles
- **Cloud Deployment**: Oracle Cloud + Supabase for persistence
- **Advanced Analytics**: Learning curve visualization, weak area identification
- **Mobile Responsive**: Material Design responsive UI for mobile devices

---

## 📝 Project Repository

**GitHub**: [thesivarohith/hack](https://github.com/thesivarohith/hack)

**Status**: Production-ready, cleaned codebase (commit: 9a8a489)

---

*Documentation generated: 2026-01-06*
