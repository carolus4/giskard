"""
Simple prompt loader that focuses only on versioning prompt text
Metadata (model, temperature, etc.) is handled in code, not in files
"""

import os
import glob
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PromptVersion:
    """Simple prompt version with just the essential info"""
    name: str
    version: str
    text: str
    file_path: str
    created_at: Optional[datetime] = None


class SimplePromptLoader:
    """Simple prompt loader that only manages prompt text versions"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        self._prompts_cache: Dict[str, List[PromptVersion]] = {}
        self._load_all_prompts()

    def _load_all_prompts(self):
        """Load all prompt text files"""
        self._prompts_cache = {}
        
        if not os.path.exists(self.prompts_dir):
            os.makedirs(self.prompts_dir, exist_ok=True)
            return

        # Find all prompt text files matching the pattern {name}_v{version}.txt
        pattern = os.path.join(self.prompts_dir, "*_v*.txt")
        prompt_files = glob.glob(pattern)
        
        for file_path in prompt_files:
            try:
                # Extract name and version from filename
                filename = os.path.basename(file_path)
                name_part = filename.replace('.txt', '')
                
                # Split on '_v' to separate name and version
                if '_v' in name_part:
                    name, version = name_part.rsplit('_v', 1)
                else:
                    print(f"Warning: File {filename} doesn't follow naming convention")
                    continue
                
                # Read the prompt text
                with open(file_path, 'r') as f:
                    text = f.read()
                
                # Get file modification time as created_at
                created_at = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                prompt_version = PromptVersion(
                    name=name,
                    version=version,
                    text=text,
                    file_path=file_path,
                    created_at=created_at
                )
                
                # Group by prompt name
                if name not in self._prompts_cache:
                    self._prompts_cache[name] = []
                
                self._prompts_cache[name].append(prompt_version)
                    
            except Exception as e:
                print(f"Error loading prompt file {file_path}: {e}")
                continue

        # Sort each prompt list by version
        for name in self._prompts_cache:
            self._prompts_cache[name].sort(key=lambda x: x.version)

    def get_prompt(self, name: str, version: Optional[str] = None) -> Optional[PromptVersion]:
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

    def get_latest_prompt(self, name: str) -> Optional[PromptVersion]:
        """Get the latest version of a prompt"""
        if name not in self._prompts_cache or not self._prompts_cache[name]:
            return None
        return self._prompts_cache[name][-1]

    def list_prompts(self) -> List[str]:
        """List all available prompt names"""
        return list(self._prompts_cache.keys())

    def get_prompt_versions(self, name: str) -> List[PromptVersion]:
        """Get all versions of a specific prompt"""
        return self._prompts_cache.get(name, [])

    def save_prompt(self, name: str, version: str, text: str) -> str:
        """Save a prompt text to a file"""
        os.makedirs(self.prompts_dir, exist_ok=True)
        
        filename = f"{name}_v{version}.txt"
        file_path = os.path.join(self.prompts_dir, filename)
        
        with open(file_path, 'w') as f:
            f.write(text)
        
        # Reload cache to include the new prompt
        self._load_all_prompts()
        
        return filename

    def delete_prompt(self, name: str, version: str) -> bool:
        """Delete a specific prompt version"""
        filename = f"{name}_v{version}.txt"
        file_path = os.path.join(self.prompts_dir, filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            self._load_all_prompts()
            return True
        return False

    def refresh_cache(self):
        """Refresh the prompts cache by reloading all files"""
        self._load_all_prompts()


# Global simple prompt loader instance
simple_prompt_loader = SimplePromptLoader()
