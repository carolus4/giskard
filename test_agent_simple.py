#!/usr/bin/env python3
"""
Simple test script for the agent orchestration layer
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.agent_service import AgentService
from utils.agent_metrics import agent_metrics
from models.task_db import TaskDB

def test_agent_basic_functionality():
    """Test basic agent functionality"""
    print("🧪 Testing Agent Orchestration Layer")
    print("=" * 50)
    
    # Reset metrics
    agent_metrics.reset_metrics()
    
    # Create agent service
    agent_service = AgentService()
    
    # Test 1: Check Ollama availability
    print("1. Checking Ollama availability...")
    is_available = agent_service.is_ollama_available()
    print(f"   Ollama available: {is_available}")
    
    if not is_available:
        print("   ⚠️  Ollama is not running. Please start Ollama to test the full functionality.")
        return
    
    # Test 2: Test agent step with mock data
    print("\n2. Testing agent step...")
    messages = [
        {'type': 'user', 'content': 'Create a test task for the agent orchestration system'}
    ]
    ui_context = {
        'current_tasks': [],
        'user_preferences': {}
    }
    
    try:
        result = agent_service.process_step(messages, ui_context)
        print(f"   Success: {result.get('success')}")
        print(f"   Assistant text: {result.get('assistant_text', '')[:100]}...")
        print(f"   Side effects: {len(result.get('side_effects', []))}")
        print(f"   Undo token: {result.get('undo_token', 'None')[:20]}...")
        
        # Test 3: Test undo functionality if a task was created
        if result.get('side_effects') and result.get('undo_token'):
            print("\n3. Testing undo functionality...")
            undo_token = result['undo_token']
            undo_result = agent_service.undo_last_mutation(undo_token)
            print(f"   Undo success: {undo_result.get('success')}")
            if undo_result.get('success'):
                print(f"   Undo message: {undo_result.get('message')}")
        
        # Test 4: Check metrics
        print("\n4. Checking metrics...")
        metrics = agent_metrics.get_metrics()
        print(f"   Total requests: {metrics.get('requests_total', 0)}")
        print(f"   Successful requests: {metrics.get('requests_successful', 0)}")
        print(f"   Failed requests: {metrics.get('requests_failed', 0)}")
        print(f"   Tool calls: {metrics.get('tool_calls_total', 0)}")
        print(f"   Create task calls: {metrics.get('create_task_calls', 0)}")
        print(f"   Undo operations: {metrics.get('undo_operations', 0)}")
        print(f"   Average response time: {metrics.get('average_response_time', 0):.2f}s")
        
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test 5: Clean up test tasks
    print("\n5. Cleaning up test tasks...")
    tasks = TaskDB.get_all()
    test_tasks = [t for t in tasks if 'test' in t.title.lower()]
    for task in test_tasks:
        task.delete()
        print(f"   Deleted: {task.title}")
    
    print("\n✅ Agent orchestration test completed!")

def test_api_endpoints():
    """Test API endpoints (requires server to be running)"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 30)
    
    import requests
    
    base_url = "http://localhost:5001/api"
    
    # Test metrics endpoint
    try:
        response = requests.get(f"{base_url}/agent/metrics", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Metrics endpoint working")
            print(f"   Metrics: {data.get('data', {}).get('metrics', {})}")
        else:
            print(f"❌ Metrics endpoint failed: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("❌ Server not running. Start the server with: python app.py")
    except Exception as e:
        print(f"❌ Error testing metrics endpoint: {e}")

if __name__ == '__main__':
    test_agent_basic_functionality()
    test_api_endpoints()
