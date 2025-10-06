"""
Configuration management for the router system
"""
import os
from typing import Optional
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class RouterConfig(BaseSettings):
    """Configuration for the router system"""
    
    # Model configuration
    model_name: str = Field(default="gemma3:4b", description="Ollama model name")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    
    # API configuration
    api_base_url: str = Field(default="http://localhost:5001", description="API base URL")
    
    # Router configuration
    prompt_file: str = Field(default="prompts/router_v1.3.txt", description="Router prompt file path")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    timeout_seconds: int = Field(default=30, description="Request timeout in seconds")
    
    # Logging configuration
    log_level: str = Field(default="INFO", description="Logging level")
    enable_structured_logging: bool = Field(default=True, description="Enable structured logging")
    
    class Config:
        env_prefix = "GISKARD_ROUTER_"
        case_sensitive = False


class RouterConfigManager:
    """Manager for router configuration"""
    
    def __init__(self, config: Optional[RouterConfig] = None):
        self.config = config or RouterConfig()
    
    def get_model_config(self) -> dict:
        """Get model configuration"""
        return {
            "model_name": self.config.model_name,
            "base_url": self.config.ollama_base_url
        }
    
    def get_api_config(self) -> dict:
        """Get API configuration"""
        return {
            "base_url": self.config.api_base_url
        }
    
    def get_router_config(self) -> dict:
        """Get router configuration"""
        return {
            "prompt_file": self.config.prompt_file,
            "max_retries": self.config.max_retries,
            "timeout_seconds": self.config.timeout_seconds
        }
    
    def get_logging_config(self) -> dict:
        """Get logging configuration"""
        return {
            "log_level": self.config.log_level,
            "enable_structured_logging": self.config.enable_structured_logging
        }
    
    @classmethod
    def from_env(cls) -> 'RouterConfigManager':
        """Create configuration from environment variables"""
        return cls(RouterConfig())
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'RouterConfigManager':
        """Create configuration from dictionary"""
        return cls(RouterConfig(**config_dict))
