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
