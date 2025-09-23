#!/usr/bin/env python3
"""
Migration script to remove the old 'category' column from the tasks table
Since we now use 'categories' (plural) as a JSON array, the old 'category' column is no longer needed.
"""
import os
import sys
import sqlite3
from datetime import datetime

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection

def remove_old_category_column():
    """Remove the old 'category' column from the tasks table"""
    print("🗑️  Removing old 'category' column from tasks table...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # First, let's verify the current schema
        cursor.execute('PRAGMA table_info(tasks)')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'category' not in column_names:
            print("✅ Old 'category' column already removed")
            return
        
        print(f"📋 Current columns: {column_names}")
        
        # Create a backup of the current table
        backup_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_table = f"tasks_backup_before_category_removal_{backup_timestamp}"
        
        print(f"💾 Creating backup table: {backup_table}")
        cursor.execute(f'CREATE TABLE {backup_table} AS SELECT * FROM tasks')
        
        # Create new table without the category column
        print("🔨 Creating new table without 'category' column...")
        cursor.execute('''
            CREATE TABLE tasks_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT NOT NULL CHECK (status IN ('open','in_progress','done')),
                sort_key INTEGER NOT NULL,
                project TEXT DEFAULT NULL,
                categories TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT
            )
        ''')
        
        # Copy data from old table to new table (excluding category column)
        print("📋 Copying data to new table...")
        cursor.execute('''
            INSERT INTO tasks_new (id, title, description, status, sort_key, project, categories, created_at, updated_at, started_at, completed_at)
            SELECT id, title, description, status, sort_key, project, categories, created_at, updated_at, started_at, completed_at
            FROM tasks
        ''')
        
        # Drop old table and rename new table
        print("🔄 Replacing old table with new table...")
        cursor.execute('DROP TABLE tasks')
        cursor.execute('ALTER TABLE tasks_new RENAME TO tasks')
        
        # Recreate the index
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_tasks_sort_key ON tasks(sort_key)
        ''')
        
        # Verify the new schema
        cursor.execute('PRAGMA table_info(tasks)')
        new_columns = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns]
        
        print(f"✅ New columns: {new_column_names}")
        
        # Verify data integrity
        cursor.execute('SELECT COUNT(*) FROM tasks')
        task_count = cursor.fetchone()[0]
        print(f"✅ Task count after migration: {task_count}")
        
        conn.commit()
        print("✅ Successfully removed old 'category' column!")
        print(f"💾 Backup table created: {backup_table}")
        
    except Exception as e:
        print(f"❌ Error during migration: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    remove_old_category_column()
