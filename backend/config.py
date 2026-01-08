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
        # Cloud mode - uses Hugging Face Inference API
        from langchain_huggingface import HuggingFaceEndpoint
        return HuggingFaceEndpoint(
            repo_id=config["model"],
            huggingfacehub_api_token=config["api_token"],
            max_new_tokens=512,  # Changed from max_length
            temperature=config.get("temperature", 0.7),
            task="text-generation"
        )

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
        # Cloud mode - uses Hugging Face embeddings
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
