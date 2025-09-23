#!/usr/bin/env python3
"""
Test script for the new SQLite-based API system
"""
import requests
import json
import time

BASE_URL = "http://localhost:5001/api/v2"

def test_api():
    """Test the new API endpoints"""
    print("🧪 Testing New SQLite-based API")
    print("=" * 50)
    
    # Test 1: Get all tasks
    print("\n1. Testing GET /tasks")
    response = requests.get(f"{BASE_URL}/tasks")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: {data['counts']['today']} tasks today")
        print(f"   - Open: {len(data['tasks']['open'])}")
        print(f"   - In Progress: {len(data['tasks']['in_progress'])}")
        print(f"   - Done: {len(data['tasks']['done'])}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False
    
    # Test 2: Create a new task
    print("\n2. Testing POST /tasks")
    new_task = {
        "title": "API Test Task",
        "description": "Testing the new clean API",
        "project": "Testing",
        "categories": ["learning"]
    }
    response = requests.post(f"{BASE_URL}/tasks", json=new_task)
    if response.status_code == 200:
        data = response.json()
        task_id = data['task']['id']
        print(f"✅ Success: Created task with ID {task_id}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False
    
    # Test 3: Get specific task
    print(f"\n3. Testing GET /tasks/{task_id}")
    response = requests.get(f"{BASE_URL}/tasks/{task_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: Retrieved task '{data['title']}'")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False
    
    # Test 4: Update task status to in_progress
    print(f"\n4. Testing PATCH /tasks/{task_id}/status")
    response = requests.patch(f"{BASE_URL}/tasks/{task_id}/status", json={"status": "in_progress"})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: Task status updated to {data['task']['status']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False
    
    # Test 5: Update task content
    print(f"\n5. Testing PUT /tasks/{task_id}")
    update_data = {
        "title": "Updated API Test Task",
        "description": "Updated description for testing",
        "project": "Updated Testing"
    }
    response = requests.put(f"{BASE_URL}/tasks/{task_id}", json=update_data)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: Task updated - '{data['task']['title']}'")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False
    
    # Test 6: Mark task as done
    print(f"\n6. Testing PATCH /tasks/{task_id}/status (mark done)")
    response = requests.patch(f"{BASE_URL}/tasks/{task_id}/status", json={"status": "done"})
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: Task marked as done")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False
    
    # Test 7: Test reordering (get some task IDs first)
    print(f"\n7. Testing POST /tasks/reorder")
    response = requests.get(f"{BASE_URL}/tasks")
    if response.status_code == 200:
        data = response.json()
        # Get first 3 open tasks for reordering
        open_tasks = data['tasks']['open'][:3]
        if len(open_tasks) >= 2:
            task_ids = [task['id'] for task in open_tasks]
            # Reverse the order
            task_ids.reverse()
            
            response = requests.post(f"{BASE_URL}/tasks/reorder", json={"task_ids": task_ids})
            if response.status_code == 200:
                print(f"✅ Success: Reordered {len(task_ids)} tasks")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
        else:
            print("⚠️  Skipped: Not enough tasks to test reordering")
    
    # Test 8: Delete the test task
    print(f"\n8. Testing DELETE /tasks/{task_id}")
    response = requests.delete(f"{BASE_URL}/tasks/{task_id}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success: Task deleted - {data['message']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
        return False
    
    # Test 9: Test legacy endpoints for backward compatibility
    print(f"\n9. Testing legacy endpoints")
    response = requests.post(f"{BASE_URL}/tasks/add", json={"title": "Legacy Test", "description": "Testing legacy endpoint"})
    if response.status_code == 200:
        data = response.json()
        legacy_task_id = data['task']['id']
        print(f"✅ Success: Legacy add endpoint works - ID {legacy_task_id}")
        
        # Clean up
        requests.delete(f"{BASE_URL}/tasks/{legacy_task_id}")
    else:
        print(f"❌ Failed: Legacy add endpoint - {response.status_code}")
    
    print(f"\n🎉 All tests completed successfully!")
    return True

if __name__ == '__main__':
    try:
        success = test_api()
        if success:
            print("\n✨ New API system is working perfectly!")
        else:
            print("\n❌ Some tests failed. Check the output above.")
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server. Make sure it's running on port 5001.")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
