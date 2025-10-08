#!/usr/bin/env python3
"""
Test script for Langfuse integration with Giskard agent
"""
import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from orchestrator.langgraph_orchestrator import LangGraphOrchestrator
from config.langfuse_config import langfuse_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_langfuse_configuration():
    """Test Langfuse configuration"""
    print("🔧 Testing Langfuse Configuration...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file found")
    else:
        print("⚠️  .env file not found (using environment variables)")
    
    if langfuse_config.enabled:
        print("✅ Langfuse is enabled and configured")
        print(f"   Host: {langfuse_config.host}")
        print(f"   Public Key: {langfuse_config.public_key[:10]}...")
        return True
    else:
        print("❌ Langfuse is not configured")
        print("   Options:")
        print("   1. Create .env file: cp env.example .env")
        print("   2. Set environment variables: export LANGFUSE_PUBLIC_KEY=...")
        return False


def test_callback_handler():
    """Test Langfuse callback handler creation"""
    print("\n🔧 Testing Callback Handler Creation...")
    
    handler = langfuse_config.get_callback_handler(
        trace_id="test-trace-123",
        user_id="test-user"
    )
    
    if handler:
        print("✅ Callback handler created successfully")
        return True
    else:
        print("❌ Failed to create callback handler")
        return False


def test_agent_with_langfuse():
    """Test the agent with Langfuse tracing"""
    print("\n🤖 Testing Agent with Langfuse Tracing...")
    
    try:
        # Initialize the orchestrator
        orchestrator = LangGraphOrchestrator()
        
        # Test input
        test_input = "Create a task to review the quarterly report"
        session_id = f"test-session-{int(datetime.now().timestamp())}"
        
        print(f"   Input: {test_input}")
        print(f"   Session ID: {session_id}")
        
        # Run the agent
        result = orchestrator.run(
            input_text=test_input,
            session_id=session_id,
            domain="test"
        )
        
        print(f"   Success: {result.get('success')}")
        print(f"   Trace ID: {result.get('trace_id')}")
        print(f"   Final Message: {result.get('final_message', '')[:100]}...")
        
        if result.get('success'):
            print("✅ Agent execution completed successfully")
            return True
        else:
            print("❌ Agent execution failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during agent test: {str(e)}")
        return False


def test_router_with_langfuse():
    """Test the router with Langfuse tracing"""
    print("\n🧭 Testing Router with Langfuse Tracing...")
    
    try:
        from orchestrator.tools.router import Router
        
        # Initialize router
        router = Router()
        
        # Test input
        test_input = "Add a task to my todo list"
        trace_id = f"router-test-{int(datetime.now().timestamp())}"
        
        print(f"   Input: {test_input}")
        print(f"   Trace ID: {trace_id}")
        
        # Test router with Langfuse tracing
        result = router.plan_actions(
            user_input=test_input,
            trace_id=trace_id,
            user_id="test-user"
        )
        
        print(f"   Tool Name: {result.get('tool_name')}")
        print(f"   Assistant Text: {result.get('assistant_text', '')[:100]}...")
        
        print("✅ Router execution completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error during router test: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("🚀 Starting Langfuse Integration Tests")
    print("=" * 50)
    
    tests = [
        test_langfuse_configuration,
        test_callback_handler,
        test_router_with_langfuse,
        test_agent_with_langfuse
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Langfuse integration is working correctly.")
        print("\n📝 Next Steps:")
        print("1. Set up your Langfuse account at https://cloud.langfuse.com")
        print("2. Get your API keys from the Langfuse dashboard")
        print("3. Set environment variables:")
        print("   export LANGFUSE_PUBLIC_KEY='your-public-key'")
        print("   export LANGFUSE_SECRET_KEY='your-secret-key'")
        print("4. Run your Giskard agent and check the Langfuse dashboard for traces")
    else:
        print("⚠️  Some tests failed. Check the configuration and try again.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
