---
title: FocusFlow
emoji: 📚
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8501
pinned: false
---

# 📚 FocusFlow - AI Study Companion

An intelligent study assistant powered by AI that transforms your learning materials into personalized, adaptive study experiences.

## ✨ Features

- **📖 Multi-Subject Study Planning**: Upload PDFs and get automated multi-day study plans
- **💬 RAG-Powered Q&A**: Ask questions and get answers with source citations
- **📝 Adaptive Quizzes**: Context-based quizzes that adapt to your performance
- **📊 Progress Tracking**: Track mastery levels and quiz history
- **🎯 Smart Day Progression**: Automatically unlocks new topics as you complete them
- **🔍 Source Citations**: Every answer cites the exact source and page number

## 🤖 Models Used

- **LLM**: Meta-Llama-3-8B-Instruct (via Hugging Face Inference API)
- **Embeddings**: nomic-embed-text (for semantic search)

## 🚀 How to Use

1. **Upload PDFs**: Add your study materials in the Sources panel
2. **Generate Plan**: Ask the Calendar to create a study plan (e.g., "Make a 5-day plan")
3. **Study**: Click on topics to view lessons and ask questions
4. **Take Quizzes**: Test your knowledge and unlock new topics

## 📝 Demo Note

This is a **cloud demo version** running on Hugging Face Spaces using the Llama-3-8B model.

**For offline/local use** with enhanced privacy and llama3.2:1b (no internet required):
- 📂 [GitHub Repository](https://github.com/thesivarohith/hack)
- 📖 [Local Setup Guide](https://github.com/thesivarohith/hack/blob/main/RUN_GUIDE.md)

The local version works completely offline and keeps all your data private on your machine.

## 🛠️ Tech Stack

- **Frontend**: Streamlit
- **Backend**: FastAPI + LangChain
- **Vector DB**: ChromaDB
- **LLM**: Hugging Face Inference API

## 📄 License

MIT License - See [LICENSE](https://github.com/thesivarohith/hack/blob/main/LICENSE) for details.

---

Built with ❤️ for better learning experiences
