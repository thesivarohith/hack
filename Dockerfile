FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the sentence-transformers embedding model during build
# so it's cached in the image and doesn't need network at runtime
ENV HF_HOME=/app/.cache/huggingface
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data chroma_db logs

# Expose ports for backend (8000) and frontend (8501)
EXPOSE 8501 8000

# Set environment to use Hugging Face
ENV LLM_PROVIDER=huggingface

# Use cached model — don't try to download at runtime
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1

# Enable Supabase for persistent storage
ENV USE_SUPABASE=true

# Create production startup script with health checks
RUN echo '#!/bin/bash\n\
    set -e\n\
    \n\
    echo "===== Application Startup at $(date) =====" \n\
    echo "=== FocusFlow Startup ===" \n\
    \n\
    # Wait for DNS/networking to be ready (HF Spaces can be slow)\n\
    echo "Waiting for network readiness..." \n\
    sleep 3\n\
    \n\
    echo "Starting backend on port 8000..." \n\
    \n\
    # Start FastAPI backend\n\
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &\n\
    BACKEND_PID=$!\n\
    echo "Backend started with PID $BACKEND_PID" \n\
    \n\
    # Wait for backend to be healthy (max 90 seconds)\n\
    echo "Waiting for backend health check..." \n\
    for i in {1..90}; do\n\
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then\n\
    echo "✅ Backend is healthy!" \n\
    break\n\
    fi\n\
    if [ $i -eq 90 ]; then\n\
    echo "❌ Backend failed to start. Logs:" \n\
    tail -50 logs/backend.log\n\
    exit 1\n\
    fi\n\
    echo "Attempt $i/90 - waiting..." \n\
    sleep 1\n\
    done\n\
    \n\
    # Test critical imports before launching Streamlit\n\
    echo "Testing Python imports..." \n\
    python3 -c "\n\
import sys\n\
try:\n\
    import streamlit; print(\"  ✅ streamlit\")\n\
except Exception as e: print(f\"  ❌ streamlit: {e}\"); sys.exit(1)\n\
try:\n\
    import requests; print(\"  ✅ requests\")\n\
except Exception as e: print(f\"  ❌ requests: {e}\")\n\
try:\n\
    from streamlit_calendar import calendar; print(\"  ✅ streamlit_calendar\")\n\
except Exception as e: print(f\"  ❌ streamlit_calendar: {e}\")\n\
try:\n\
    import firebase_admin; print(\"  ✅ firebase_admin\")\n\
except Exception as e: print(f\"  ❌ firebase_admin: {e}\")\n\
print(\"Import check complete.\")\n\
    "\n\
    \n\
    # Start Streamlit frontend\n\
    echo "Starting frontend on port 8501..." \n\
    exec streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true 2>&1\n\
    ' > /app/start.sh && chmod +x /app/start.sh

# Run startup script
CMD ["/app/start.sh"]
