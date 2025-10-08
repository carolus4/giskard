#!/usr/bin/env python3
"""
Simple test for Langfuse trace hierarchy
"""
import os
import sys
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.langfuse_config import langfuse_config
from langfuse import get_client

def test_simple_trace():
    """Test a simple trace hierarchy"""
    print("🧪 Testing Simple Langfuse Trace Hierarchy...")x§§
    print("=" * 50)
    
    if not langfuse_config.enabled:
        print("❌ Langfuse is not configured")
        return False
    
    print("✅ Langfuse is configured")
    
    # Create a test trace (Langfuse requires 32 lowercase hex chars)
    import hashlib
    trace_id = hashlib.md5(f"test-simple-{int(time.time())}".encode()).hexdigest()
    user_id = "test-user-123"
    
    print(f"\n📊 Creating simple trace hierarchy:")
    print(f"   Trace ID: {trace_id}")
    print(f"   User ID: {user_id}")
    
    try:
        client = get_client()
        
        # Create trace context
        from langfuse.types import TraceContext
        trace_context = TraceContext(
            trace_id=trace_id,
            user_id=user_id,
            input={"input_text": "Test message", "session_id": user_id}
        )
        
        print("✅ Created trace context")
        
        # Create root span
        root_span = client.start_span(
            trace_context=trace_context,
            name="chat.turn",
            input={"input_text": "Test message", "session_id": user_id}
        )
        print("✅ Created root span: chat.turn")
        
        # Create planner span
        planner_span = client.start_span(
            trace_context=trace_context,
            name="plan",
            input={"input_text": "Test message"}
        )
        print("✅ Created planner span: plan")
        
        # Create planner generation
        planner_generation = planner_span.start_generation(
            name="planner.llm",
            input={"messages": [{"type": "HumanMessage", "content": "Test message"}]}
        )
        print("✅ Created planner generation: planner.llm")
        
        # Simulate LLM response
        response = "Test planner response"
        planner_generation.update(output=response)
        print("✅ Updated planner generation with output")
        
        # End planner generation and span
        planner_generation.end()
        planner_span.end()
        
        # Create synthesizer span
        synthesizer_span = client.start_span(
            trace_context=trace_context,
            name="synthesize",
            input={"action_results": [], "input_text": "Test message"}
        )
        print("✅ Created synthesizer span: synthesize")
        
        # Create synthesizer generation
        synthesizer_generation = synthesizer_span.start_generation(
            name="synthesizer.llm",
            input={"messages": [{"type": "SystemMessage", "content": "Test prompt"}]}
        )
        print("✅ Created synthesizer generation: synthesizer.llm")
        
        # Simulate LLM response
        response = "Test synthesizer response"
        synthesizer_generation.update(output=response)
        print("✅ Updated synthesizer generation with output")
        
        # End synthesizer generation and span
        synthesizer_generation.end()
        synthesizer_span.end()
        
        # End root span
        root_span.update(output={"final_message": "Test synthesizer response", "total_steps": 2})
        root_span.end()
        print("✅ Ended root span")
        
        # Update trace
        client.update_current_trace(output={"final_message": "Test synthesizer response", "total_steps": 2})
        print("✅ Updated trace with final output")
        
        # Flush events
        langfuse_config.flush()
        print("✅ Flushed events to Langfuse")
        
        print(f"\n🎯 Expected trace hierarchy in Langfuse dashboard:")
        print(f"📊 chat.turn (trace)")
        print(f"├── 🔍 plan (span)")
        print(f"│   └── ⚡ planner.llm (generation)")
        print(f"└── 🎯 synthesize (span)")
        print(f"    └── ⚡ synthesizer.llm (generation)")
        
        print(f"\n📝 Check your Langfuse dashboard at: {langfuse_config.host}")
        print(f"   Look for trace ID: {trace_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating trace hierarchy: {e}")
        return False

if __name__ == "__main__":
    success = test_simple_trace()
    if success:
        print("\n🎉 Simple trace hierarchy test completed successfully!")
    else:
        print("\n❌ Simple trace hierarchy test failed.")
    
    sys.exit(0 if success else 1)
