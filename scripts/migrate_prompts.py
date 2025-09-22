#!/usr/bin/env python3
"""
Migration script to convert from old prompt_registry.json to new file-based prompt system
"""

import json
import os
import sys
from datetime import datetime

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.file_prompt_loader import FilePromptLoader, PromptConfig


def migrate_prompts():
    """Migrate prompts from old registry.json to individual files"""
    
    # Paths
    old_registry_path = "data/prompt_registry.json"
    prompts_dir = "prompts"
    
    # Check if old registry exists
    if not os.path.exists(old_registry_path):
        print(f"Old registry file not found at {old_registry_path}")
        print("Migration not needed - using file-based system")
        return
    
    # Create prompts directory if it doesn't exist
    os.makedirs(prompts_dir, exist_ok=True)
    
    # Load old registry
    with open(old_registry_path, 'r') as f:
        old_data = json.load(f)
    
    # Initialize file loader
    file_loader = FilePromptLoader(prompts_dir)
    
    migrated_count = 0
    
    # Migrate each prompt
    for prompt_name, prompt_versions in old_data.items():
        print(f"Migrating {prompt_name}...")
        
        for prompt_data in prompt_versions:
            try:
                # Create PromptConfig from old data
                prompt_config = PromptConfig.from_dict(prompt_data)
                
                # Save to individual file
                filename = file_loader.save_prompt(prompt_config)
                print(f"  -> Saved {filename}")
                migrated_count += 1
                
            except Exception as e:
                print(f"  -> Error migrating {prompt_name} v{prompt_data.get('version', 'unknown')}: {e}")
    
    print(f"\nMigration complete! Migrated {migrated_count} prompts to individual files.")
    print(f"Prompts are now stored in: {prompts_dir}/")
    
    # Ask if user wants to backup the old file
    response = input("\nWould you like to backup the old registry file? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        backup_path = f"{old_registry_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(old_registry_path, backup_path)
        print(f"Old registry backed up to: {backup_path}")
    else:
        print("Old registry file kept as-is")


def list_current_prompts():
    """List all current prompts in the file-based system"""
    file_loader = FilePromptLoader("prompts")
    
    print("Current prompts in file-based system:")
    print("=" * 50)
    
    for prompt_name in file_loader.list_prompts():
        versions = file_loader.get_prompt_versions(prompt_name)
        print(f"\n{prompt_name}:")
        for version in versions:
            print(f"  - v{version.version} ({version.created_at.strftime('%Y-%m-%d %H:%M')})")


if __name__ == "__main__":
    print("Prompt Migration Tool")
    print("=" * 20)
    
    if len(sys.argv) > 1 and sys.argv[1] == "list":
        list_current_prompts()
    else:
        migrate_prompts()
        print("\nTo list current prompts, run: python scripts/migrate_prompts.py list")
