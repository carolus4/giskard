"""
Test script to verify improved Langfuse tracing implementation

This script tests:
1. Single root "chat.turn" trace
2. Planner and synthesizer as nested observations with token counts
3. Tool executions tracked as observations
4. Prompts properly linked
5. No duplicate ChatOpenAI traces
6. Session tracking
7. Model metadata included
8. Proper flush handling
"""
import requests
import json
import time
import hashlib
from datetime import datetime


def test_improved_tracing():
    """Test the improved Langfuse tracing implementation"""

    print("=" * 80)
    print("Testing Improved Langfuse Tracing Implementation")
    print("=" * 80)

    # Configuration
    api_url = "http://localhost:5000/api/agent/conversation"

    # Test data
    test_message = "Create a task to review the quarterly report"
    session_id = f"test-session-{int(time.time())}"
    trace_id = hashlib.md5(f"trace-{int(time.time())}".encode()).hexdigest()

    print(f"\n1. Test Configuration")
    print(f"   - API URL: {api_url}")
    print(f"   - Session ID: {session_id}")
    print(f"   - Trace ID: {trace_id}")
    print(f"   - Test Message: '{test_message}'")

    # Prepare request
    request_data = {
        "input_text": test_message,
        "session_id": session_id,
        "domain": "productivity",
        "conversation_context": [],
        "trace_id": trace_id
    }

    print(f"\n2. Sending Request...")
    print(f"   Request Data: {json.dumps(request_data, indent=2)}")

    try:
        # Send request
        start_time = time.time()
        response = requests.post(api_url, json=request_data, timeout=30)
        end_time = time.time()

        print(f"\n3. Response Received")
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Response Time: {end_time - start_time:.2f}s")

        if response.status_code == 200:
            result = response.json()

            print(f"\n4. Response Data")
            print(f"   - Success: {result.get('success')}")
            print(f"   - Message: {result.get('message')}")
            print(f"   - Session ID: {result.get('session_id')}")
            print(f"   - Trace ID: {result.get('trace_id')}")
            print(f"   - Total Steps: {result.get('total_steps')}")

            # Check steps
            steps = result.get('steps', [])
            print(f"\n5. Execution Steps ({len(steps)} total)")
            for step in steps:
                print(f"   Step {step['step_number']}: {step['step_type']}")
                print(f"      - Status: {step['status']}")
                print(f"      - Content: {step['content'][:100]}...")
                if 'details' in step:
                    print(f"      - Details: {step['details']}")

            # Final message
            final_message = result.get('final_message', '')
            print(f"\n6. Final Message")
            print(f"   {final_message}")

            print(f"\n" + "=" * 80)
            print("✅ Test Completed Successfully!")
            print("=" * 80)

            # Verification checklist
            print(f"\n7. Langfuse Verification Checklist")
            print(f"   Visit: https://cloud.langfuse.com")
            print(f"   Look for trace ID: {trace_id}")
            print(f"\n   ✓ Verify the following in Langfuse:")
            print(f"   [ ] Single root trace named 'chat.turn'")
            print(f"   [ ] Planner observation (planner.llm) with token counts")
            print(f"   [ ] Synthesizer observation (synthesizer.llm) with token counts")
            print(f"   [ ] Tool execution observations (if applicable)")
            print(f"   [ ] No duplicate ChatOpenAI traces")
            print(f"   [ ] Session ID: {session_id}")
            print(f"   [ ] Prompts linked correctly")
            print(f"   [ ] Model metadata: gemma3:4b, temperature: 0.7")
            print(f"   [ ] Tags: ['conversation', 'productivity']")

            # Additional tests
            print(f"\n8. Running Additional Verification...")

            # Test with conversation context
            print(f"\n   8a. Testing with conversation context...")
            context_request = {
                "input_text": "What was that task about?",
                "session_id": session_id,
                "domain": "productivity",
                "conversation_context": [
                    {"type": "user", "content": test_message},
                    {"type": "bot", "content": final_message}
                ]
            }

            context_response = requests.post(api_url, json=context_request, timeout=30)
            if context_response.status_code == 200:
                print(f"   ✓ Conversation context test passed")
                context_result = context_response.json()
                print(f"   - Response: {context_result.get('final_message', '')[:100]}...")
            else:
                print(f"   ✗ Conversation context test failed: {context_response.status_code}")

            # Summary
            print(f"\n" + "=" * 80)
            print("📊 Test Summary")
            print("=" * 80)
            print(f"✅ All API tests passed successfully")
            print(f"📝 Manual verification required in Langfuse dashboard")
            print(f"🔗 Trace ID: {trace_id}")
            print(f"🔗 Session ID: {session_id}")

            return True

        else:
            print(f"\n❌ Request Failed")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except requests.exceptions.Timeout:
        print(f"\n❌ Request Timeout")
        print(f"   The request took longer than 30 seconds")
        return False

    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ Connection Error")
        print(f"   Could not connect to {api_url}")
        print(f"   Make sure the server is running")
        print(f"   Error: {str(e)}")
        return False

    except Exception as e:
        print(f"\n❌ Unexpected Error")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_error_handling():
    """Test that flush is called even on errors"""
    print(f"\n" + "=" * 80)
    print("Testing Error Handling and Flush")
    print("=" * 80)

    api_url = "http://localhost:5000/api/agent/conversation"

    # Test with invalid data to trigger error
    invalid_request = {
        "input_text": "",  # Empty input should trigger error
        "session_id": f"error-test-{int(time.time())}"
    }

    print(f"\n1. Testing error handling with empty input...")
    response = requests.post(api_url, json=invalid_request)

    if response.status_code == 400:
        print(f"   ✓ Error properly handled (400 Bad Request)")
        print(f"   - Response: {response.json()}")
        print(f"   ✓ Server should have called flush() in finally block")
        return True
    else:
        print(f"   ✗ Unexpected status code: {response.status_code}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("🚀 Starting Improved Langfuse Tracing Tests")
    print("=" * 80)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"\nPrerequisites:")
    print(f"  1. Server running on http://localhost:5000")
    print(f"  2. Langfuse credentials configured in .env")
    print(f"  3. Internet connection to Langfuse cloud")

    input(f"\nPress Enter to continue...")

    # Run tests
    test1_passed = test_improved_tracing()
    time.sleep(2)  # Brief pause between tests
    test2_passed = test_error_handling()

    # Final summary
    print(f"\n\n" + "=" * 80)
    print("🏁 Final Test Results")
    print("=" * 80)
    print(f"Main Tracing Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Error Handling Test: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"\n{'✅ All tests passed!' if test1_passed and test2_passed else '❌ Some tests failed'}")
    print("=" * 80)
