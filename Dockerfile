FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p data chroma_db

# Expose ports for backend (8000) and frontend (8501)
EXPOSE 8501 8000

# Set environment to use Hugging Face
ENV LLM_PROVIDER=huggingface

# Create startup script
RUN echo '#!/bin/bash\n\
# Start FastAPI backend in background\n\
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &\n\
\n\
# Wait for backend to start\n\
sleep 2\n\
\n\
# Start Streamlit frontend\n\
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true\n\
' > /app/start.sh && chmod +x /app/start.sh

# Run startup script
CMD ["/app/start.sh"]
