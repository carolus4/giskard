"""
Enhanced prompt management with Langfuse integration and local fallback
"""
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from langfuse import Langfuse
from config.langfuse_config import langfuse_config

logger = logging.getLogger(__name__)


class PromptManager:
    """
    Enhanced prompt manager that tries Langfuse first, then falls back to local files
    """
    
    def __init__(self, local_prompts_dir: str = "langfuse-prompts"):
        self.local_prompts_dir = local_prompts_dir
        self.langfuse_client = langfuse_config.client if langfuse_config.enabled else None
        
    def get_prompt(self, name: str, label: str = "production", **kwargs) -> Dict[str, Any]:
        """
        Get a prompt from Langfuse or fall back to local file
        
        Args:
            name: Prompt name
            label: Langfuse label (e.g., "staging", "production")
            **kwargs: Additional parameters for prompt compilation
            
        Returns:
            Dictionary containing prompt text and metadata
        """
        # Try Langfuse first
        if self.langfuse_client:
            try:
                prompt = self.langfuse_client.get_prompt(name, label=label)
                logger.info(f"✅ Loaded prompt '{name}' from Langfuse (label: {label})")
                return {
                    "text": prompt.prompt,
                    "name": prompt.name,
                    "label": label,
                    "source": "langfuse",
                    "version": getattr(prompt, 'version', None),
                    "created_at": getattr(prompt, 'created_at', None),
                    "langfuse_prompt": prompt  # Store the actual Langfuse prompt object
                }
            except Exception as e:
                logger.warning(f"Failed to load prompt '{name}' from Langfuse: {e}")
                logger.info(f"Falling back to local prompt file")
        
        # Fallback to local file
        return self.load_local_prompt(name, **kwargs)
    
    def load_local_prompt(self, name: str, **kwargs) -> Dict[str, Any]:
        """
        Load a prompt from local file system
        
        Args:
            name: Prompt name (without extension)
            **kwargs: Additional parameters for prompt compilation
            
        Returns:
            Dictionary containing prompt text and metadata
        """
        file_path = os.path.join(self.local_prompts_dir, f"{name}.txt")
        
        try:
            with open(file_path, 'r') as f:
                text = f.read()
            
            logger.info(f"✅ Loaded prompt '{name}' from local file: {file_path}")
            return {
                "text": text,
                "name": name,
                "source": "local",
                "file_path": file_path,
                "loaded_at": datetime.now().isoformat()
            }
        except FileNotFoundError:
            logger.error(f"Local prompt file not found: {file_path}")
            raise FileNotFoundError(f"Prompt file not found: {file_path}")
        except Exception as e:
            logger.error(f"Error loading local prompt '{name}': {e}")
            raise
    
    def compile_prompt(self, prompt_data: Dict[str, Any], **template_vars) -> str:
        """
        Compile a prompt with template variables using Langfuse syntax {{variable}}
        
        Args:
            prompt_data: Prompt data from get_prompt()
            **template_vars: Variables to substitute in the prompt
            
        Returns:
            Compiled prompt text
        """
        text = prompt_data["text"]
        
        # Add default template variables
        defaults = {
            "current_datetime": datetime.now().isoformat(),
        }
        defaults.update(template_vars)
        
        try:
            # Handle Langfuse template syntax {{variable}}
            import re
            
            # Replace {{variable}} patterns with actual values
            def replace_langfuse_var(match):
                var_name = match.group(1).strip()
                if var_name in defaults:
                    return str(defaults[var_name])
                else:
                    # Keep the original if variable not found
                    return match.group(0)
            
            # Replace Langfuse template variables {{variable}}
            compiled = re.sub(r'\{\{([^}]+)\}\}', replace_langfuse_var, text)
            
            logger.debug(f"Compiled prompt '{prompt_data['name']}' with {len(defaults)} variables")
            return compiled
        except Exception as e:
            logger.error(f"Error compiling prompt: {e}")
            raise
    
    def get_compiled_prompt(self, name: str, label: str = "production", **template_vars) -> str:
        """
        Get and compile a prompt in one step
        
        Args:
            name: Prompt name
            label: Langfuse label
            **template_vars: Template variables
            
        Returns:
            Compiled prompt text
        """
        prompt_data = self.get_prompt(name, label=label)
        return self.compile_prompt(prompt_data, **template_vars)


# Global prompt manager instance
prompt_manager = PromptManager()


def load_local_prompt(name: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to load a local prompt
    """
    return prompt_manager.load_local_prompt(name, **kwargs)


def get_prompt(name: str, label: str = "production", **kwargs) -> Dict[str, Any]:
    """
    Convenience function to get a prompt (Langfuse or local fallback)
    """
    return prompt_manager.get_prompt(name, label=label, **kwargs)


def get_compiled_prompt(name: str, label: str = "production", **template_vars) -> str:
    """
    Convenience function to get and compile a prompt
    """
    return prompt_manager.get_compiled_prompt(name, label=label, **template_vars)
