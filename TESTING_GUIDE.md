# Testing the Improved Langfuse Tracing

## Quick Start

### 1. Prerequisites

Ensure you have:
- ✅ Server running: `python app.py`
- ✅ Langfuse credentials in `.env`
- ✅ Internet connection to Langfuse cloud

### 2. Run the Test

```bash
python test_improved_tracing.py
```

### 3. Expected Output

```
================================================================================
🚀 Starting Improved Langfuse Tracing Tests
================================================================================

Timestamp: 2025-10-23T...

Prerequisites:
  1. Server running on http://localhost:5000
  2. Langfuse credentials configured in .env
  3. Internet connection to Langfuse cloud

Press Enter to continue...

================================================================================
Testing Improved Langfuse Tracing Implementation
================================================================================

1. Test Configuration
   - API URL: http://localhost:5000/api/agent/conversation
   - Session ID: test-session-1234567890
   - Trace ID: abc123def456...
   - Test Message: 'Create a task to review the quarterly report'

2. Sending Request...
   Request Data: {...}

3. Response Received
   - Status Code: 200
   - Response Time: 5.23s

4. Response Data
   - Success: True
   - Message: Conversation completed
   - Session ID: test-session-1234567890
   - Trace ID: abc123def456...
   - Total Steps: 3

5. Execution Steps (3 total)
   Step 1: planner_llm
      - Status: completed
      - Content: I'll help you create a task to review the quarterly report...
      - Details: {'assistant_text': '...', 'actions_count': 1}
   Step 2: action_exec
      - Status: completed
      - Content: ⚡ Executed 1 actions
      - Details: {'successful_actions': 1, 'failed_actions': 0}
   Step 3: synthesizer_llm
      - Status: completed
      - Content: I've created a task to review the quarterly report...
      - Details: {'is_final': True}

6. Final Message
   I've created a task to review the quarterly report...

================================================================================
✅ Test Completed Successfully!
================================================================================

7. Langfuse Verification Checklist
   Visit: https://cloud.langfuse.com
   Look for trace ID: abc123def456...

   ✓ Verify the following in Langfuse:
   [ ] Single root trace named 'chat.turn'
   [ ] Planner observation (planner.llm) with token counts
   [ ] Synthesizer observation (synthesizer.llm) with token counts
   [ ] Tool execution observations (if applicable)
   [ ] No duplicate ChatOpenAI traces
   [ ] Session ID: test-session-1234567890
   [ ] Prompts linked correctly
   [ ] Model metadata: gemma3:4b, temperature: 0.7
   [ ] Tags: ['conversation', 'productivity']

8. Running Additional Verification...

   8a. Testing with conversation context...
   ✓ Conversation context test passed
   - Response: Based on our previous conversation...

================================================================================
📊 Test Summary
================================================================================
✅ All API tests passed successfully
📝 Manual verification required in Langfuse dashboard
🔗 Trace ID: abc123def456...
🔗 Session ID: test-session-1234567890

================================================================================
Testing Error Handling and Flush
================================================================================

1. Testing error handling with empty input...
   ✓ Error properly handled (400 Bad Request)
   - Response: {'error': 'input_text is required'}
   ✓ Server should have called flush() in finally block

================================================================================
🏁 Final Test Results
================================================================================
Main Tracing Test: ✅ PASSED
Error Handling Test: ✅ PASSED

✅ All tests passed!
================================================================================
```

## Verifying in Langfuse

### Step 1: Open Langfuse Dashboard

Visit: https://cloud.langfuse.com

### Step 2: Find Your Trace

1. Go to "Traces" section
2. Look for the trace ID from the test output
3. Or search by session ID

### Step 3: Verify Trace Structure

Check that you see:

```
chat.turn
├── planner.llm (generation)
│   ├── Model: gemma3:4b
│   ├── Temperature: 0.7
│   ├── Input tokens: ~1,234
│   ├── Output tokens: ~567
│   └── Prompt: [Linked]
│
├── tool.execute (span)
│   ├── Duration: ~0.5s
│   └── Metadata: {tool_name, tool_args}
│
└── synthesizer.llm (generation)
    ├── Model: gemma3:4b
    ├── Temperature: 0.7
    ├── Input tokens: ~2,345
    ├── Output tokens: ~789
    └── Prompt: [Linked]
```

### Step 4: Check Metadata

In the trace details, verify:
- **Session ID**: Present
- **User ID**: Same as session ID
- **Tags**: ["conversation", "productivity"]
- **Metadata**: Contains domain and trace_id

### Step 5: Verify No Duplicates

Ensure there are NO:
- Orphaned ChatOpenAI traces
- Duplicate generation observations
- Incorrectly named root traces (like "synthesize")

## Troubleshooting

### Test Fails with Connection Error

**Problem**: `Could not connect to http://localhost:5000`

**Solution**:
```bash
# Start the server
python app.py

# Wait for "Running on http://localhost:5000"
# Then run the test again
```

### Test Fails with 500 Error

**Problem**: Server returns 500 Internal Server Error

**Solution**:
1. Check server logs for errors
2. Verify all dependencies installed:
   ```bash
   pip install -r requirements.txt
   ```
3. Check Langfuse configuration in `.env`

### No Traces Appearing in Langfuse

**Problem**: Test passes but no traces in Langfuse

**Solution**:
1. Check `.env` file has correct credentials:
   ```bash
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```
2. Check server logs for Langfuse warnings
3. Try manually flushing:
   ```python
   from config.langfuse_config import langfuse_config
   langfuse_config.flush()
   ```
4. Wait 30-60 seconds for traces to appear in Langfuse

### Traces Missing Token Counts

**Problem**: Traces appear but token counts are 0 or missing

**Solution**:
1. This is expected for Ollama models (they don't report tokens)
2. Token counting works best with OpenAI API
3. The trace structure is correct regardless

## Manual Testing

If you prefer to test manually:

```bash
# Use curl to send a test request
curl -X POST http://localhost:5000/api/agent/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "Create a task to review the quarterly report",
    "session_id": "manual-test-session",
    "domain": "productivity",
    "conversation_context": []
  }'
```

## What to Look For

### ✅ Good Signs
- Response time: 3-10 seconds
- All 3 steps completed
- Final message makes sense
- No errors in server logs
- Traces appear in Langfuse within 60 seconds

### ❌ Bad Signs
- Response time > 30 seconds
- Steps incomplete
- Error messages in response
- Server logs show warnings
- No traces in Langfuse after 5 minutes

## Next Steps

After verifying the tests pass:

1. **Test in production environment**
   - Run with real user requests
   - Monitor Langfuse dashboard
   - Check for any performance issues

2. **Analyze traces**
   - Look for slow operations
   - Identify high-cost prompts
   - Track error patterns

3. **Optimize based on data**
   - Adjust prompts to reduce tokens
   - Cache frequently used results
   - Parallelize independent operations

4. **Set up alerts**
   - Alert on high costs
   - Alert on slow traces
   - Alert on error rates

## Support

If you encounter issues:

1. Check this guide first
2. Review server logs
3. Check Langfuse dashboard
4. Review the implementation docs:
   - `LANGFUSE_TRACING_IMPROVEMENTS.md`
   - `TRACING_BEFORE_AFTER.md`
   - `TRACING_REFACTOR_SUMMARY.md`

Good luck! 🚀
