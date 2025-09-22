#!/usr/bin/env python3
"""
Enhanced prompt manager for the new file-based prompt system
"""

import json
import os
import sys
from datetime import datetime
from typing import Optional

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.file_prompt_loader import FilePromptLoader, PromptConfig


class PromptManager:
    """Enhanced prompt manager for file-based prompts"""
    
    def __init__(self):
        self.loader = FilePromptLoader("prompts")
    
    def list_prompts(self):
        """List all available prompts with their versions"""
        print("Available Prompts:")
        print("=" * 50)
        
        for prompt_name in self.loader.list_prompts():
            versions = self.loader.get_prompt_versions(prompt_name)
            print(f"\n{prompt_name}:")
            for version in versions:
                created = version.created_at.strftime('%Y-%m-%d %H:%M') if version.created_at else 'Unknown'
                print(f"  - v{version.version} ({created})")
                print(f"    Model: {version.model}, Temp: {version.temperature}")
                print(f"    Goal: {version.goal}")
    
    def show_prompt(self, name: str, version: Optional[str] = None):
        """Show detailed information about a specific prompt"""
        prompt = self.loader.get_prompt(name, version)
        if not prompt:
            print(f"Prompt '{name}' v{version or 'latest'} not found")
            return
        
        print(f"Prompt: {prompt.name} v{prompt.version}")
        print("=" * 50)
        print(f"Goal: {prompt.goal}")
        print(f"Model: {prompt.model}")
        print(f"Temperature: {prompt.temperature}")
        print(f"Token Limit: {prompt.token_limit}")
        print(f"Top P: {prompt.top_p}")
        print(f"Created: {prompt.created_at}")
        print("\nPrompt Text:")
        print("-" * 30)
        print(prompt.prompt)
    
    def create_prompt(self):
        """Interactive prompt creation"""
        print("Create New Prompt")
        print("=" * 20)
        
        name = input("Prompt name: ").strip()
        if not name:
            print("Prompt name is required")
            return
        
        version = input("Version (e.g., 1.0): ").strip()
        if not version:
            print("Version is required")
            return
        
        goal = input("Goal/Description: ").strip()
        model = input("Model (default: gemma3:4b): ").strip() or "gemma3:4b"
        
        try:
            temperature = float(input("Temperature (default: 0.7): ").strip() or "0.7")
        except ValueError:
            temperature = 0.7
        
        try:
            token_limit = int(input("Token limit (default: 500): ").strip() or "500")
        except ValueError:
            token_limit = 500
        
        try:
            top_p = float(input("Top P (default: 0.9): ").strip() or "0.9")
        except ValueError:
            top_p = 0.9
        
        print("\nEnter the prompt text (end with a line containing only 'END'):")
        prompt_lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            prompt_lines.append(line)
        
        prompt_text = "\n".join(prompt_lines)
        
        if not prompt_text.strip():
            print("Prompt text is required")
            return
        
        # Create prompt config
        prompt_config = PromptConfig(
            name=name,
            version=version,
            goal=goal,
            model=model,
            temperature=temperature,
            token_limit=token_limit,
            top_p=top_p,
            prompt=prompt_text
        )
        
        # Save prompt
        filename = self.loader.save_prompt(prompt_config)
        print(f"\nPrompt created successfully: {filename}")
    
    def edit_prompt(self, name: str, version: str):
        """Edit an existing prompt"""
        prompt = self.loader.get_prompt(name, version)
        if not prompt:
            print(f"Prompt '{name}' v{version} not found")
            return
        
        print(f"Editing {name} v{version}")
        print("=" * 30)
        print("Current prompt text:")
        print("-" * 20)
        print(prompt.prompt)
        print("-" * 20)
        
        print("\nEnter new prompt text (end with a line containing only 'END'):")
        prompt_lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            prompt_lines.append(line)
        
        new_prompt_text = "\n".join(prompt_lines)
        
        if not new_prompt_text.strip():
            print("Prompt text is required")
            return
        
        # Update prompt
        prompt.prompt = new_prompt_text
        filename = self.loader.save_prompt(prompt)
        print(f"\nPrompt updated successfully: {filename}")
    
    def delete_prompt(self, name: str, version: str):
        """Delete a specific prompt version"""
        if self.loader.delete_prompt(name, version):
            print(f"Deleted {name} v{version}")
        else:
            print(f"Could not delete {name} v{version} (file not found)")
    
    def export_prompt(self, name: str, version: Optional[str] = None):
        """Export a prompt to a file"""
        prompt = self.loader.get_prompt(name, version)
        if not prompt:
            print(f"Prompt '{name}' v{version or 'latest'} not found")
            return
        
        filename = f"{name}_v{prompt.version}_export.json"
        with open(filename, 'w') as f:
            json.dump(prompt.to_dict(), f, indent=2)
        
        print(f"Exported to: {filename}")


def main():
    """Main CLI interface"""
    manager = PromptManager()
    
    if len(sys.argv) < 2:
        print("Prompt Manager - File-based System")
        print("=" * 40)
        print("Usage:")
        print("  python scripts/prompt_manager_new.py list")
        print("  python scripts/prompt_manager_new.py show <name> [version]")
        print("  python scripts/prompt_manager_new.py create")
        print("  python scripts/prompt_manager_new.py edit <name> <version>")
        print("  python scripts/prompt_manager_new.py delete <name> <version>")
        print("  python scripts/prompt_manager_new.py export <name> [version]")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        manager.list_prompts()
    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: show <name> [version]")
            return
        name = sys.argv[2]
        version = sys.argv[3] if len(sys.argv) > 3 else None
        manager.show_prompt(name, version)
    elif command == "create":
        manager.create_prompt()
    elif command == "edit":
        if len(sys.argv) < 4:
            print("Usage: edit <name> <version>")
            return
        name = sys.argv[2]
        version = sys.argv[3]
        manager.edit_prompt(name, version)
    elif command == "delete":
        if len(sys.argv) < 4:
            print("Usage: delete <name> <version>")
            return
        name = sys.argv[2]
        version = sys.argv[3]
        manager.delete_prompt(name, version)
    elif command == "export":
        if len(sys.argv) < 3:
            print("Usage: export <name> [version]")
            return
        name = sys.argv[2]
        version = sys.argv[3] if len(sys.argv) > 3 else None
        manager.export_prompt(name, version)
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
