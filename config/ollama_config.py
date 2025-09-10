"""
Ollama configuration settings
"""

# Default Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "llama3.1:8b"

# Chat/Coaching configuration
CHAT_CONFIG = {
    "model": DEFAULT_MODEL,
    "stream": False,
    "options": {
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 500
    }
}

# Classification configuration (more conservative for consistency)
CLASSIFICATION_CONFIG = {
    "model": DEFAULT_MODEL,
    "stream": False,
    "options": {
        "temperature": 0.1,  # Low temperature for consistent classification
        "top_p": 0.9,
        "max_tokens": 100
    }
}

# Request timeout in seconds
REQUEST_TIMEOUT = 30
