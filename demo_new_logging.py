#!/usr/bin/env python3
"""
Demo script showing the new agent logging system with thread_id and step tracking
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.task_db import AgentStepDB
from orchestrator.langgraph_orchestrator import LangGraphOrchestrator
from database import get_connection

def demo_logging_system():
    """Demonstrate the new agent logging system"""
    print("🚀 Demo: New Agent Logging System")
    print("=" * 50)

    # Initialize orchestrator
    orchestrator = LangGraphOrchestrator()

    # Test input
    test_input = "What tasks should I focus on today?"
    session_id = "demo-session-123"

    print(f"📝 Processing input: '{test_input}'")
    print(f"🔗 Session ID: {session_id}")
    print()

    # Run the orchestrator (this will create database entries)
    try:
        result = orchestrator.run(test_input, session_id)

        print("✅ Orchestrator completed successfully")
        print(f"📊 Thread ID: {result.get('thread_id')}")
        print(f"🔢 Current Step: {result.get('current_step')}")
        print()

        # Show the steps that were logged
        if result.get('thread_id'):
            steps = AgentStepDB.get_by_thread_id(result['thread_id'])
            print(f"📋 Database now contains {len(steps)} steps for this thread:")
            print()

            for step in steps:
                print(f"Step {step.step_number}: {step.step_type}")
                print(f"  Timestamp: {step.timestamp}")
                print(f"  Thread ID: {step.thread_id}")
                print(f"  Input: {step.input_data}")
                print(f"  Output: {step.output_data}")

                if step.rendered_prompt:
                    print(f"  Prompt: {step.rendered_prompt[:100]}...")
                if step.llm_output:
                    print(f"  LLM Output: {step.llm_output[:100]}...")

                print(f"  Error: {step.error}")
                print()

        # Show all threads
        print("🌐 All conversation threads:")
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
                print(f"  {thread[0]}: {thread[1]} steps ({thread[2]} to {thread[3]})")

    except Exception as e:
        print(f"❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    demo_logging_system()
