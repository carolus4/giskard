#!/usr/bin/env python3
"""
DEPRECATED: Migration script to move data from todo.txt to SQLite database

This script has already been run and is no longer needed.
The migration from todo.txt to SQLite has been completed.
"""
import os
import sys
import re
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_database
from models.task_db import TaskDB
from models.task import Task, TaskCollection
from utils.file_manager import TodoFileManager


def parse_canonical_format(text: str) -> tuple[str, str, str, list[str]]:
    """Parse the canonical format to extract project, title, description, and categories"""
    
    # Extract project name
    project_match = re.search(r'project:"([^"]*)"|project:(\S+)', text)
    project = ""
    if project_match:
        project = project_match.group(1) or project_match.group(2)
        # Remove project tag from text
        text = re.sub(r'project:"[^"]*"|project:\S+', '', text).strip()
    
    # Extract note/description
    note_match = re.search(r'note:"([^"]*)"|note:(\S+)', text)
    description = ""
    if note_match:
        description = note_match.group(1) or note_match.group(2)
        # Remove note tag from text
        text = re.sub(r'note:"[^"]*"|note:\S+', '', text).strip()
    
    # Extract categories
    categories_match = re.search(r'categories:"([^"]*)"|categories:(\S+)', text)
    categories = []
    if categories_match:
        categories_str = categories_match.group(1) or categories_match.group(2)
        if categories_str and categories_str != '""':
            categories = [cat.strip() for cat in categories_str.split(',') if cat.strip()]
        # Remove categories tag from text
        text = re.sub(r'categories:"[^"]*"|categories:\S+', '', text).strip()
    
    # Extract other tags (status, time_minutes, etc.) and remove them
    text = re.sub(r'\s+(?:status|time_minutes|created):[^\s]+', '', text).strip()
    
    # What's left is the title
    title = text.strip()
    
    # Format title as [Project] Title if project exists
    if project and project != '""':
        title = f"[{project}] {title}"
    
    return title, description, project, categories


def migrate_tasks():
    """Migrate tasks from todo.txt to SQLite database"""
    print("🚀 Starting migration from todo.txt to SQLite...")
    
    # Initialize database
    init_database()
    
    # Load existing tasks from todo.txt
    file_manager = TodoFileManager()
    collection = file_manager.load_tasks()
    
    print(f"📄 Found {len(collection.tasks)} tasks in todo.txt")
    
    # Migrate each task
    migrated_count = 0
    skipped_count = 0
    
    for task in collection.tasks:
        try:
            # Parse the task text to extract components
            if "project:" in task.title:
                # This is in canonical format
                title, description, project, categories = parse_canonical_format(task.title)
            else:
                # Legacy format - use as is
                title = task.title
                description = task.description
                project = None
                categories = task.categories or []
            
            # Create new database task
            db_task = TaskDB.create(
                title=title,
                description=description,
                project=project,
                categories=categories
            )
            
            # Set status after creation
            if task.status == 'done':
                db_task.mark_done()
            elif task.status == 'in_progress':
                db_task.mark_in_progress()
            # 'open' is the default status
            
            # Set timestamps based on status
            if task.status == 'done' and task.completion_date:
                # Parse completion date and set completed_at
                try:
                    completion_date = datetime.strptime(task.completion_date, '%Y-%m-%d')
                    db_task.completed_at = completion_date.isoformat()
                    db_task.save()
                except ValueError:
                    # If date parsing fails, use current time
                    db_task.completed_at = datetime.now().isoformat()
                    db_task.save()
            elif task.status == 'in_progress':
                # Set started_at to a reasonable time (created_at + 1 hour)
                created_time = datetime.fromisoformat(db_task.created_at)
                started_time = created_time.replace(hour=created_time.hour + 1)
                db_task.started_at = started_time.isoformat()
                db_task.save()
            
            migrated_count += 1
            print(f"✅ Migrated: {title[:50]}...")
            
        except Exception as e:
            print(f"❌ Failed to migrate task '{task.title[:50]}...': {e}")
            skipped_count += 1
            continue
    
    print(f"\n🎉 Migration completed!")
    print(f"✅ Successfully migrated: {migrated_count} tasks")
    print(f"❌ Skipped: {skipped_count} tasks")
    
    # Verify migration
    open_tasks, in_progress_tasks, done_tasks = TaskDB.get_by_status()
    print(f"\n📊 Database verification:")
    print(f"   Open tasks: {len(open_tasks)}")
    print(f"   In progress tasks: {len(in_progress_tasks)}")
    print(f"   Done tasks: {len(done_tasks)}")
    print(f"   Total: {len(open_tasks) + len(in_progress_tasks) + len(done_tasks)}")
    
    return migrated_count, skipped_count


def backup_todo_file():
    """Create a backup of the original todo.txt file"""
    todo_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'todo.txt')
    backup_file = f"{todo_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if os.path.exists(todo_file):
        import shutil
        shutil.copy2(todo_file, backup_file)
        print(f"📦 Created backup: {backup_file}")
        return backup_file
    else:
        print("⚠️  No todo.txt file found to backup")
        return None


if __name__ == '__main__':
    print("🔄 Giskard Migration Tool")
    print("=" * 50)
    
    # Create backup first
    backup_file = backup_todo_file()
    
    # Run migration
    migrated, skipped = migrate_tasks()
    
    if migrated > 0:
        print(f"\n✨ Migration successful! {migrated} tasks migrated to SQLite.")
        print("🔄 You can now update your app to use the new database API.")
        if backup_file:
            print(f"💾 Original data backed up to: {backup_file}")
    else:
        print("\n⚠️  No tasks were migrated. Check the error messages above.")
