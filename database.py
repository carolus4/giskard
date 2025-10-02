"""
Database configuration and initialization for Giskard
"""
import sqlite3
import os
import time
import threading
from datetime import datetime
from typing import Optional
from contextlib import contextmanager

# Database configuration
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data', 'giskard.db')

# Thread-local storage for database connections
_local = threading.local()

def init_database():
    """Initialize the SQLite database with the Task table"""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    cursor = conn.cursor()
    
    # Enable WAL mode for better concurrency
    cursor.execute('PRAGMA journal_mode=WAL')
    
    # Set busy timeout to handle locks gracefully
    cursor.execute('PRAGMA busy_timeout=30000')  # 30 seconds
    
    # Create the tasks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
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

    # Create index for efficient sorting
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_tasks_sort_key ON tasks(sort_key)
    ''')

    # Create index for status filtering
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
    ''')

    # Create the agent_steps table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT NOT NULL,
            step_number INTEGER NOT NULL,
            step_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            input_data TEXT DEFAULT '{}',
            output_data TEXT DEFAULT '{}',
            rendered_prompt TEXT,
            llm_input TEXT DEFAULT '{}',
            llm_output TEXT,
            error TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create indexes for efficient querying
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_agent_steps_thread_id ON agent_steps(thread_id)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_agent_steps_step_number ON agent_steps(step_number)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_agent_steps_step_type ON agent_steps(step_type)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_agent_steps_timestamp ON agent_steps(timestamp)
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"✅ Database initialized at {DATABASE_PATH}")

@contextmanager
def get_connection():
    """Get a database connection with proper error handling and retries"""
    conn = None
    max_retries = 3
    retry_delay = 0.1
    
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(
                DATABASE_PATH, 
                timeout=30.0,
                check_same_thread=False
            )
            # Enable WAL mode for better concurrency
            conn.execute('PRAGMA journal_mode=WAL')
            # Set busy timeout to handle locks gracefully
            conn.execute('PRAGMA busy_timeout=30000')  # 30 seconds
            # Enable foreign keys
            conn.execute('PRAGMA foreign_keys=ON')
            break
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                print(f"Database locked, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                continue
            else:
                raise e
    
    if conn is None:
        raise sqlite3.OperationalError("Failed to connect to database after multiple retries")
    
    try:
        yield conn
    finally:
        if conn:
            conn.close()

def get_next_sort_key():
    """Get the next available sort key for new tasks with gaps for efficient reordering"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT MAX(sort_key) FROM tasks')
        result = cursor.fetchone()
        max_sort_key = result[0] if result[0] is not None else 0
        # Use gaps of 1000 for efficient reordering
        return max_sort_key + 1000

if __name__ == '__main__':
    init_database()
