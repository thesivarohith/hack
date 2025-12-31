# How to Run FocusFlow

FocusFlow consists of two parts: a **Backend** (FastAPI) and a **Frontend** (Streamlit). You need to run both simultaneously in separate terminals.

### Prerequisites
Ensure you are in the project root:
```bash
cd /home/siva/Desktop/hack
```

### Step 1: Start the Backend
The backend handles the database, RAG engine, and logic.
```bash
venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*Wait until you see "Application startup complete".*

### Step 2: Start the Frontend
The frontend is the UI you interact with. Open a **new terminal tab/window** and run:
```bash
venv/bin/streamlit run app.py
```

### Step 3: Access the App
Open your browser to the URL shown in the terminal, usually:
[http://localhost:8501](http://localhost:8501)

---
### Troubleshooting
- **Connection Error?** Ensure Step 1 is running and hasn't crashed.
- **Port Busy?** If port 8000 or 8501 is taken, kill the old processes (`pkill -f uvicorn` or `pkill -f streamlit`) and try again.
