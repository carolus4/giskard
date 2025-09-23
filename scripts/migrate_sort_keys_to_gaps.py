#!/usr/bin/env python3
"""
Migration script to convert existing sort keys to use gaps for efficient reordering
"""

import sqlite3
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DATABASE_PATH

def migrate_sort_keys():
    """Migrate sort keys to use gaps for efficient reordering"""
    print("🔄 Starting sort key gaps migration...")
    
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database not found at {DATABASE_PATH}")
        return False
    
    # Backup the database
    backup_path = f"{DATABASE_PATH}.backup.sort_keys"
    print(f"📋 Creating backup at {backup_path}")
    
    import shutil
    shutil.copy2(DATABASE_PATH, backup_path)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Get all tasks ordered by current sort_key
        cursor.execute('''
            SELECT id, sort_key, status 
            FROM tasks 
            ORDER BY sort_key ASC
        ''')
        tasks = cursor.fetchall()
        
        if not tasks:
            print("✅ No tasks to migrate")
            return True
        
        print(f"📝 Found {len(tasks)} tasks to migrate")
        
        # Update sort keys with gaps of 1000
        for i, (task_id, old_sort_key, status) in enumerate(tasks):
            new_sort_key = (i + 1) * 1000
            cursor.execute('''
                UPDATE tasks 
                SET sort_key = ?, updated_at = ?
                WHERE id = ?
            ''', (new_sort_key, '2025-09-23T11:00:00.000000', task_id))
            
            print(f"  ✅ Task {task_id} ({status}): {old_sort_key} -> {new_sort_key}")
        
        conn.commit()
        print("✅ Sort key gaps migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_sort_keys()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)

