# Langfuse Tracing Fixes

This document describes the fixes applied to resolve Langfuse tracing issues in the Giskard agent.

## Issues Fixed

### 1. Extra "ChatOpenAI" traces without full lineage but with token count

**Problem**: The router was creating separate ChatOpenAI traces that weren't properly nested under the main conversation trace.

**Solution**: Removed separate Langfuse tracing from the router's `plan_actions` method. The router now executes without creating its own traces, allowing the main conversation flow to handle all tracing.

**Files Modified**:
- `orchestrator/tools/router.py`: Removed Langfuse callback handler creation and import

### 2. "synthesize" trace with full lineage but no token count

**Problem**: The synthesizer was creating a separate "synthesize" span instead of using the proper trace hierarchy.

**Solution**: Changed the synthesizer to create a generation observation directly within the root span instead of creating a separate span.

**Files Modified**:
- `server/routes/agent.py`: Replaced separate synthesizer span with direct observation within root span

### 3. Trace name should be "chat.turn" instead of "synthesize"

**Problem**: The synthesizer was creating a separate span named "synthesize".

**Solution**: The root span is now properly named "chat.turn" and the synthesizer is an observation within it.

### 4. Empty "chat.turn" span within "synthesize"

**Problem**: Confusing trace hierarchy with nested spans.

**Solution**: Simplified the hierarchy to have a single root "chat.turn" span with observations for each LLM call.

## New Trace Structure

The fixed trace structure now follows this hierarchy:

```
chat.turn (root span)
├── planner.llm (generation observation)
└── synthesizer.llm (generation observation)
```

## Key Changes Made

### Router Changes (`orchestrator/tools/router.py`)

1. **Removed Langfuse import**: No longer imports `langfuse_config`
2. **Simplified `plan_actions` method**: Removed separate callback handler creation
3. **Direct chain execution**: Router chain now executes without additional tracing

### Agent Route Changes (`server/routes/agent.py`)

1. **Planner integration**: Planner now creates generation observation directly within root span
2. **Synthesizer integration**: Synthesizer now creates generation observation directly within root span
3. **Removed separate spans**: No more separate "plan" or "synthesize" spans
4. **Proper cleanup**: Removed references to separate spans in cleanup code

## Benefits

1. **Proper token counting**: All LLM calls now have proper token counting within the main trace
2. **Clean hierarchy**: Single root trace with observations for each LLM call
3. **No duplicate traces**: Eliminated extra ChatOpenAI traces
4. **Better observability**: Clear trace structure for debugging and monitoring

## Testing

Run the test script to verify the fixes:

```bash
python test_tracing_fixes.py
```

This will test the conversation flow and verify that:
- Only one root "chat.turn" trace is created
- Planner and synthesizer are observations within the root trace
- No separate ChatOpenAI traces are created
- Token counting works properly

## Expected Langfuse Output

After these fixes, you should see in Langfuse:

1. **Single root trace**: Named "chat.turn" with proper input/output
2. **Two observations**: 
   - `planner.llm` with token counts and prompt reference
   - `synthesizer.llm` with token counts and prompt reference
3. **No separate traces**: No extra ChatOpenAI or synthesize traces
4. **Proper lineage**: All operations nested under the main conversation trace





