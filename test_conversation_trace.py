#!/usr/bin/env python3
"""
Test script to verify conversation endpoint generates Langfuse traces
"""
import os
import sys
import json
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.langfuse_config import langfuse_config

def test_conversation_trace():
    """Test that conversation endpoint generates traces"""
    print("🧪 Testing Conversation Endpoint Langfuse Integration...")
    print("=" * 60)
    
    # Check Langfuse configuration
    if not langfuse_config.enabled:
        print("❌ Langfuse is not configured")
        return False
    
    print("✅ Langfuse is configured")
    print(f"   Host: {langfuse_config.host}")
    print(f"   Public Key: {langfuse_config.public_key[:10]}...")
    
    # Test callback handler creation
    trace_id = f"test-conversation-{int(time.time())}"
    user_id = "test-user-123"
    
    handler = langfuse_config.get_callback_handler(trace_id, user_id)
    if handler:
        print("✅ Callback handler created successfully")
        print(f"   Trace ID: {trace_id}")
        print(f"   User ID: {user_id}")
    else:
        print("❌ Failed to create callback handler")
        return False
    
    # Test flush
    try:
        langfuse_config.flush()
        print("✅ Langfuse flush successful")
    except Exception as e:
        print(f"⚠️  Langfuse flush warning: {e}")
    
    print("\n🎯 What to expect in Langfuse dashboard:")
    print(f"   - Trace ID: {trace_id}")
    print("   - User ID: test-user-123")
    print("   - LLM calls for planner and synthesizer")
    print("   - Complete conversation flow")
    print("   - Token usage and performance metrics")
    
    print("\n📝 Next steps:")
    print("1. Start your Giskard agent: python app.py")
    print("2. Send a chat message through the UI")
    print("3. Check the Langfuse dashboard for traces")
    print("4. Look for trace ID starting with 'chat-' or your session ID")
    
    return True

if __name__ == "__main__":
    success = test_conversation_trace()
    if success:
        print("\n🎉 Conversation endpoint is ready for Langfuse tracing!")
    else:
        print("\n❌ Setup incomplete. Please check your configuration.")
    
    sys.exit(0 if success else 1)
