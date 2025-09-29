#!/usr/bin/env python3
"""
Debug script to show the exact synthesis prompt used
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator.langgraph_orchestrator import LangGraphOrchestrator
import json

def debug_synthesis():
    """Show the exact synthesis prompt used"""
    print("🔍 Debugging LangGraph Synthesis Process")
    print("=" * 50)
    
    # Initialize orchestrator
    orchestrator = LangGraphOrchestrator()
    
    # Simulate the state after planner and action execution
    mock_state = {
        "input_text": "Show me my tasks",
        "action_results": [
            {
                "name": "fetch_tasks",
                "ok": True,
                "result": {
                    "tasks": [
                        {"id": 1, "title": "Review quarterly report", "status": "open"},
                        {"id": 2, "title": "Mark 45 minutes as a ride", "status": "open"},
                        {"id": 3, "title": "PM meetup recap - AI and product management", "status": "open"}
                    ],
                    "count": 86,
                    "message": "Fetched 86 tasks"
                }
            }
        ]
    }
    
    # Load the synthesizer prompt from registry
    from config.prompts import get_synthesizer_prompt
    action_results_str = json.dumps(mock_state["action_results"], indent=2)
    full_prompt = get_synthesizer_prompt(mock_state["input_text"], action_results_str)
    
    print("📝 FULL SYNTHESIS PROMPT SENT TO LLM:")
    print("=" * 50)
    print(full_prompt)
    print("=" * 50)
    
    print("\n📊 FETCH_TASKS RESPONSE DATA:")
    print("=" * 30)
    print(json.dumps(mock_state["action_results"][0]["result"], indent=2))

if __name__ == "__main__":
    debug_synthesis()
