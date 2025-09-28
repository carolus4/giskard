#!/usr/bin/env python3
"""
Test what fetch_tasks actually returns with real data
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from orchestrator.actions.actions import ActionExecutor
import json

def test_real_fetch_tasks():
    """Test fetch_tasks with real data"""
    print("🔍 Testing Real fetch_tasks Response")
    print("=" * 50)
    
    # Initialize action executor
    executor = ActionExecutor()
    
    # Call fetch_tasks
    success, result = executor.fetch_tasks()
    
    print(f"Success: {success}")
    print(f"Result keys: {list(result.keys())}")
    print(f"Task count: {result.get('count', 'N/A')}")
    print(f"Message: {result.get('message', 'N/A')}")
    
    if success and 'tasks' in result:
        tasks = result['tasks']
        print(f"\n📊 First 3 Real Tasks:")
        for i, task in enumerate(tasks[:3]):
            print(f"  {i+1}. ID: {task.get('id')}")
            print(f"     Title: {task.get('title')}")
            print(f"     Status: {task.get('status')}")
            print(f"     Project: {task.get('project')}")
            print(f"     Categories: {task.get('categories')}")
            print(f"     Created: {task.get('created_at')}")
            print()
    
    print("📝 Full Result Structure:")
    print(json.dumps(result, indent=2)[:1000] + "..." if len(json.dumps(result, indent=2)) > 1000 else json.dumps(result, indent=2))

if __name__ == "__main__":
    test_real_fetch_tasks()
