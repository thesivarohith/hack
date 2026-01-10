#!/bin/bash
# Debug script to test backend startup locally

echo "Testing backend startup..."
python3 -c "from backend.main import app; print('✅ Backend imports successful')" || {
    echo "❌ Backend import failed!"
    exit 1
}

echo "✅ All imports work!"
echo "Starting backend on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000
