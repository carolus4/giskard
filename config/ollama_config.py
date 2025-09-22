"""
Ollama configuration settings
"""

from .prompt_registry import prompt_registry

# Default Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "gemma3:4b"

# Request timeout in seconds
REQUEST_TIMEOUT = 100  # Reduced back to 30 seconds with better handling


def get_prompt_config(prompt_name: str, version: str = None):
    """Get prompt configuration from registry"""
    return prompt_registry.get_prompt(prompt_name, version)


def get_chat_config():
    """Get chat configuration using the latest coaching prompt"""
    coaching_prompt = prompt_registry.get_latest_prompt("coaching_system")
    if coaching_prompt:
        return {
            "model": coaching_prompt.model,
            "stream": False,
            "options": {
                "temperature": coaching_prompt.temperature,
                "top_p": coaching_prompt.top_p,
                "max_tokens": coaching_prompt.token_limit,
                "top_k": coaching_prompt.top_k
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
    classification_prompt = prompt_registry.get_latest_prompt("task_classification")
    if classification_prompt:
        return {
            "model": classification_prompt.model,
            "stream": False,
            "options": {
                "temperature": classification_prompt.temperature,
                "top_p": classification_prompt.top_p,
                "max_tokens": classification_prompt.token_limit,
                "top_k": classification_prompt.top_k
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
