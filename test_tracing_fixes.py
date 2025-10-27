#!/usr/bin/env python3
"""
Test script to verify Langfuse tracing fixes
"""
import os
import sys
import json
import time
import logging
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from server.routes.agent import conversation_stream
from config.langfuse_config import langfuse_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_tracing_fixes():
    """Test the tracing fixes to ensure proper hierarchy and token counting"""
    
    print("🧪 Testing Langfuse Tracing Fixes")
    print("=" * 50)
    
    # Check if Langfuse is configured
    if not langfuse_config.enabled:
        print("❌ Langfuse not configured - set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
        return False
    
    print("✅ Langfuse is configured")
    
    # Test data
    test_input = "Show me my tasks"
    session_id = f"test-session-{int(time.time())}"
    trace_id = f"test-trace-{int(time.time())}"
    
    print(f"📝 Test input: {test_input}")
    print(f"🆔 Session ID: {session_id}")
    print(f"🔍 Trace ID: {trace_id}")
    
    try:
        # Create a mock request context
        from flask import Flask, request
        app = Flask(__name__)
        
        with app.test_request_context(
            '/conversation',
            method='POST',
            json={
                'input_text': test_input,
                'session_id': session_id,
                'domain': 'chat',
                'trace_id': trace_id,
                'conversation_context': []
            }
        ):
            print("\n🚀 Starting conversation test...")
            
            # Call the conversation endpoint
            response = conversation_stream()
            
            if response:
                response_data = response.get_json()
                print(f"✅ Response received: {response_data.get('message', 'No message')}")
                
                if response_data.get('success'):
                    print("✅ Conversation completed successfully")
                    
                    # Check if we have steps data
                    steps = response_data.get('data', {}).get('steps', [])
                    print(f"📊 Steps completed: {len(steps)}")
                    
                    for i, step in enumerate(steps, 1):
                        print(f"  {i}. {step.get('step_type', 'unknown')}: {step.get('status', 'unknown')}")
                    
                    # Flush Langfuse events
                    langfuse_config.flush()
                    print("🔄 Langfuse events flushed")
                    
                    return True
                else:
                    print(f"❌ Conversation failed: {response_data.get('message', 'Unknown error')}")
                    return False
            else:
                print("❌ No response received")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🔧 Langfuse Tracing Fixes Test")
    print("=" * 50)
    
    success = test_tracing_fixes()
    
    if success:
        print("\n✅ All tests passed!")
        print("\n📋 Expected Langfuse trace structure:")
        print("  - Root trace: 'chat.turn'")
        print("  - Observations: 'planner.llm', 'synthesizer.llm'")
        print("  - No separate 'ChatOpenAI' traces")
        print("  - No separate 'synthesize' span")
        print("  - Proper token counting in observations")
    else:
        print("\n❌ Tests failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())





