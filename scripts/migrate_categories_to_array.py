#!/usr/bin/env python3
"""
Migration script to convert category field to categories array in the database
"""

import sqlite3
import json
import os
import sys

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DATABASE_PATH

def migrate_categories():
    """Migrate category field to categories array"""
    print("🔄 Starting categories migration...")
    
    # Check if database exists
    if not os.path.exists(DATABASE_PATH):
        print(f"❌ Database not found at {DATABASE_PATH}")
        return False
    
    # Backup the database
    backup_path = f"{DATABASE_PATH}.backup.categories"
    print(f"📋 Creating backup at {backup_path}")
    
    import shutil
    shutil.copy2(DATABASE_PATH, backup_path)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if categories column exists
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'categories' in columns:
            print("✅ Categories column already exists")
        else:
            # Add categories column
            print("➕ Adding categories column...")
            cursor.execute("ALTER TABLE tasks ADD COLUMN categories TEXT DEFAULT '[]'")
        
        # Migrate existing category data to categories array
        print("🔄 Migrating existing category data...")
        cursor.execute("SELECT id, category FROM tasks WHERE category IS NOT NULL AND category != ''")
        rows = cursor.fetchall()
        
        for task_id, category in rows:
            # Convert comma-separated string to JSON array
            if category:
                categories = [cat.strip() for cat in category.split(',') if cat.strip()]
                categories_json = json.dumps(categories)
                
                cursor.execute("UPDATE tasks SET categories = ? WHERE id = ?", (categories_json, task_id))
                print(f"  ✅ Migrated task {task_id}: '{category}' -> {categories}")
        
        # Remove old category column (optional - we'll keep it for now for safety)
        # cursor.execute("ALTER TABLE tasks DROP COLUMN category")
        
        conn.commit()
        print("✅ Categories migration completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = migrate_categories()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)

