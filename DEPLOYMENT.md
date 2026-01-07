# FocusFlow Deployment Guide

## Local Deployment (Offline Mode - Default)

**Best for**: Personal study, maximum privacy, offline access

### Prerequisites
- Python 3.10+
- Ollama installed
- 4GB+ RAM

### Setup

```bash
# Clone repository
git clone https://github.com/thesivarohith/hack.git
cd hack

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Ollama models
ollama pull llama3.2:1b
ollama pull nomic-embed-text
```

### Run

```bash
# Terminal 1 - Start backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 - Start frontend
streamlit run app.py
```

Access at: `http://localhost:8501`

---

## Hugging Face Spaces Deployment (Cloud Demo)

**Best for**: Sharing publicly, showcasing

### Prerequisites
- Hugging Face account (free)
- Hugging Face API token

### Step 1: Get HF API Token

1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Click "New token"
3. Name: `focusflow`
4. Type: **Read**
5. Copy the token: `hf_xxxxx`

### Step 2: Create Space

1. Go to [huggingface.co](https://huggingface.co)
2. Click profile → **New Space**
3. Settings:
   - **Name**: `focusflow`
   - **License**: MIT
   - **SDK**: Docker
   - **Hardware**: CPU basic (free)
4. Click **Create Space**

### Step 3: Configure Environment

1. In your space, go to **Settings** → **Variables**
2. Add secret:
   - Key: `HUGGINGFACE_API_TOKEN`
   - Value: `hf_xxxxx` (your token)

### Step 4: Push Code

```bash
# Clone your space
git clone https://huggingface.co/spaces/YOUR_USERNAME/focusflow
cd focusflow

# Copy files from this repo
cp -r /path/to/hack/* .

# Add and commit
git add .
git commit -m "Initial deployment"
git push
```

### Step 5: Wait for Build

- Build takes ~10-15 minutes
- Watch logs in the Space
- Your app will be live at: `https://huggingface.co/spaces/YOUR_USERNAME/focusflow`

---

## Comparison

| Feature | Local (Ollama) | Cloud (HF Spaces) |
|---------|----------------|-------------------|
| **Internet** | ❌ Not required | ✅ Required |
| **Model** | llama3.2:1b (1B params) | Llama-3-8B (8B params) |
| **Speed** | ⚡ Very fast | 🐢 Slower (CPU) |
| **Privacy** | 🔒 100% private | 🌐 Public demo |
| **Cost** | 💰 Free | 💰 Free |
| **Best For** | Daily studying | Sharing/demos |

---

## Switching Modes Locally

### Test Cloud Mode Locally

```bash
# Set environment variables
export LLM_PROVIDER=huggingface
export HUGGINGFACE_API_TOKEN=hf_xxxxx

# Run normally
streamlit run app.py
```

### Back to Local Mode

```bash
# Unset or just restart terminal
unset LLM_PROVIDER
streamlit run app.py
```

---

## Troubleshooting

### Local Mode Issues

**Ollama not found:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2:1b
ollama pull nomic-embed-text
```

**Port already in use:**
```bash
# Find and kill process on port 8501
lsof -ti:8501 | xargs kill -9
```

### Cloud Mode Issues

**API token error:**
- Make sure `HUGGINGFACE_API_TOKEN` is set in HF Space variables
- Token must have at least **Read** permission

**Slow responses:**
- This is normal on free CPU tier
- Responses take 10-30 seconds (vs instant on local)

---

## Support

- **GitHub Issues**: [github.com/thesivarohith/hack/issues](https://github.com/thesivarohith/hack/issues)
- **Documentation**: See [TECHNICAL_DOCUMENTATION.md](./TECHNICAL_DOCUMENTATION.md)

---

**Recommended**: Use local deployment for daily studying, cloud deployment only for demos/sharing.
