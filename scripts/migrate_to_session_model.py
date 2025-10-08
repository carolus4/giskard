#!/usr/bin/env python3
"""
Migration script to convert from trace_id-based model to session-based model
"""
import os
import sys
import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_connection, DATABASE_PATH

def create_session_tables():
    """Create new session-based tables"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Create sessions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT DEFAULT '{}'
            )
        ''')
        
        # Create traces table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS traces (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                user_message TEXT NOT NULL,
                assistant_response TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT DEFAULT 'in_progress',
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        
        # Update agent_steps table to include session_id
        cursor.execute('''
            ALTER TABLE agent_steps ADD COLUMN session_id TEXT
        ''')
        
        # Create indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_traces_session_id ON traces(session_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_traces_created_at ON traces(created_at)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_agent_steps_session_id ON agent_steps(session_id)
        ''')
        
        conn.commit()
        print("✅ Created session-based tables")

def migrate_existing_data():
    """Migrate existing agent_steps data to new session-based model"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Get all unique trace_ids from existing data
        cursor.execute('SELECT DISTINCT trace_id FROM agent_steps ORDER BY timestamp ASC')
        trace_ids = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Found {len(trace_ids)} unique trace_ids to migrate")
        
        # Group trace_ids by session (using a simple heuristic)
        sessions = {}
        for trace_id in trace_ids:
            # Extract session identifier from trace_id
            # Current format: "chat-1759940138959-smagnz1tz"
            if trace_id.startswith('chat-'):
                # Extract the timestamp part as session identifier
                parts = trace_id.split('-')
                if len(parts) >= 2:
                    session_key = f"session-{parts[1]}"  # Use timestamp as session
                else:
                    session_key = f"session-{trace_id}"
            else:
                # For other formats, use the trace_id as session
                session_key = f"session-{trace_id}"
            
            if session_key not in sessions:
                sessions[session_key] = []
            sessions[session_key].append(trace_id)
        
        print(f"📊 Grouped into {len(sessions)} sessions")
        
        # Create sessions and traces
        for session_id, trace_list in sessions.items():
            # Create session
            session_uuid = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO sessions (id, user_id, created_at, updated_at, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (session_uuid, None, created_at, created_at, json.dumps({
                "original_session_id": session_id,
                "migrated_at": created_at,
                "trace_count": len(trace_list)
            })))
            
            # Create traces for this session
            for trace_id in trace_list:
                # Get the first step to extract user message
                cursor.execute('''
                    SELECT input_data, timestamp FROM agent_steps 
                    WHERE trace_id=? AND step_type='ingest_user_input'
                    ORDER BY step_number ASC LIMIT 1
                ''', (trace_id,))
                
                first_step = cursor.fetchone()
                user_message = "Unknown message"
                created_at = datetime.now().isoformat()
                
                if first_step:
                    input_data = json.loads(first_step[0]) if first_step[0] else {}
                    user_message = input_data.get('input_text', 'Unknown message')
                    created_at = first_step[1]
                
                # Get the last step to extract assistant response
                cursor.execute('''
                    SELECT output_data FROM agent_steps 
                    WHERE trace_id=? AND step_type='synthesizer_llm'
                    ORDER BY step_number DESC LIMIT 1
                ''', (trace_id,))
                
                last_step = cursor.fetchone()
                assistant_response = None
                
                if last_step:
                    output_data = json.loads(last_step[0]) if last_step[0] else {}
                    assistant_response = output_data.get('final_message', '')
                
                # Create trace
                trace_uuid = str(uuid.uuid4())
                cursor.execute('''
                    INSERT INTO traces (id, session_id, user_message, assistant_response, 
                                     created_at, completed_at, status, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (trace_uuid, session_uuid, user_message, assistant_response,
                      created_at, created_at, 'completed', json.dumps({
                          "original_trace_id": trace_id,
                          "migrated_at": created_at
                      })))
                
                # Update agent_steps to include session_id
                cursor.execute('''
                    UPDATE agent_steps SET session_id=? WHERE trace_id=?
                ''', (session_uuid, trace_id))
        
        conn.commit()
        print("✅ Migrated existing data to session-based model")

def verify_migration():
    """Verify the migration was successful"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Check sessions
        cursor.execute('SELECT COUNT(*) FROM sessions')
        session_count = cursor.fetchone()[0]
        print(f"📊 Sessions created: {session_count}")
        
        # Check traces
        cursor.execute('SELECT COUNT(*) FROM traces')
        trace_count = cursor.fetchone()[0]
        print(f"📊 Traces created: {trace_count}")
        
        # Check agent_steps with session_id
        cursor.execute('SELECT COUNT(*) FROM agent_steps WHERE session_id IS NOT NULL')
        steps_with_session = cursor.fetchone()[0]
        print(f"📊 Agent steps with session_id: {steps_with_session}")
        
        # Check for orphaned steps
        cursor.execute('SELECT COUNT(*) FROM agent_steps WHERE session_id IS NULL')
        orphaned_steps = cursor.fetchone()[0]
        print(f"📊 Orphaned agent steps: {orphaned_steps}")
        
        if orphaned_steps > 0:
            print("⚠️  Warning: Some agent steps were not migrated")
        else:
            print("✅ All agent steps successfully migrated")

def main():
    """Run the migration"""
    print("🚀 Starting migration to session-based data model")
    print("=" * 60)
    
    # Backup existing database
    backup_path = f"{DATABASE_PATH}.backup.{int(datetime.now().timestamp())}"
    print(f"📦 Creating backup: {backup_path}")
    
    import shutil
    shutil.copy2(DATABASE_PATH, backup_path)
    print("✅ Database backup created")
    
    try:
        # Create new tables
        print("\n🔧 Creating session-based tables...")
        create_session_tables()
        
        # Migrate existing data
        print("\n📊 Migrating existing data...")
        migrate_existing_data()
        
        # Verify migration
        print("\n✅ Verifying migration...")
        verify_migration()
        
        print("\n🎉 Migration completed successfully!")
        print(f"📦 Backup available at: {backup_path}")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print(f"📦 Restore from backup: {backup_path}")
        raise

if __name__ == "__main__":
    main()
