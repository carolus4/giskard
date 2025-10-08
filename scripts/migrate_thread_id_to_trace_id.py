#!/usr/bin/env python3
"""
Migration script to rename thread_id to trace_id in the database.
This script handles the database schema change and data migration.
"""

import sqlite3
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def migrate_database():
    """Migrate the database schema from thread_id to trace_id."""
    db_path = project_root / "data" / "giskard.db"
    
    if not db_path.exists():
        print("❌ Database file not found. Please ensure the database exists.")
        return False
    
    print(f"🔄 Starting migration of thread_id to trace_id in {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if the agent_steps table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='agent_steps'")
        if not cursor.fetchone():
            print("❌ agent_steps table not found. Nothing to migrate.")
            return False
        
        # Check if thread_id column exists
        cursor.execute("PRAGMA table_info(agent_steps)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'thread_id' not in columns:
            print("❌ thread_id column not found. Migration may have already been completed.")
            return False
        
        if 'trace_id' in columns:
            print("❌ trace_id column already exists. Migration may have already been completed.")
            return False
        
        print("📊 Current table structure:")
        for column in columns:
            print(f"  - {column}")
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Step 1: Add the new trace_id column
            print("🔄 Adding trace_id column...")
            cursor.execute("ALTER TABLE agent_steps ADD COLUMN trace_id TEXT")
            
            # Step 2: Copy data from thread_id to trace_id
            print("🔄 Copying data from thread_id to trace_id...")
            cursor.execute("UPDATE agent_steps SET trace_id = thread_id")
            
            # Step 3: Create new index on trace_id
            print("🔄 Creating index on trace_id...")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_agent_steps_trace_id ON agent_steps(trace_id)")
            
            # Step 4: Drop the old index on thread_id
            print("🔄 Dropping old index on thread_id...")
            cursor.execute("DROP INDEX IF EXISTS idx_agent_steps_thread_id")
            
            # Step 5: Drop the thread_id column
            print("🔄 Dropping thread_id column...")
            # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
            cursor.execute("""
                CREATE TABLE agent_steps_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    trace_id TEXT NOT NULL,
                    step_number INTEGER NOT NULL,
                    step_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    input_data TEXT DEFAULT '{}',
                    output_data TEXT DEFAULT '{}',
                    rendered_prompt TEXT,
                    llm_input TEXT DEFAULT '{}',
                    llm_output TEXT,
                    error TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    llm_model TEXT
                )
            """)
            
            # Copy data to new table
            cursor.execute("""
                INSERT INTO agent_steps_new (id, trace_id, step_number, step_type, timestamp, input_data, output_data, rendered_prompt, llm_input, llm_output, error, created_at, llm_model)
                SELECT id, trace_id, step_number, step_type, timestamp, input_data, output_data, rendered_prompt, llm_input, llm_output, error, created_at, llm_model
                FROM agent_steps
            """)
            
            # Drop old table and rename new one
            cursor.execute("DROP TABLE agent_steps")
            cursor.execute("ALTER TABLE agent_steps_new RENAME TO agent_steps")
            
            # Commit the transaction
            cursor.execute("COMMIT")
            
            print("✅ Migration completed successfully!")
            
            # Verify the migration
            cursor.execute("PRAGMA table_info(agent_steps)")
            new_columns = [column[1] for column in cursor.fetchall()]
            print("📊 New table structure:")
            for column in new_columns:
                print(f"  - {column}")
            
            # Check data integrity
            cursor.execute("SELECT COUNT(*) FROM agent_steps")
            count = cursor.fetchone()[0]
            print(f"📊 Total records migrated: {count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during migration: {e}")
            cursor.execute("ROLLBACK")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False
    
    finally:
        if 'conn' in locals():
            conn.close()

def main():
    """Main migration function."""
    print("🚀 Starting thread_id to trace_id migration...")
    
    success = migrate_database()
    
    if success:
        print("✅ Migration completed successfully!")
        print("📝 Next steps:")
        print("  1. Update your code to use 'trace_id' instead of 'thread_id'")
        print("  2. Test your application to ensure everything works correctly")
        print("  3. Consider backing up your database before deploying to production")
    else:
        print("❌ Migration failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
