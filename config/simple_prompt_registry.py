"""
Simplified prompt registry that focuses on prompt text versions
Metadata is handled in code, not in files
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import os
from .simple_prompt_loader import SimplePromptLoader, PromptVersion


class SimplePromptRegistry:
    """Simplified registry that only manages prompt text versions"""
    
    def __init__(self, data_dir: str = "data", prompts_dir: str = "prompts"):
        self.data_dir = data_dir
        self.prompts_dir = prompts_dir
        self.performance_file = os.path.join(data_dir, "prompt_performance.json")
        self.prompt_loader = SimplePromptLoader(prompts_dir)
        self._performance_log: List[Dict[str, Any]] = []
        self._load_performance_data()
        
        # Prompt metadata is now in code
        self._prompt_metadata = {
            "coaching_system": {
                "goal": "Provide supportive productivity coaching and task management advice",
                "model": "gemma3:4b",
                "temperature": 0.7,
                "token_limit": 500,
                "top_p": 0.9
            },
            "task_classification": {
                "goal": "Classify tasks into health, career, and learning categories with high precision",
                "model": "gemma3:4b",
                "temperature": 0.0,
                "token_limit": 100,
                "top_p": 0.9
            }
        }

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

    def get_prompt_text(self, name: str, version: Optional[str] = None) -> Optional[str]:
        """Get prompt text by name and optionally version"""
        prompt = self.prompt_loader.get_prompt(name, version)
        return prompt.text if prompt else None

    def get_latest_prompt_text(self, name: str) -> Optional[str]:
        """Get the latest version of a prompt text"""
        prompt = self.prompt_loader.get_latest_prompt(name)
        return prompt.text if prompt else None

    def get_prompt_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Get prompt metadata from code"""
        return self._prompt_metadata.get(name)

    def get_prompt_config(self, name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get complete prompt configuration (text + metadata)"""
        text = self.get_prompt_text(name, version)
        metadata = self.get_prompt_metadata(name)
        
        if not text or not metadata:
            return None
        
        # Get the specific version info
        prompt_version = self.prompt_loader.get_prompt(name, version)
        if not prompt_version:
            return None
        
        return {
            "name": name,
            "version": prompt_version.version,
            "text": text,
            "created_at": prompt_version.created_at.isoformat() if prompt_version.created_at else None,
            **metadata
        }

    def list_prompts(self) -> List[str]:
        """List all available prompt names"""
        return self.prompt_loader.list_prompts()

    def get_prompt_versions(self, name: str) -> List[PromptVersion]:
        """Get all versions of a specific prompt"""
        return self.prompt_loader.get_prompt_versions(name)

    def save_prompt(self, name: str, version: str, text: str) -> str:
        """Save a new prompt version"""
        return self.prompt_loader.save_prompt(name, version, text)

    def delete_prompt(self, name: str, version: str) -> bool:
        """Delete a specific prompt version"""
        return self.prompt_loader.delete_prompt(name, version)

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

    def add_prompt_metadata(self, name: str, metadata: Dict[str, Any]):
        """Add or update prompt metadata in code"""
        self._prompt_metadata[name] = metadata


# Global simplified registry instance
simple_prompt_registry = SimplePromptRegistry()
