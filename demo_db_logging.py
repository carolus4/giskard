#!/usr/bin/env python3
"""
Demo script showing the new agent logging database functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.task_db import AgentStepDB
from database import get_connection

def demo_database_logging():
    """Demonstrate the new agent logging database system"""
    print("🚀 Demo: New Agent Logging Database System")
    print("=" * 60)

    # Create some sample steps to demonstrate the system
    print("📝 Creating sample conversation steps...")

    # Simulate a conversation thread
    thread_id = "demo-conversation-456"

    steps_data = [
        {
            "step_type": "workflow_start",
            "input_data": {"input_text": "What tasks should I work on?", "session_id": thread_id},
            "output_data": {}
        },
        {
            "step_type": "ingest_user_input",
            "input_data": {"input_text": "What tasks should I work on?"},
            "output_data": {"messages_count": 1, "user_message_added": True}
        },
        {
            "step_type": "planner_llm",
            "input_data": {"input_text": "What tasks should I work on?", "messages_count": 1},
            "output_data": {"llm_response": "Let me check your tasks...", "parsing_success": True},
            "rendered_prompt": "You are a helpful assistant. Help the user decide what to focus on based on their current tasks.",
            "llm_input": {"messages": ["System prompt", "User: What tasks should I work on?"]},
            "llm_output": "Let me check your tasks..."
        },
        {
            "step_type": "action_exec",
            "input_data": {"actions_to_execute": [{"name": "fetch_tasks", "args": {}}]},
            "output_data": {"action_results": [{"name": "fetch_tasks", "ok": True, "result": {"tasks": []}}]}
        },
        {
            "step_type": "synthesizer_llm",
            "input_data": {"action_results": [], "input_text": "What tasks should I work on?"},
            "output_data": {"final_message": "You have no pending tasks. Great job staying on top of things!", "synthesis_success": True},
            "rendered_prompt": "Based on the action results, provide a helpful response to the user.",
            "llm_input": {"messages": ["System prompt"]},
            "llm_output": "You have no pending tasks. Great job staying on top of things!"
        }
    ]

    # Create steps in database
    for i, step_data in enumerate(steps_data):
        step = AgentStepDB.create(
            thread_id=thread_id,
            step_number=i + 1,
            **step_data
        )
        print(f"  ✅ Created step {i+1}: {step.step_type}")

    print()
    print("📊 Thread Overview:")
    steps = AgentStepDB.get_by_thread_id(thread_id)

    for step in steps:
        print(f"  Step {step.step_number}: {step.step_type} - {step.timestamp}")

    print()
    print("🔍 Detailed Step Information:")

    for step in steps:
        print(f"\n--- Step {step.step_number}: {step.step_type} ---")
        print(f"Thread ID: {step.thread_id}")
        print(f"Timestamp: {step.timestamp}")
        print(f"Input: {step.input_data}")
        print(f"Output: {step.output_data}")

        if step.rendered_prompt:
            print(f"Prompt: {step.rendered_prompt[:80]}...")
        if step.llm_input:
            print(f"LLM Input: {step.llm_input}")
        if step.llm_output:
            print(f"LLM Output: {step.llm_output[:80]}...")
        if step.error:
            print(f"Error: {step.error}")

    print()
    print("🌐 All Conversation Threads:")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT thread_id, COUNT(*) as step_count, MIN(timestamp) as first, MAX(timestamp) as last
            FROM agent_steps
            GROUP BY thread_id
            ORDER BY last DESC
        ''')

        threads = cursor.fetchall()
        for thread in threads:
            print(f"  {thread[0]}: {thread[1]} steps ({thread[2][:19]} to {thread[3][:19]})")

    print()
    print("📈 Database Statistics:")
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM agent_steps')
        total_steps = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(DISTINCT thread_id) FROM agent_steps')
        total_threads = cursor.fetchone()[0]

    print(f"  Total steps: {total_steps}")
    print(f"  Total threads: {total_threads}")
    print()
    print("✅ Demo completed successfully!")

if __name__ == '__main__':
    demo_database_logging()
