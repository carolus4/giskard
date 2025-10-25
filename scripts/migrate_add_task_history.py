#!/usr/bin/env python3
"""
Migration script to add task_history table for tracking task changes
"""
import os
import sys
import sqlite3
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection, DATABASE_PATH

def create_task_history_table():
    """Create the task_history table"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Create the task_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_at TEXT NOT NULL,
                change_type TEXT NOT NULL CHECK (change_type IN ('create','update','delete','status_change')),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        ''')

        # Create indexes for efficient querying
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_task_history_task_id ON task_history(task_id)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_task_history_changed_at ON task_history(changed_at)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_task_history_field_name ON task_history(field_name)
        ''')

        conn.commit()
        print("✅ Created task_history table with indexes")

def verify_migration():
    """Verify the migration was successful"""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if task_history table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='task_history'
        """)
        table_exists = cursor.fetchone()

        if table_exists:
            print("✅ task_history table exists")

            # Check indexes
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='index' AND tbl_name='task_history'
            """)
            indexes = cursor.fetchall()
            print(f"✅ Created {len(indexes)} indexes:")
            for idx in indexes:
                print(f"   - {idx[0]}")
        else:
            print("❌ task_history table not found")
            return False

        return True

def main():
    """Run the migration"""
    print("🚀 Starting migration to add task_history table")
    print("=" * 60)

    # Backup existing database
    backup_path = f"{DATABASE_PATH}.backup.{int(datetime.now().timestamp())}"
    print(f"📦 Creating backup: {backup_path}")

    import shutil
    shutil.copy2(DATABASE_PATH, backup_path)
    print("✅ Database backup created")

    try:
        # Create task_history table
        print("\n🔧 Creating task_history table...")
        create_task_history_table()

        # Verify migration
        print("\n✅ Verifying migration...")
        if verify_migration():
            print("\n🎉 Migration completed successfully!")
            print(f"📦 Backup available at: {backup_path}")
        else:
            print("\n❌ Migration verification failed")
            print(f"📦 Restore from backup: {backup_path}")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print(f"📦 Restore from backup: {backup_path}")
        raise

if __name__ == "__main__":
    main()
