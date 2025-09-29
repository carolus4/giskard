"""
Ollama configuration settings
"""

from .simple_prompt_registry import simple_prompt_registry

# Default Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma3:4b"

# Request timeout in seconds
REQUEST_TIMEOUT = 100  # Reduced back to 30 seconds with better handling


def get_prompt_config(prompt_name: str, version: str = None):
    """Get prompt configuration from registry"""
    return simple_prompt_registry.get_prompt_config(prompt_name, version)


def get_chat_config():
    """Get chat configuration using the latest coaching prompt"""
    coaching_config = simple_prompt_registry.get_prompt_config("coaching_system")
    if coaching_config:
        return {
            "model": coaching_config["model"],
            "stream": False,
            "options": {
                "temperature": coaching_config["temperature"],
                "top_p": coaching_config["top_p"],
                "max_tokens": coaching_config["token_limit"]
            }
        }
    
    # Fallback to default configuration
    return {
        "model": DEFAULT_MODEL,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 500
        }
    }


def get_classification_config():
    """Get classification configuration using the latest classification prompt"""
    classification_config = simple_prompt_registry.get_prompt_config("task_classification")
    if classification_config:
        return {
            "model": classification_config["model"],
            "stream": False,
            "options": {
                "temperature": classification_config["temperature"],
                "top_p": classification_config["top_p"],
                "max_tokens": classification_config["token_limit"]
            }
        }
    
    # Fallback to default configuration
    return {
        "model": DEFAULT_MODEL,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "max_tokens": 100
        }
    }


# Legacy configurations for backward compatibility
CHAT_CONFIG = get_chat_config()
CLASSIFICATION_CONFIG = get_classification_config()
