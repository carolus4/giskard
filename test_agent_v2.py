#!/usr/bin/env python3
"""
Simple test script for the new Agent V2 orchestrator
"""
import requests
import json
import time

def test_agent_v2_endpoint():
    """Test the new /api/agent/v2/step endpoint"""
    base_url = "http://localhost:5001"
    endpoint = f"{base_url}/api/agent/v2/step"
    
    print("🧪 Testing Agent V2 Orchestrator")
    print("=" * 50)
    
    # Test data
    test_cases = [
        {
            "name": "Create Task",
            "data": {
                "input_text": "Create a task to review the quarterly report",
                "session_id": "test-session-1",
                "domain": "test"
            }
        },
        {
            "name": "Fetch Tasks",
            "data": {
                "input_text": "What are my current tasks?",
                "session_id": "test-session-2",
                "domain": "test"
            }
        },
        {
            "name": "Pure Chat",
            "data": {
                "input_text": "Hello, how are you?",
                "session_id": "test-session-3",
                "domain": "test"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 Testing: {test_case['name']}")
        print(f"Input: {test_case['data']['input_text']}")
        
        try:
            # Make request
            response = requests.post(
                endpoint,
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Success!")
                print(f"Events: {len(result.get('events', []))}")
                print(f"Final Message: {result.get('final_message', '')[:100]}...")
                
                # Show event types
                events = result.get('events', [])
                event_types = [event.get('type') for event in events]
                print(f"Event Types: {event_types}")
                
            else:
                print(f"❌ Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection Error: Make sure the server is running on port 5001")
        except requests.exceptions.Timeout:
            print("❌ Timeout: Request took too long")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_agent_v2_endpoint()
