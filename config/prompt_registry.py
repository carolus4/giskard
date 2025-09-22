"""
Centralized prompt registry for tracking prompt performance over time
Now uses file-based prompt storage for easier management
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os
from .file_prompt_loader import FilePromptLoader, PromptConfig


# PromptConfig is now imported from file_prompt_loader


class PromptRegistry:
    """Registry for managing and tracking prompt performance"""
    
    def __init__(self, data_dir: str = "data", prompts_dir: str = "prompts"):
        self.data_dir = data_dir
        self.prompts_dir = prompts_dir
        self.performance_file = os.path.join(data_dir, "prompt_performance.json")
        self.file_loader = FilePromptLoader(prompts_dir)
        self._performance_log: List[Dict[str, Any]] = []
        self._load_performance_data()

    def _load_performance_data(self):
        """Load performance data from file"""
        if os.path.exists(self.performance_file):
            try:
                with open(self.performance_file, 'r') as f:
                    self._performance_log = json.load(f)
            except Exception as e:
                print(f"Error loading performance data: {e}")
                self._performance_log = []

    def _save_performance_data(self):
        """Save performance data to file"""
        os.makedirs(self.data_dir, exist_ok=True)
        with open(self.performance_file, 'w') as f:
            json.dump(self._performance_log, f, indent=2)

    def register_prompt(self, prompt_config: PromptConfig) -> str:
        """Register a new prompt configuration"""
        filename = self.file_loader.save_prompt(prompt_config)
        return filename

    def get_prompt(self, name: str, version: Optional[str] = None) -> Optional[PromptConfig]:
        """Get a specific prompt by name and optionally version"""
        return self.file_loader.get_prompt(name, version)

    def get_latest_prompt(self, name: str) -> Optional[PromptConfig]:
        """Get the latest version of a prompt"""
        return self.file_loader.get_latest_prompt(name)

    def list_prompts(self) -> List[str]:
        """List all available prompt names"""
        return self.file_loader.list_prompts()

    def get_prompt_versions(self, name: str) -> List[PromptConfig]:
        """Get all versions of a specific prompt"""
        return self.file_loader.get_prompt_versions(name)

    def log_performance(self, prompt_name: str, prompt_version: str, 
                       output: str, metrics: Optional[Dict[str, Any]] = None):
        """Log performance data for a prompt execution"""
        performance_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt_name": prompt_name,
            "prompt_version": prompt_version,
            "output": output,
            "metrics": metrics or {}
        }
        
        self._performance_log.append(performance_entry)
        self._save_performance_data()

    def get_performance_history(self, prompt_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get performance history, optionally filtered by prompt name"""
        if prompt_name is None:
            return self._performance_log
        
        return [entry for entry in self._performance_log 
                if entry.get('prompt_name') == prompt_name]

    def get_performance_summary(self, prompt_name: str) -> Dict[str, Any]:
        """Get performance summary for a specific prompt"""
        history = self.get_performance_history(prompt_name)
        
        if not history:
            return {"total_executions": 0}
        
        return {
            "total_executions": len(history),
            "latest_execution": history[-1]["timestamp"] if history else None,
            "first_execution": history[0]["timestamp"] if history else None,
            "average_output_length": sum(len(entry.get("output", "")) for entry in history) / len(history)
        }


# Global registry instance
prompt_registry = PromptRegistry()


# Prompts are now loaded from individual files in the prompts/ directory
# No need for hardcoded prompt creation functions
