"""
Configuration system for FocusFlow LLM providers.
Supports both local (Ollama) and cloud (Hugging Face) deployments.
"""
import os
from enum import Enum

class LLMProvider(Enum):
    """Available LLM providers"""
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"

# Read from environment variable, default to Ollama (local)
USE_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

# Set DEPLOYMENT_MODE=cloud in HuggingFace Spaces secrets
# Leave unset or set to "local" for local development
DEPLOYMENT_MODE = os.environ.get("DEPLOYMENT_MODE", "local").lower()
IS_CLOUD = DEPLOYMENT_MODE == "cloud"

# Configuration for both providers
CONFIG = {
    "llm_provider": LLMProvider.OLLAMA if USE_PROVIDER == "ollama" else LLMProvider.HUGGINGFACE,
    
    # Local Ollama configuration (offline mode)
    "ollama": {
        "model": "llama3.2:1b",
        "base_url": "http://localhost:11434"
    },
    
    # Hugging Face configuration (cloud demo mode)
    "huggingface": {
        "model": "meta-llama/Meta-Llama-3-8B-Instruct",
        "api_token": os.getenv("HUGGINGFACE_API_TOKEN", ""),
        "max_length": 512,
        "temperature": 0.7
    }
}

def get_llm_provider():
    """Get the current LLM provider"""
    return CONFIG["llm_provider"]

def get_llm_config():
    """Get configuration for the current provider"""
    provider = get_llm_provider()
    return CONFIG[provider.value]

def is_local_mode():
    """Check if running in local (offline) mode"""
    return get_llm_provider() == LLMProvider.OLLAMA

def is_cloud_mode():
    """Check if running in cloud (online demo) mode"""
    return get_llm_provider() == LLMProvider.HUGGINGFACE

def get_llm():
    """
    Get LLM instance based on environment configuration.
    Supports both local (Ollama) and cloud (Hugging Face) modes.
    """
    provider = get_llm_provider()
    config = get_llm_config()
    
    if provider == LLMProvider.OLLAMA:
        # Local mode - uses Ollama for offline inference
        return Ollama(
            model=config["model"],
            base_url=config.get("base_url", "http://localhost:11434")
        )
    else:
        # Cloud mode - uses Hugging Face Inference API with Chat wrapper
        from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
        
        # Create base endpoint
        llm = HuggingFaceEndpoint(
            repo_id=config["model"],
            huggingfacehub_api_token=config["api_token"],
            max_new_tokens=512,
            temperature=config.get("temperature", 0.7)
        )
        
        # Wrap with ChatHuggingFace for chat-based models
        return ChatHuggingFace(llm=llm)

def get_embeddings():
    """
    Get embeddings model based on environment configuration.
    Supports both local (Ollama) and cloud (Hugging Face) modes.
    """
    provider = get_llm_provider()
    
    if provider == LLMProvider.OLLAMA:
        # Local mode - uses Ollama embeddings
        from langchain_community.embeddings import OllamaEmbeddings
        return OllamaEmbeddings(model="nomic-embed-text")
    else:
        # Cloud mode - uses Hugging Face embeddings (pre-cached in Docker image)
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )

# ========== FIREBASE AUTH CONFIG ==========
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "")
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY", "")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "")

# ========== OAUTH CONFIG ==========
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
APP_URL = os.getenv("APP_URL", "http://localhost:8501")

def is_firebase_configured():
    """Check if Firebase credentials are available (cloud mode with auth)"""
    return bool(FIREBASE_SERVICE_ACCOUNT_JSON)

# ========== YOUTUBE DATA API CONFIG ==========
# Set YOUTUBE_API_KEY in HuggingFace Spaces secrets for cloud-reliable transcript fetching
# Without it, falls back to youtube-transcript-api (works locally but blocked on datacenter IPs)
# Get your key: https://console.cloud.google.com → Enable YouTube Data API v3 → Create API Key
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", None)

def has_youtube_api_key():
    """Check if YouTube Data API key is configured"""
    return bool(YOUTUBE_API_KEY)
