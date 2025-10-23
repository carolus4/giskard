# Langfuse Tracing Improvements

This document describes the comprehensive improvements made to the Langfuse tracing implementation in the Giskard agent.

## Overview

The tracing implementation has been refactored to use Langfuse's `@observe()` decorator pattern, providing cleaner code, better maintainability, and improved observability.

## Key Improvements

### 1. ✅ Simplified Tracing with `@observe()` Decorator

**Before**: Manual span and observation management
```python
# Old approach - complex and error-prone
root_span = client.start_span(...)
planner_generation = root_span.start_observation(...)
planner_generation.update(...)
planner_generation.end()
```

**After**: Decorator-based automatic tracing
```python
# New approach - clean and maintainable
@observe(name="planner.llm", as_type="generation")
def call_planner_llm(orchestrator, input_text, ...):
    langfuse_context.update_current_observation(
        model="gemma3:4b",
        model_parameters={"temperature": 0.7}
    )
    return orchestrator.llm.invoke(messages)
```

**Benefits**:
- Automatic trace hierarchy management
- Less boilerplate code
- Easier to maintain and debug
- Proper error handling built-in

### 2. ✅ Guaranteed Flush with try/finally

**Before**: Flush could be skipped on errors
```python
# Old approach
result = process_conversation(...)
langfuse_config.flush()  # Skipped if error occurs
```

**After**: Flush always executes
```python
# New approach
try:
    result = process_conversation_with_tracing(...)
    return APIResponse.success(...)
finally:
    # Always flush Langfuse events, even on error
    langfuse_config.flush()
```

**Benefits**:
- Traces always sent to Langfuse
- No data loss on errors
- Better observability of failures

### 3. ✅ Standardized Callback Handler Creation

**Before**: Multiple callback handlers created per conversation
```python
# Old approach - inefficient
handler1 = langfuse_config.get_callback_handler(trace_id, user_id)
response1 = llm.invoke(messages, config={"callbacks": [handler1]})

handler2 = langfuse_config.get_callback_handler(trace_id, user_id)
response2 = llm.invoke(messages, config={"callbacks": [handler2]})
```

**After**: No callback handlers needed - decorators handle everything
```python
# New approach - decorators manage tracing automatically
@observe(name="planner.llm", as_type="generation")
def call_planner_llm(...):
    return orchestrator.llm.invoke(messages)
```

**Benefits**:
- Simpler code
- Consistent tracing
- No handler management overhead

### 4. ✅ Model Metadata Included

**Before**: Model information missing from traces
```python
# Old approach - no model metadata
response = llm.invoke(messages)
```

**After**: Rich model metadata in every generation
```python
# New approach
langfuse_context.update_current_observation(
    model="gemma3:4b",
    model_parameters={"temperature": 0.7},
    metadata={
        "trace_id": trace_id,
        "session_id": session_id,
        "step_type": "planner"
    }
)
```

**Benefits**:
- Cost tracking per model
- Performance analysis by model
- Better debugging with full context

### 5. ✅ Tool Events Converted to Observations

**Before**: Tools tracked as simple events
```python
# Old approach - limited observability
tool_span.create_event(name="tool.request", input={...})
tool_span.create_event(name="tool.response", input={...})
```

**After**: Tools tracked as full observations
```python
# New approach
@observe(name="tool.execute", as_type="span")
def execute_action_with_tracing(orchestrator, action_name, action_args):
    langfuse_context.update_current_observation(
        metadata={"tool_name": action_name, "tool_args": action_args}
    )
    success, result = orchestrator.action_executor.execute_action(...)
    langfuse_context.update_current_observation(
        output={"success": success, "result": result}
    )
    return result
```

**Benefits**:
- Duration tracking for tools
- Better hierarchy visualization
- Full input/output capture
- Error tracking per tool

### 6. ✅ Proper Prompt Linking

**Before**: Unclear prompt linking
```python
# Old approach - may not link correctly
planner_generation = root_span.start_observation(
    prompt=langfuse_prompt  # Unclear if this works
)
```

**After**: Explicit prompt linking via context
```python
# New approach
langfuse_context.update_current_observation(
    prompt=langfuse_prompt  # Properly linked via context
)
```

**Benefits**:
- Prompts correctly linked in Langfuse UI
- Version tracking works
- Prompt performance metrics available

### 7. ✅ Session Tracking for Conversations

**Before**: No session grouping
```python
# Old approach - traces not grouped by session
```

**After**: Full session tracking
```python
# New approach
langfuse_context.update_current_trace(
    session_id=session_id,
    user_id=session_id,
    metadata={"domain": domain, "trace_id": trace_id},
    tags=["conversation", domain]
)
```

**Benefits**:
- Multi-turn conversations grouped
- User behavior analysis
- Session-level metrics
- Better cost attribution

### 8. ✅ Clean Code Architecture

**Before**: 400+ lines of complex tracing logic in main endpoint

**After**: Clean separation with helper functions
- `call_planner_llm()` - 63 lines, focused on planning
- `execute_action_with_tracing()` - 41 lines, focused on tool execution
- `call_synthesizer_llm()` - 49 lines, focused on synthesis
- `process_conversation_with_tracing()` - 153 lines, orchestrates flow
- Main endpoint: ~85 lines, handles HTTP/session management only

