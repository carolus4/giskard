#!/usr/bin/env python3
"""
Test script to verify Langfuse trace hierarchy
"""
import os
import sys
import time
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.langfuse_config import langfuse_config

def test_trace_hierarchy():
    """Test the trace hierarchy implementation"""
    print("🧪 Testing Langfuse Trace Hierarchy...")
    print("=" * 50)
    
    if not langfuse_config.enabled:
        print("❌ Langfuse is not configured")
        return False
    
    print("✅ Langfuse is configured")
    
    # Create a test trace
    trace_id = f"test-hierarchy-{int(time.time())}"
    user_id = "test-user-123"
    
    print(f"\n📊 Creating trace hierarchy for:")
    print(f"   Trace ID: {trace_id}")
    print(f"   User ID: {user_id}")
    
    # Create main trace
    trace = langfuse_config.create_trace(
        name="chat.turn",
        trace_id=trace_id,
        user_id=user_id,
        input_data={"input_text": "Test message", "session_id": user_id}
    )
    
    if not trace:
        print("❌ Failed to create trace")
        return False
    
    print("✅ Created main trace: chat.turn")
    
    # Create planner span
    planner_span = langfuse_config.create_span(
        trace,
        name="plan",
        span_type="agent",
        input_data={"input_text": "Test message"}
    )
    
    if not planner_span:
        print("❌ Failed to create planner span")
        return False
    
    print("✅ Created planner span: plan (agent)")
    
    # Create planner generation
    planner_generation = langfuse_config.create_generation(
        planner_span,
        name="planner.llm",
        input_data={"messages": [{"type": "HumanMessage", "content": "Test message"}]},
        output_data={"response": "Test planner response"}
    )
    
    if not planner_generation:
        print("❌ Failed to create planner generation")
        return False
    
    print("✅ Created planner generation: planner.llm")
    
    # Create action span (optional)
    action_span = langfuse_config.create_span(
        trace,
        name="tool.execute.test_action",
        span_type="retriever",
        input_data={"actions": [{"name": "test_action", "args": {}}]}
    )
    
    if action_span:
        action_span.update(output=[{"name": "test_action", "ok": True, "result": "Test result"}])
        print("✅ Created action span: tool.execute.test_action (retriever)")
    else:
        print("⚠️  Action span not created (this is optional)")
    
    # Create synthesizer span
    synthesizer_span = langfuse_config.create_span(
        trace,
        name="synthesize",
        span_type="generation",
        input_data={"action_results": [{"name": "test_action", "ok": True}]}
    )
    
    if not synthesizer_span:
        print("❌ Failed to create synthesizer span")
        return False
    
    print("✅ Created synthesizer span: synthesize (generation)")
    
    # Create synthesizer generation
    synthesizer_generation = langfuse_config.create_generation(
        synthesizer_span,
        name="synthesizer.llm",
        input_data={"messages": [{"type": "SystemMessage", "content": "Test prompt"}]},
        output_data={"response": "Test synthesizer response"}
    )
    
    if not synthesizer_generation:
        print("❌ Failed to create synthesizer generation")
        return False
    
    print("✅ Created synthesizer generation: synthesizer.llm")
    
    # Complete the trace
    trace.update(output={"final_message": "Test synthesizer response", "total_steps": 3})
    print("✅ Updated trace with final output")
    
    # Flush events
    langfuse_config.flush()
    print("✅ Flushed events to Langfuse")
    
    print(f"\n🎯 Expected trace hierarchy in Langfuse dashboard:")
    print(f"📊 chat.turn (trace)")
    print(f"├── 🔍 plan (span)")
    print(f"│   └── ⚡ planner.llm (generation)")
    print(f"├── 🔧 tool.execute.test_action (span) [optional]")
    print(f"└── 🎯 synthesize (span)")
    print(f"    └── ⚡ synthesizer.llm (generation)")
    
    print(f"\n📝 Check your Langfuse dashboard at: {langfuse_config.host}")
    print(f"   Look for trace ID: {trace_id}")
    
    return True

if __name__ == "__main__":
    success = test_trace_hierarchy()
    if success:
        print("\n🎉 Trace hierarchy test completed successfully!")
    else:
        print("\n❌ Trace hierarchy test failed.")
    
    sys.exit(0 if success else 1)
