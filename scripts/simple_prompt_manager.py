#!/usr/bin/env python3
"""
Simple prompt manager for text-only prompt versions
Metadata is handled in code, not in files
"""

import os
import sys
from datetime import datetime
from typing import Optional

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.simple_prompt_loader import SimplePromptLoader


class SimplePromptManager:
    """Simple prompt manager for text-only prompts"""
    
    def __init__(self):
        self.loader = SimplePromptLoader("prompts")
    
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
                print(f"    File: {os.path.basename(version.file_path)}")
    
    def show_prompt(self, name: str, version: Optional[str] = None):
        """Show a specific prompt"""
        prompt = self.loader.get_prompt(name, version)
        if not prompt:
            print(f"Prompt '{name}' v{version or 'latest'} not found")
            return
        
        print(f"Prompt: {prompt.name} v{prompt.version}")
        print("=" * 50)
        print(f"File: {os.path.basename(prompt.file_path)}")
        print(f"Created: {prompt.created_at}")
        print("\nPrompt Text:")
        print("-" * 30)
        print(prompt.text)
    
    def create_prompt(self):
        """Interactive prompt creation"""
        print("Create New Prompt Version")
        print("=" * 30)
        
        name = input("Prompt name: ").strip()
        if not name:
            print("Prompt name is required")
            return
        
        version = input("Version (e.g., 1.0): ").strip()
        if not version:
            print("Version is required")
            return
        
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
        
        # Save prompt
        filename = self.loader.save_prompt(name, version, prompt_text)
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
        print(prompt.text)
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
        filename = self.loader.save_prompt(name, version, new_prompt_text)
        print(f"\nPrompt updated successfully: {filename}")
    
    def delete_prompt(self, name: str, version: str):
        """Delete a specific prompt version"""
        if self.loader.delete_prompt(name, version):
            print(f"Deleted {name} v{version}")
        else:
            print(f"Could not delete {name} v{version} (file not found)")
    
    def open_in_editor(self, name: str, version: str):
        """Open prompt in default editor"""
        prompt = self.loader.get_prompt(name, version)
        if not prompt:
            print(f"Prompt '{name}' v{version} not found")
            return
        
        # Try to open with common editors
        editors = ['code', 'nano', 'vim', 'emacs']
        for editor in editors:
            if os.system(f"which {editor} > /dev/null 2>&1") == 0:
                os.system(f"{editor} {prompt.file_path}")
                return
        
        print(f"Could not find a suitable editor. File location: {prompt.file_path}")


def main():
    """Main CLI interface"""
    manager = SimplePromptManager()
    
    if len(sys.argv) < 2:
        print("Simple Prompt Manager - Text-Only Versions")
        print("=" * 45)
        print("Usage:")
        print("  python scripts/simple_prompt_manager.py list")
        print("  python scripts/simple_prompt_manager.py show <name> [version]")
        print("  python scripts/simple_prompt_manager.py create")
        print("  python scripts/simple_prompt_manager.py edit <name> <version>")
        print("  python scripts/simple_prompt_manager.py delete <name> <version>")
        print("  python scripts/simple_prompt_manager.py edit-file <name> <version>")
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
    elif command == "edit-file":
        if len(sys.argv) < 4:
            print("Usage: edit-file <name> <version>")
            return
        name = sys.argv[2]
        version = sys.argv[3]
        manager.open_in_editor(name, version)
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
