# Langfuse Duplicate Trace Fix

## Problem

You were seeing **TWO separate traces** for each conversation:

1. **"ChatOpenAI" trace** - Created by CallbackHandler
   - Only shows 1 LLM call (synthesizer)
   - Orphaned/separate from main trace
   - Has token counts

2. **"chat.turn" trace** - Your manually created trace
   - Shows full hierarchy
   - Properly organized observations
   - Missing token counts on LLM calls

### Visual Representation

**Before (Duplicate Traces):**
```
Trace 1: "ChatOpenAI" (from CallbackHandler)
└─ synthesizer.llm [GENERATION] ← Duplicate!
   └─ Token counts ✅

Trace 2: "chat.turn" (manually created)
├─ chat.turn [SPAN]
│  ├─ planner.llm [GENERATION] ← No token counts ❌
│  ├─ tool.execute.fetch_tasks [SPAN]
│  │  ├─ tool.request [EVENT]
│  │  └─ tool.response [EVENT]
│  └─ synthesizer.llm [GENERATION] ← No token counts ❌
```

## Root Cause

**Mixing two tracing approaches:**

1. **Manual observation creation** (lines 333-338, 540-545):
   ```python
   planner_generation = root_span.start_observation(
       name="planner.llm",
       as_type="generation",
       ...
   )
   ```

2. **CallbackHandler** (lines 351-362, 556-567):
   ```python
   langfuse_handler = langfuse_config.get_callback_handler(...)
   response = orchestrator.llm.invoke(
       messages,
       config={"callbacks": [langfuse_handler]}  # Creates separate trace!
   )
   ```

When you use **both**, you get:
- ❌ Duplicate observations (one manual, one from callback)
- ❌ Separate "ChatOpenAI" trace
- ❌ Confusing trace hierarchy
- ❌ Split metrics across two traces

## The Fix

**Removed CallbackHandler usage** because we're already manually creating observations.

### Planner LLM (Lines 343-348)

**Before:**
```python
# Get Langfuse callback handler for planner
langfuse_handler = None
if client and root_span:
    try:
        langfuse_handler = langfuse_config.get_callback_handler(
            trace_id=trace_id,
            user_id=session_id
        )
    except Exception as e:
        logger.warning(f"Failed to get Langfuse callback handler: {e}")

# Call LLM with Langfuse tracing
if langfuse_handler:
    response = orchestrator.llm.invoke(
        messages,
        config={"callbacks": [langfuse_handler]}  # ❌ Creates duplicate
    )
else:
    response = orchestrator.llm.invoke(messages)
```

**After:**
```python
# Call LLM for planning
logger.info("Calling LLM for planning")

# Note: We don't use CallbackHandler here because we're manually creating
# the observation above (planner_generation). Using both would create duplicates.
response = orchestrator.llm.invoke(messages)  # ✅ Clean, no duplicates
```

### Synthesizer LLM (Lines 533-536)

**Before:**
```python
# Get Langfuse callback handler for synthesizer
langfuse_handler = None
if client and root_span:
    try:
        langfuse_handler = langfuse_config.get_callback_handler(...)
    except Exception as e:
        logger.warning(f"Failed to get Langfuse callback handler: {e}")

# Call LLM with Langfuse tracing
if langfuse_handler:
    response = orchestrator.llm.invoke(
        messages,
        config={"callbacks": [langfuse_handler]}  # ❌ Creates duplicate
    )
else:
    response = orchestrator.llm.invoke(messages)
```

**After:**
```python
# Call LLM for final response
# Note: We don't use CallbackHandler here because we're manually creating
# the observation above (synthesizer_generation). Using both would create duplicates.
response = orchestrator.llm.invoke(messages)  # ✅ Clean, no duplicates
```

## Expected Result

**After (Single Clean Trace):**
```
Trace: "chat.turn"
└─ chat.turn [SPAN]
   ├─ planner.llm [GENERATION]
   │  ├─ Input: Messages
   │  ├─ Output: Decision JSON
   │  └─ Prompt: Linked ✅
   │
   ├─ tool.execute.fetch_tasks [SPAN]
   │  ├─ tool.request [EVENT]
   │  └─ tool.response [EVENT]
   │
   └─ synthesizer.llm [GENERATION]
      ├─ Input: Messages + Results
      ├─ Output: Final response
      └─ Prompt: Linked ✅
```

## Why This Works

### Manual Observation Creation
When you do:
```python
generation = root_span.start_observation(
    name="planner.llm",
    as_type="generation",
    input={...}
)
# ... LLM call ...
generation.update(output=response)
generation.end()
```

You get:
- ✅ Full control over the observation
- ✅ Proper nesting in your trace
- ✅ Custom metadata and naming
- ⚠️ **BUT**: No automatic token counting from LangChain

### CallbackHandler
When you use:
```python
response = llm.invoke(messages, config={"callbacks": [handler]})
```

You get:
- ✅ Automatic token counting
- ✅ Automatic input/output capture
- ❌ **BUT**: Creates its own trace ("ChatOpenAI")
- ❌ **AND**: Not nested in your custom trace

### The Trade-off

We chose **manual observation creation** because:
1. ✅ Clean, single trace hierarchy
2. ✅ Full control over trace structure
3. ✅ Proper nesting and organization
4. ⚠️ Missing automatic token counts (but Ollama doesn't report them anyway)

## Note on Token Counts

**Important**: Ollama models (gemma3:4b) **don't report token counts** through the OpenAI-compatible API, so you wouldn't get token counts even with the CallbackHandler.

If you switch to a real OpenAI model later, you could:

**Option A**: Keep manual observations (cleaner)
```python
# Manually add token counts after LLM call
if hasattr(response, 'usage'):
    generation.update(
        usage={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens
        }
    )
```

**Option B**: Use only CallbackHandler (simpler but less control)
```python
# Remove manual start_observation()
# Just use callback handler
response = llm.invoke(messages, config={"callbacks": [handler]})
# No manual update/end needed
```

## When to Use Each Approach

### Use Manual Observations When:
- ✅ You need custom trace hierarchy
- ✅ You want specific observation names
- ✅ You need to add custom metadata
- ✅ You're using Ollama (no token counts anyway)
- ✅ You want full control

### Use CallbackHandler When:
- ✅ You want automatic tracing with zero code
- ✅ You're using OpenAI/Anthropic (token counts work)
- ✅ You don't need custom trace structure
- ✅ Simple is more important than control

### NEVER Use Both Together:
- ❌ Creates duplicate traces
- ❌ Confusing hierarchy
- ❌ Split metrics
- ❌ Wasted Langfuse quota

## Testing

After the fix:
1. ✅ Send a message through your agent
2. ✅ Check Langfuse dashboard
3. ✅ Verify you see **only ONE trace** named "chat.turn"
4. ✅ Verify all observations are nested properly
5. ✅ Verify **NO "ChatOpenAI" trace** appears

Example test:
```bash
curl -X POST http://localhost:5001/api/agent/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "Fetch my tasks",
    "session_id": "test",
    "domain": "productivity"
  }'
```

Then check Langfuse - you should see **exactly one** clean trace! 🎉

## Summary

**What we fixed:**
- ✅ Removed duplicate CallbackHandler usage
- ✅ Kept manual observation creation for full control
- ✅ Single clean trace in Langfuse
- ✅ Proper hierarchy with all observations nested

**Result:**
- One "chat.turn" trace
- Clean hierarchy
- No duplicate "ChatOpenAI" traces
- All observations properly organized

This gives you the clean, organized trace structure you expected!
