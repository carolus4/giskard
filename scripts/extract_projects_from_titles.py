#!/usr/bin/env python3
"""
Migration script to extract project names from task titles and populate the project field
This fixes the legacy format where projects were embedded in titles like "[Project] Task Title"
"""
import os
import sys
import re
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.task_db import TaskDB

def extract_projects_from_titles():
    """Extract project names from task titles and populate the project field"""
    print("🔄 Extracting project names from task titles...")
    
    # Pattern to match [Project] Task Title format
    project_pattern = r'^\[([^\]]+)\]\s+(.+)$'
    
    # Get all tasks
    tasks = TaskDB.get_all()
    updated_count = 0
    
    print(f"📊 Found {len(tasks)} total tasks")
    
    for task in tasks:
        # Skip if task already has a project
        if task.project:
            continue
            
        # Check if title matches the pattern
        match = re.match(project_pattern, task.title)
        if match:
            project_name = match.group(1).strip()
            clean_title = match.group(2).strip()
            
            # Update the task
            task.project = project_name
            task.title = clean_title
            task.save()
            
            updated_count += 1
            print(f"  ✅ Updated: \"[{project_name}] {clean_title}\" -> Project: {project_name}, Title: {clean_title}")
    
    print(f"\\n🎉 Migration complete!")
    print(f"📈 Updated {updated_count} tasks")
    print(f"📊 {len(tasks) - updated_count} tasks already had proper format or no project")
    
    return updated_count

def verify_migration():
    """Verify the migration was successful"""
    print("\\n🔍 Verifying migration...")
    
    tasks = TaskDB.get_all()
    project_pattern = r'^\[([^\]]+)\]\s+(.+)$'
    
    remaining_embedded = 0
    tasks_with_projects = 0
    
    for task in tasks:
        if task.project:
            tasks_with_projects += 1
        
        if re.match(project_pattern, task.title) and not task.project:
            remaining_embedded += 1
            print(f"  ⚠️  Still embedded: \"{task.title}\" (Project: {task.project})")
    
    print(f"\\n📊 Verification results:")
    print(f"  Tasks with project field: {tasks_with_projects}")
    print(f"  Tasks still with embedded projects: {remaining_embedded}")
    
    if remaining_embedded == 0:
        print("  ✅ Migration successful - no embedded projects remaining!")
    else:
        print(f"  ⚠️  {remaining_embedded} tasks still have embedded projects")
    
    return remaining_embedded == 0

if __name__ == '__main__':
    print("🚀 Starting project extraction migration...")
    updated_count = extract_projects_from_titles()
    success = verify_migration()
    
    if success:
        print("\\n🎉 Migration completed successfully!")
    else:
        print("\\n⚠️  Migration completed with some issues - please review the output above")

