"""
File-based prompt loader for managing prompts as individual files
Each prompt is stored as a separate JSON file with the naming convention: {name}_v{version}.json
"""

import json
import os
import glob
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class PromptConfig:
    """Configuration for a specific prompt attempt"""
    name: str
    version: str
    goal: str
    model: str
    temperature: float
    token_limit: int
    top_k: Optional[int] = None
    top_p: Optional[float] = None
    prompt: str = ""
    prompt_file: Optional[str] = None
    output: Optional[str] = None
    created_at: Optional[datetime] = None
    performance_metrics: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptConfig':
        """Create from dictionary"""
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)


class FilePromptLoader:
    """File-based prompt loader that reads prompts from individual JSON files"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        self._prompts_cache: Dict[str, List[PromptConfig]] = {}
        self._load_all_prompts()

    def _load_all_prompts(self):
        """Load all prompts from the prompts directory"""
        self._prompts_cache = {}
        
        if not os.path.exists(self.prompts_dir):
            os.makedirs(self.prompts_dir, exist_ok=True)
            return

        # Find all prompt files matching the pattern {name}_v{version}.json
        pattern = os.path.join(self.prompts_dir, "*_v*.json")
        prompt_files = glob.glob(pattern)
        
        for file_path in prompt_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    
                # Load prompt text from separate file if specified
                if 'prompt_file' in data:
                    prompt_file_path = os.path.join(self.prompts_dir, data['prompt_file'])
                    if os.path.exists(prompt_file_path):
                        with open(prompt_file_path, 'r') as f:
                            data['prompt'] = f.read()
                    else:
                        print(f"Warning: Prompt file {data['prompt_file']} not found for {data.get('name', 'unknown')}")
                        data['prompt'] = ""
                
                prompt_config = PromptConfig.from_dict(data)
                    
                # Group by prompt name
                if prompt_config.name not in self._prompts_cache:
                    self._prompts_cache[prompt_config.name] = []
                
                self._prompts_cache[prompt_config.name].append(prompt_config)
                    
            except Exception as e:
                print(f"Error loading prompt file {file_path}: {e}")
                continue

        # Sort each prompt list by version
        for name in self._prompts_cache:
            self._prompts_cache[name].sort(key=lambda x: x.version)

    def get_prompt(self, name: str, version: Optional[str] = None) -> Optional[PromptConfig]:
        """Get a specific prompt by name and optionally version"""
        if name not in self._prompts_cache:
            return None
        
        if version is None:
            # Return the latest version
            return self._prompts_cache[name][-1] if self._prompts_cache[name] else None
        
        # Return specific version
        for prompt in self._prompts_cache[name]:
            if prompt.version == version:
                return prompt
        return None

    def get_latest_prompt(self, name: str) -> Optional[PromptConfig]:
        """Get the latest version of a prompt"""
        if name not in self._prompts_cache or not self._prompts_cache[name]:
            return None
        return self._prompts_cache[name][-1]

    def list_prompts(self) -> List[str]:
        """List all available prompt names"""
        return list(self._prompts_cache.keys())

    def get_prompt_versions(self, name: str) -> List[PromptConfig]:
        """Get all versions of a specific prompt"""
        return self._prompts_cache.get(name, [])

    def save_prompt(self, prompt_config: PromptConfig) -> str:
        """Save a prompt configuration to files"""
        os.makedirs(self.prompts_dir, exist_ok=True)
        
        # Save JSON metadata file
        json_filename = f"{prompt_config.name}_v{prompt_config.version}.json"
        json_file_path = os.path.join(self.prompts_dir, json_filename)
        
        # Save text file for prompt content
        txt_filename = f"{prompt_config.name}_v{prompt_config.version}.txt"
        txt_file_path = os.path.join(self.prompts_dir, txt_filename)
        
        # Save prompt text to separate file
        with open(txt_file_path, 'w') as f:
            f.write(prompt_config.prompt)
        
        # Create metadata dict with reference to text file
        metadata = prompt_config.to_dict()
        metadata['prompt_file'] = txt_filename
        del metadata['prompt']  # Remove prompt text from JSON
        
        # Save JSON metadata
        with open(json_file_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Reload cache to include the new prompt
        self._load_all_prompts()
        
        return json_filename

    def delete_prompt(self, name: str, version: str) -> bool:
        """Delete a specific prompt version"""
        json_filename = f"{name}_v{version}.json"
        json_file_path = os.path.join(self.prompts_dir, json_filename)
        txt_filename = f"{name}_v{version}.txt"
        txt_file_path = os.path.join(self.prompts_dir, txt_filename)
        
        deleted = False
        if os.path.exists(json_file_path):
            os.remove(json_file_path)
            deleted = True
        if os.path.exists(txt_file_path):
            os.remove(txt_file_path)
            deleted = True
            
        if deleted:
            self._load_all_prompts()
        return deleted

    def refresh_cache(self):
        """Refresh the prompts cache by reloading all files"""
        self._load_all_prompts()

    def get_prompt_file_path(self, name: str, version: str) -> str:
        """Get the file path for a specific prompt version"""
        filename = f"{name}_v{version}.json"
        return os.path.join(self.prompts_dir, filename)

    def list_prompt_files(self) -> List[str]:
        """List all prompt files in the directory"""
        if not os.path.exists(self.prompts_dir):
            return []
        
        pattern = os.path.join(self.prompts_dir, "*_v*.json")
        return glob.glob(pattern)


# Global file-based prompt loader instance
file_prompt_loader = FilePromptLoader()
