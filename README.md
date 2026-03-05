---
title: FocusFlow
emoji: 🎯
colorFrom: purple
colorTo: indigo
sdk: docker
app_file: app.py
pinned: false
---

#  FocusFlow - AI Study Companion

An intelligent study assistant powered by AI that transforms your learning materials into personalized, adaptive study experiences.

##  Features

- ** Multi-Subject Study Planning**: Upload PDFs and get automated multi-day study plans
- ** RAG-Powered Q&A**: Ask questions and get answers with source citations
- ** Adaptive Quizzes**: Context-based quizzes that adapt to your performance
- ** Progress Tracking**: Track mastery levels and quiz history
- ** Smart Day Progression**: Automatically unlocks new topics as you complete them
- ** Source Citations**: Every answer cites the exact source and page number
- ** Cloud Persistence**: Study plans and progress persist across sessions (cloud demo only)
- ** Multi-User Support**: Each browser session maintains isolated data

##  Live Demo

**[Try FocusFlow on Hugging Face Spaces](https://huggingface.co/spaces/SivaRohith69/focusflow)**

> **Note**: The cloud demo uses ephemeral containers. Your data persists in Supabase but each browser tab is treated as a separate user. For true persistent local storage, use the local deployment below.

##  Models Used

### Cloud Demo (HF Spaces)
- **LLM**: Meta-Llama-3-8B-Instruct (via Hugging Face Inference API)
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2

### Local Deployment
- **LLM**: llama3.2:1b (via Ollama - offline)
- **Embeddings**: nomic-embed-text (offline)

##  Local Installation

### Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running
- 8GB+ RAM recommended

### Quick Start

```bash
# Clone the repository
git clone https://github.com/thesivarohith/hack.git
cd hack

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Pull required Ollama models
ollama pull llama3.2:1b
ollama pull nomic-embed-text

# Start the backend
uvicorn backend.main:app --reload &

# Start the frontend
streamlit run app.py
```

Visit `http://localhost:8501` to use the app!

##  How to Use

1. **Upload PDFs**: Add your study materials in the Sources panel
2. **Generate Plan**: Ask the Calendar to create a study plan (e.g., "Make a 5-day plan")
3. **Study**: Click on topics to view lessons and ask questions
4. **Take Quizzes**: Test your knowledge and unlock new topics
5. **Track Progress**: View analytics and mastery levels

##  Architecture

```
┌─────────────────────────────────────────┐
│         Streamlit Frontend              │
│  (Material Design UI + Calendar)        │
└──────────────┬──────────────────────────┘
               │
       ┌───────▼────────┐
       │  FastAPI       │
       │  Backend       │
       └───────┬────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼────┐ ┌──▼────┐ ┌──▼─────────┐
│ ChromaDB│ │  LLM  │ │ Supabase  │
│ (RAG)   │ │       │ │ (Cloud DB)│
└─────────┘ └───────┘ └───────────┘
```

##  Tech Stack

- **Frontend**: Streamlit + Material Design
- **Backend**: FastAPI + LangChain
- **Vector DB**: ChromaDB
- **LLM**: Ollama (local) / HuggingFace (cloud)
- **Database**: Supabase PostgreSQL (cloud) / JSON files (local)

##  Cloud vs Local

| Feature | Local | Cloud (HF Spaces) |
|---------|-------|-------------------|
| **Privacy** |  Fully offline |  Data in cloud |
| **Cost** |  Free |  Free |
| **Speed** |  Depends on hardware |  Fast |
| **Persistence** |  Local files |  Supabase DB |
| **Setup** |  Requires Ollama |  Just click |
| **Multi-user** |  Single user |  Multi-user |

##  Configuration

### Environment Variables

For cloud deployment, set these in Hugging Face Spaces Settings:

```bash
# Required for cloud mode
HUGGINGFACE_API_TOKEN=your_hf_token
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
USE_SUPABASE=true
LLM_PROVIDER=huggingface
```

For local deployment, no configuration needed!

##  Privacy

- **Local Mode**: All data stays on your machine. No internet required.
- **Cloud Mode**: Study plans stored in Supabase. PDFs processed in-memory, not stored.

##  License

MIT License - See [LICENSE](LICENSE) for details.

##  Contributing

Contributions welcome! Please feel free to submit a Pull Request.

##  Contact

For questions or feedback, open an issue on [GitHub](https://github.com/thesivarohith/hack/issues).

---

**Built with  for better learning experiences**

 **Links:**
- [Live Demo](https://huggingface.co/spaces/SivaRohith69/focusflow)

## 🚀 Latest Updates
- ✅ Firebase Authentication (Google, GitHub, Email/Password)
- ✅ OCR support for scanned PDFs
- ✅ Paste Text feature for cloud mode
- ✅ Student data stored in Supabase per user
- ✅ Deployed on HuggingFace Spaces
