#!/usr/bin/env python3
"""
Test script for LangGraph agent implementation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator.langgraph_orchestrator import LangGraphOrchestrator
import json

def test_langgraph_agent():
    """Test the LangGraph agent implementation"""
    print("🤖 Testing LangGraph Agent Implementation")
    print("=" * 50)
    
    try:
        # Initialize orchestrator
        orchestrator = LangGraphOrchestrator()
        print("✅ LangGraph orchestrator initialized")
        
        # Test input
        test_input = "Create a task to review the quarterly report"
        print(f"📝 Test input: {test_input}")
        
        # Run the agent
        result = orchestrator.run(
            input_text=test_input,
            session_id="test-session-123",
            domain="chat"
        )
        
        print("\n📊 Results:")
        print(f"Success: {result.get('success')}")
        print(f"Message: {result.get('message')}")
        print(f"Final Message: {result.get('final_message')}")
        
        if result.get('state_patch'):
            print(f"State Patch: {json.dumps(result['state_patch'], indent=2)}")
        
        print("\n✅ LangGraph agent test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_langgraph_agent()
    sys.exit(0 if success else 1)
