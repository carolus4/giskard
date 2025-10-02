#!/usr/bin/env python3
"""
Migration script to migrate existing agent logs from JSON to database
"""
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.task_db import AgentStepDB

def migrate_agent_logs():
    """Migrate existing agent logs from JSON file to database"""
    log_file = '/Users/charlesdupont/Dev/giskard/data/agent_logs.json'

    if not os.path.exists(log_file):
        print("❌ No agent logs file found to migrate")
        return False

    try:
        # Read existing logs
        with open(log_file, 'r') as f:
            logs = json.load(f)

        print(f"📊 Found {len(logs)} log entries to migrate")

        # Group logs by session_id (which will become thread_id)
        thread_groups = {}
        for log in logs:
            session_id = log.get('input', {}).get('session_id', 'legacy-thread')
            if session_id not in thread_groups:
                thread_groups[session_id] = []
            thread_groups[session_id].append(log)

        migrated_count = 0

        for thread_id, thread_logs in thread_groups.items():
            print(f"🔄 Migrating thread {thread_id} ({len(thread_logs)} steps)")

            for i, log in enumerate(thread_logs):
                try:
                    # Extract data from old format
                    step_type = log.get('node', 'unknown')
                    input_data = log.get('input', {})
                    output_data = log.get('output', {})

                    # Create database entry
                    AgentStepDB.create(
                        thread_id=thread_id,
                        step_number=i + 1,
                        step_type=step_type,
                        input_data=input_data,
                        output_data=output_data
                    )

                    migrated_count += 1

                except Exception as e:
                    print(f"⚠️  Failed to migrate step {i+1} in thread {thread_id}: {e}")

        print(f"✅ Successfully migrated {migrated_count} log entries")
        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Starting agent logs migration...")
    success = migrate_agent_logs()
    if success:
        print("🎉 Migration completed successfully!")
    else:
        print("💥 Migration failed!")
        sys.exit(1)
