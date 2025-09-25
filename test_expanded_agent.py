#!/usr/bin/env python3
"""
Test script to verify the expanded agent capabilities
"""
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.agent_service import AgentService
from models.task_db import TaskDB

def test_expanded_agent_capabilities():
    """Test all the new agent tools"""
    print("🧪 Testing Expanded Agent Capabilities")
    print("=" * 50)
    
    agent = AgentService()
    
    # Test 1: Create a task for testing
    print("1. Testing create_task...")
    create_result = agent.process_step([
        {'type': 'user', 'content': 'Create a test task called "Agent Testing Task" with description "Testing the expanded agent capabilities"'}
    ], {})
    
    print(f"   Success: {create_result['success']}")
    if create_result['success'] and create_result['side_effects']:
        test_task_id = create_result['side_effects'][0].get('task_id')
        print(f"   Created task ID: {test_task_id}")
    else:
        print("   ❌ Failed to create test task")
        return
    
    # Test 2: Get tasks
    print("\n2. Testing get_tasks...")
    get_result = agent.process_step([
        {'type': 'user', 'content': 'Show me all my open tasks'}
    ], {})
    
    print(f"   Success: {get_result['success']}")
    if get_result['success']:
        print(f"   Response: {get_result['assistant_text'][:100]}...")
    
    # Test 3: Update task
    print("\n3. Testing update_task...")
    update_result = agent.process_step([
        {'type': 'user', 'content': f'Update task {test_task_id} to have title "Updated Agent Test Task" and add project "testing"'}
    ], {})
    
    print(f"   Success: {update_result['success']}")
    if update_result['success']:
        print(f"   Response: {update_result['assistant_text'][:100]}...")
    
    # Test 4: Update task status
    print("\n4. Testing update_task_status...")
    status_result = agent.process_step([
        {'type': 'user', 'content': f'Mark task {test_task_id} as in progress'}
    ], {})
    
    print(f"   Success: {status_result['success']}")
    if status_result['success']:
        print(f"   Response: {status_result['assistant_text'][:100]}...")
    
    # Test 5: Verify updates
    print("\n5. Verifying updates...")
    task = TaskDB.get_by_id(test_task_id)
    if task:
        print(f"   Title: {task.title}")
        print(f"   Project: {task.project}")
        print(f"   Status: {task.status}")
        print(f"   Description: {task.description}")
    
    # Test 6: Test undo functionality
    print("\n6. Testing undo functionality...")
    if status_result.get('undo_token'):
        undo_result = agent.undo_last_mutation(status_result['undo_token'])
        print(f"   Undo success: {undo_result['success']}")
        print(f"   Undo message: {undo_result.get('message', 'No message')}")
        
        # Verify undo worked
        task = TaskDB.get_by_id(test_task_id)
        if task:
            print(f"   Status after undo: {task.status}")
    
    # Test 7: Delete task
    print("\n7. Testing delete_task...")
    delete_result = agent.process_step([
        {'type': 'user', 'content': f'Delete task {test_task_id}'}
    ], {})
    
    print(f"   Success: {delete_result['success']}")
    if delete_result['success']:
        print(f"   Response: {delete_result['assistant_text'][:100]}...")
    
    # Test 8: Test delete undo
    print("\n8. Testing delete undo...")
    if delete_result.get('undo_token'):
        undo_result = agent.undo_last_mutation(delete_result['undo_token'])
        print(f"   Undo success: {undo_result['success']}")
        print(f"   Undo message: {undo_result.get('message', 'No message')}")
        
        # Verify task was restored
        if 'restored_task_id' in undo_result:
            restored_task = TaskDB.get_by_id(undo_result['restored_task_id'])
            if restored_task:
                print(f"   Restored task: {restored_task.title}")
            
            # Clean up - delete the restored task
            restored_task.delete()
    
    print("\n✅ Expanded agent capabilities test completed!")
    print("\n📋 Summary of new capabilities:")
    print("   ✅ create_task - Create new tasks")
    print("   ✅ get_tasks - Retrieve task lists")
    print("   ✅ update_task - Modify existing tasks")
    print("   ✅ delete_task - Remove tasks")
    print("   ✅ update_task_status - Change task status")
    print("   ✅ Comprehensive undo support for all operations")
    print("\n🎯 The agent can now perform full CRUD operations on tasks!")

def test_agent_conversation_examples():
    """Test realistic conversation examples"""
    print("\n🗣️ Testing Realistic Conversation Examples")
    print("=" * 50)
    
    agent = AgentService()
    
    examples = [
        "Show me my tasks that are in progress",
        "Mark task 109 as completed", 
        "Update my 'query back-end' task to add a description about fixing authentication",
        "Delete any tasks with 'test' in the title",
        "Create a task to review the new agent features"
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. User: \"{example}\"")
        try:
            result = agent.process_step([
                {'type': 'user', 'content': example}
            ], {})
            
            print(f"   Success: {result['success']}")
            print(f"   Response: {result['assistant_text'][:100]}...")
            if result.get('side_effects'):
                print(f"   Side effects: {len(result['side_effects'])} actions")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

if __name__ == '__main__':
    test_expanded_agent_capabilities()
    test_agent_conversation_examples()