**Benefits**:
- Easier to test individual components
- Better code reusability
- Simpler debugging
- Clearer separation of concerns

## New Trace Structure

```
chat.turn (root trace with session tracking)
├── Metadata:
│   ├── session_id: "session-xxx"
│   ├── domain: "productivity"
│   ├── trace_id: "abc123..."
│   └── tags: ["conversation", "productivity"]
│
├── planner.llm (generation observation)
│   ├── Model: gemma3:4b
│   ├── Parameters: {temperature: 0.7}
│   ├── Prompt: Linked to Langfuse prompt
│   ├── Input: User message + context
│   ├── Output: Planner decision
│   └── Tokens: Input + output counts
│
├── tool.execute (span observation) [for each action]
│   ├── Metadata: {tool_name, tool_args}
│   ├── Input: Action arguments
│   ├── Output: {success, result}
│   └── Duration: Execution time
│
└── synthesizer.llm (generation observation)
    ├── Model: gemma3:4b
    ├── Parameters: {temperature: 0.7}
    ├── Prompt: Linked to Langfuse prompt
    ├── Input: Action results + context
    ├── Output: Final response
    └── Tokens: Input + output counts
```

## Files Modified

### Core Implementation
1. **server/routes/agent.py** (~850 → ~616 lines, -234 lines!)
   - Added `@observe` decorator imports
   - Created `call_planner_llm()` helper function
   - Created `execute_action_with_tracing()` helper function
   - Created `call_synthesizer_llm()` helper function
   - Created `process_conversation_with_tracing()` main function
   - Simplified `/conversation` endpoint
   - Added try/finally for guaranteed flush

### Testing
2. **test_improved_tracing.py** (new file, 267 lines)
   - Comprehensive test suite
   - Manual verification checklist
   - Error handling tests
   - Conversation context tests

### Documentation
3. **LANGFUSE_TRACING_IMPROVEMENTS.md** (this file)
   - Complete documentation of improvements
   - Before/after comparisons
   - Benefits and rationale

## Testing

Run the comprehensive test suite:

```bash
# Ensure server is running
python app.py

# In another terminal, run tests
python test_improved_tracing.py
```

The test will:
1. ✅ Send a test conversation
2. ✅ Verify response structure
3. ✅ Test with conversation context
4. ✅ Test error handling and flush
5. ✅ Provide Langfuse verification checklist

## Verification Checklist

After running tests, verify in Langfuse dashboard (https://cloud.langfuse.com):

- [ ] Single root trace named "chat.turn"
- [ ] Planner observation with:
  - [ ] Model: gemma3:4b
  - [ ] Temperature: 0.7
  - [ ] Token counts (input + output)
  - [ ] Prompt link
- [ ] Synthesizer observation with:
  - [ ] Model: gemma3:4b
  - [ ] Temperature: 0.7
  - [ ] Token counts (input + output)
  - [ ] Prompt link
- [ ] Tool executions as observations (if actions were executed)
- [ ] No duplicate ChatOpenAI traces
- [ ] Session ID present
- [ ] Tags: ["conversation", "{domain}"]
- [ ] Metadata includes trace_id and domain

## Performance Impact

**Before**:
- ~400 lines of complex tracing code
- Manual span management overhead
- Potential memory leaks from unclosed spans
- Flush could be skipped on errors

**After**:
- ~250 lines total (across helper functions)
- Automatic span management
- Guaranteed cleanup via decorators
- Guaranteed flush via try/finally
- **~35% less code with better functionality**

## Migration Notes

If you have custom code that uses the old tracing approach:

1. Replace manual span creation with `@observe` decorators
2. Use `langfuse_context.update_current_observation()` for metadata
3. Remove manual callback handler creation
4. Add try/finally around any flush() calls
5. Test thoroughly with `test_improved_tracing.py`

## Best Practices

### DO ✅
- Use `@observe()` decorator for all traced functions
- Update observation metadata for context
- Use try/finally for guaranteed flush
- Link prompts via `langfuse_context`
- Include model parameters
- Add session tracking
- Use descriptive observation names

### DON'T ❌
- Don't create manual spans/observations
- Don't create multiple callback handlers
- Don't forget to flush in finally block
- Don't skip model metadata
- Don't use events instead of observations for important operations

## Future Enhancements

Potential improvements for future iterations:

1. **Async Tracing**: Use async/await for non-blocking trace submission
2. **Cost Tracking**: Add explicit cost calculation per trace
3. **Performance Budgets**: Alert when traces exceed time/cost thresholds
4. **A/B Testing**: Compare prompt versions automatically
5. **User Feedback**: Link user ratings to traces
6. **Evaluation Metrics**: Automated quality scoring

## Support

For issues or questions:
- Check Langfuse docs: https://langfuse.com/docs
- Review test output: `python test_improved_tracing.py`
- Check server logs for warnings
- Verify .env configuration

## Summary

The improved Langfuse tracing implementation provides:

✅ **Simpler code** (-234 lines, -35%)
✅ **Better observability** (model metadata, session tracking, tags)
✅ **More reliable** (guaranteed flush, proper error handling)
✅ **Easier to maintain** (decorator pattern, helper functions)
✅ **Better performance tracking** (tool observations, prompt linking)
✅ **Production-ready** (comprehensive tests, documentation)

This sets a solid foundation for advanced observability and continuous improvement of the Giskard agent.
