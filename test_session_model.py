#!/usr/bin/env python3
"""
Test script for the new session-based data model
"""
import os
import sys
import json
import time
import requests
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.session_db import SessionDB, TraceDB, AgentStepDB

def test_session_creation():
    """Test session creation and management"""
    print("🧪 Testing Session Creation...")
    
    # Create a new session
    session = SessionDB.create(
        user_id="test-user-123",
        metadata={"domain": "chat", "test": True}
    )
    
    print(f"✅ Created session: {session.id}")
    print(f"   User ID: {session.user_id}")
    print(f"   Created: {session.created_at}")
    print(f"   Metadata: {session.metadata}")
    
    return session

def test_trace_creation(session_id):
    """Test trace creation within a session"""
    print("\n🧪 Testing Trace Creation...")
    
    # Create multiple traces for the same session
    traces = []
    for i in range(3):
        trace = TraceDB.create(
            session_id=session_id,
            user_message=f"Test message {i+1}",
            metadata={"test": True, "message_number": i+1}
        )
        traces.append(trace)
        print(f"✅ Created trace {i+1}: {trace.id}")
    
    return traces

def test_agent_steps(session_id, trace_id):
    """Test agent step creation with session support"""
    print("\n🧪 Testing Agent Steps...")
    
    # Create agent steps for the trace
    steps = []
    for i in range(3):
        step = AgentStepDB.create(
            session_id=session_id,
            trace_id=trace_id,
            step_number=i+1,
            step_type=f"test_step_{i+1}",
            input_data={"test": True, "step": i+1},
            output_data={"result": f"output_{i+1}"}
        )
        steps.append(step)
        print(f"✅ Created step {i+1}: {step.step_type}")
    
    return steps

def test_data_retrieval(session_id, trace_id):
    """Test data retrieval methods"""
    print("\n🧪 Testing Data Retrieval...")
    
    # Get session by ID
    session = SessionDB.get_by_id(session_id)
    print(f"✅ Retrieved session: {session.id if session else 'None'}")
    
    # Get traces for session
    traces = TraceDB.get_by_session_id(session_id)
    print(f"✅ Retrieved {len(traces)} traces for session")
    
    # Get agent steps for trace
    steps = AgentStepDB.get_by_trace_id(trace_id)
    print(f"✅ Retrieved {len(steps)} steps for trace")
    
    # Get agent steps for session
    session_steps = AgentStepDB.get_by_session_id(session_id)
    print(f"✅ Retrieved {len(session_steps)} total steps for session")
    
    return session, traces, steps

def test_api_integration():
    """Test API integration with session-based model"""
    print("\n🧪 Testing API Integration...")
    
    # Test conversation endpoint
    try:
        response = requests.post('http://localhost:5000/api/agent/conversation', 
                              json={
                                  'input_text': 'What should I focus on today?',
                                  'domain': 'chat'
                              },
                              timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API call successful")
            print(f"   Session ID: {data.get('session_id', 'Not provided')}")
            print(f"   Trace ID: {data.get('trace_id', 'Not provided')}")
            print(f"   Steps: {len(data.get('steps', []))}")
            return data
        else:
            print(f"❌ API call failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ API call failed: {e}")
        return None

def test_multiple_conversations():
    """Test multiple conversations in the same session"""
    print("\n🧪 Testing Multiple Conversations...")
    
    session_id = None
    
    for i in range(3):
        try:
            payload = {
                'input_text': f'Test message {i+1}',
                'domain': 'chat'
            }
            
            if session_id:
                payload['session_id'] = session_id
            
            response = requests.post('http://localhost:5000/api/agent/conversation', 
                                  json=payload,
                                  timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                session_id = data.get('session_id')
                trace_id = data.get('trace_id')
                print(f"✅ Conversation {i+1}: Session {session_id}, Trace {trace_id}")
            else:
                print(f"❌ Conversation {i+1} failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Conversation {i+1} failed: {e}")
    
    return session_id

def main():
    """Run all tests"""
    print("🚀 Testing Session-Based Data Model")
    print("=" * 50)
    
    # Test 1: Session creation
    session = test_session_creation()
    
    # Test 2: Trace creation
    traces = test_trace_creation(session.id)
    
    # Test 3: Agent steps
    if traces:
        steps = test_agent_steps(session.id, traces[0].id)
    
    # Test 4: Data retrieval
    if traces:
        test_data_retrieval(session.id, traces[0].id)
    
    # Test 5: API integration (if server is running)
    print("\n" + "=" * 50)
    print("🌐 Testing API Integration (requires running server)")
    print("=" * 50)
    
    api_data = test_api_integration()
    
    if api_data:
        # Test 6: Multiple conversations
        test_multiple_conversations()
    
    print("\n🎉 Session-based model testing completed!")
    print("\n📊 Expected Data Model:")
    print("   Session (session_id)")
    print("   ├── Trace 1 (trace_id_1)")
    print("   │   ├── Step 1: planner-node")
    print("   │   ├── Step 2: action-node")
    print("   │   └── Step 3: synthesizer-node")
    print("   ├── Trace 2 (trace_id_2)")
    print("   │   └── ...")
    print("   └── Trace N (trace_id_N)")

if __name__ == "__main__":
    main()
