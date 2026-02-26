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

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data chroma_db logs

# Expose ports for backend (8000) and frontend (8501)
EXPOSE 8501 8000

# Set environment to use Hugging Face
ENV LLM_PROVIDER=huggingface

# Enable Supabase for persistent storage
ENV USE_SUPABASE=true

# Create production startup script with health checks
RUN echo '#!/bin/bash\n\
    set -e\n\
    \n\
    echo "=== FocusFlow Startup ===" \n\
    echo "Starting backend on port 8000..." \n\
    \n\
    # Start FastAPI backend\n\
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &\n\
    BACKEND_PID=$!\n\
    echo "Backend started with PID $BACKEND_PID" \n\
    \n\
    # Wait for backend to be healthy (max 60 seconds)\n\
    echo "Waiting for backend health check..." \n\
    for i in {1..60}; do\n\
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then\n\
    echo "✅ Backend is healthy!" \n\
    break\n\
    fi\n\
    if [ $i -eq 60 ]; then\n\
    echo "❌ Backend failed to start. Logs:" \n\
    tail -50 logs/backend.log\n\
    exit 1\n\
    fi\n\
    echo "Attempt $i/60 - waiting..." \n\
    sleep 1\n\
    done\n\
    \n\
    # Start Streamlit frontend\n\
    echo "Starting frontend on port 8501..." \n\
    exec streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true\n\
    ' > /app/start.sh && chmod +x /app/start.sh

# Run startup script
CMD ["/app/start.sh"]
