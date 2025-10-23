# Classification Langfuse Integration Fixes

This document describes the fixes applied to integrate Langfuse tracing into the classification system and use Langfuse managed prompts.

## Issues Fixed

### 1. Langfuse Managed Prompts Not Being Used

**Problem**: The classification system was not properly using Langfuse managed prompts. The prompt was retrieved but not properly passed to Langfuse for reference tracking.

**Solution**:
- Created local fallback prompt file at [langfuse-prompts/classifier.txt](langfuse-prompts/classifier.txt)
- Fixed `_build_classification_prompt` to properly retrieve and pass prompt metadata
- Updated `_create_classification_observation` to pass the Langfuse prompt object for reference tracking

**Files Modified**:
- `utils/classification_service.py`: Updated `_build_classification_prompt` method
- `langfuse-prompts/classifier.txt`: Created new local fallback prompt

### 2. Incorrect Trace Hierarchy

**Problem**: The classification system was creating both a span AND an observation, creating unnecessary hierarchy that didn't follow the pattern from `LANGFUSE_TRACING_FIXES.md`.

**Solution**:
- Changed to create generation observations directly within the trace
- Removed separate span creation to avoid nested hierarchy
- Followed the pattern: `trace -> generation observation` (not `trace -> span -> observation`)

**Files Modified**:
- `utils/classification_service.py`: Updated `_create_classification_observation` to create generation directly in trace

### 3. Missing Langfuse Tracing

**Problem**: Classification runs were not creating Langfuse traces to track the classification process.

**Solution**:
- Updated `ClassificationManager._create_classification_trace_context` to create actual traces (not just context)
- Added trace finalization with results after batch processing
- Added proper error handling and logging for trace creation

**Files Modified**:
- `utils/classification_manager.py`:
  - Updated `_create_classification_trace_context` to create traces
  - Updated `_process_queue_batch` to finalize traces with results

## New Trace Structure

The classification system now creates traces following this hierarchy (matching the pattern from agent.py):

```
classification.batch (trace)
└── classification.batch (root span)
    ├── classifier.llm (generation observation) - Task 1
    ├── classifier.llm (generation observation) - Task 2
    └── classifier.llm (generation observation) - Task 3
```

**How it works:**
1. Create a trace context using `langfuse_config.create_trace_context()`
2. Create a root span using `client.start_span(trace_context=...)`
3. Create generation observations using `root_span.start_observation(as_type="generation")`
4. Update observations with results using `observation.update(...)`
5. **End observations** using `observation.end()` (critical!)
6. **End the root span** using `root_span.end()` (critical!)

**Important**: You must call `.end()` on all observations and spans for them to be sent to Langfuse!

Each generation observation includes:
- **Input**: Task title, description, and prompt text
- **Output**: Categories and raw LLM response
- **Prompt Reference**: Link to Langfuse managed prompt (if available)
- **Model**: gemma3:4b
- **Metadata**: Prompt source, name, and label
- **Usage**: Token counts with format `{"input": N, "output": N, "total": N, "unit": "TOKENS"}`

## Langfuse Managed Prompt Integration

### Prompt Hierarchy

The system tries to load prompts in this order:

1. **Langfuse (Cloud)**: Tries to fetch from Langfuse with label "production"
2. **Local File**: Falls back to `langfuse-prompts/classifier.txt`
3. **Hardcoded**: Ultimate fallback to hardcoded prompt in `config/prompts.py`

### Prompt Template Variables

The classifier prompt uses Langfuse template syntax:
- `{{task_text}}`: The task title and description

### Setting Up Langfuse Managed Prompt

To use Langfuse managed prompts:

1. Go to your Langfuse dashboard
2. Create a new prompt named "classifier"
3. Use the content from [langfuse-prompts/classifier.txt](langfuse-prompts/classifier.txt)
4. Set the label to "production"
5. The system will automatically use the Langfuse version and track which prompt version was used

## Key Changes Made

### ClassificationService Changes ([utils/classification_service.py](utils/classification_service.py))

1. **Updated `_build_classification_prompt`** (lines 311-333):
   - Added better logging for prompt source
   - Improved error handling for fallback scenarios

2. **Updated `_create_classification_observation`** (lines 239-285):
   - Uses `root_span.start_observation(as_type="generation")` like agent.py
   - Properly passes Langfuse prompt object for reference tracking
   - Added metadata about prompt source, name, and label
   - Improved error logging with traceback

3. **Updated `_update_classification_observation`** (lines 287-309):
   - Changed token format to match agent.py: `{"input": N, "output": N, "total": N, "unit": "TOKENS"}`
   - Added debug logging for token counts

4. **Updated `classify_task`** (lines 118-137):
   - Added `observation.end()` call after updating the observation
   - This is **critical** - observations must be ended before they're sent to Langfuse
   - Follows the same pattern as agent.py

5. **Updated method signatures**:
   - `classify_task`: Changed `trace_context` parameter to `root_span`
   - `classify_tasks_batch`: Changed `trace_context` parameter to `root_span`

### ClassificationManager Changes ([utils/classification_manager.py](utils/classification_manager.py))

1. **Updated `_create_classification_trace_context`** (lines 155-208):
   - Creates trace context using `langfuse_config.create_trace_context()`
   - Creates root span using `client.start_span(trace_context=...)`
   - Generates unique trace ID using hashlib
   - Follows the same pattern as agent.py
   - Added proper metadata for batch processing
   - Improved error logging with traceback

2. **Updated `_process_queue_batch`** (lines 233-278):
   - Changed variable name from `trace_context` to `root_span` for clarity
   - Passes root span to classification service
   - Added span finalization with output results
   - Added `root_span.end()` call after updating - **critical for sending to Langfuse**
   - Added proper error handling for span updates

## Testing

Run the test script to verify the integration:

```bash
python test_classification_langfuse.py
```

This will test:
1. Single task classification with Langfuse tracing
2. Batch classification with Langfuse tracing
3. Prompt loading from Langfuse (or fallback)
4. Proper trace hierarchy
5. Token counting
6. Prompt reference tracking

## Expected Langfuse Output

After running classification, you should see in Langfuse:

1. **Trace**: Named "classification.batch" with:
   - Input: Batch size, task IDs, task titles
   - Output: Updated count, total tasks, results
   - Metadata: Batch size, processing type

2. **Generation Observations**: One for each task with:
   - Name: "classifier.llm"
   - Input: Task title, description, prompt text
   - Output: Categories, raw response
   - Prompt: Reference to Langfuse managed prompt (if used)
   - Model: gemma3:4b
   - Usage: Token counts
   - Metadata: Prompt source, name, label

3. **Prompt Reference**: If using Langfuse managed prompt, you'll see:
   - Which prompt version was used
   - Link to the prompt in Langfuse
   - Ability to compare across prompt versions

## Benefits

1. **Prompt Version Tracking**: Know exactly which prompt version produced which results
2. **A/B Testing**: Easy to test different prompt versions by changing the label
3. **Proper Token Counting**: All LLM calls now have accurate token usage tracking
4. **Clean Hierarchy**: Simple trace structure for easy debugging
5. **Better Observability**: Full visibility into classification process in Langfuse
6. **Fallback Safety**: Local prompts ensure system works even if Langfuse is unavailable

## Migration Notes

### For Existing Deployments

1. Add the Langfuse managed prompt to your Langfuse dashboard (optional)
2. The local fallback ensures backward compatibility
3. No database migrations required
4. Token counting works automatically

### Environment Variables

Make sure these are set in your `.env`:
```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com  # Optional, defaults to cloud
```

If not set, the system will:
- Log a warning
- Continue working without Langfuse tracing
- Use local prompt files

## Troubleshooting

### Traces Not Appearing in Langfuse

1. Check environment variables are set correctly
2. Verify `langfuse_config.enabled` is `True`
3. Check logs for trace creation errors
4. Run `langfuse_config.flush()` to force sending events

### Prompt Not Loading from Langfuse

1. Check prompt exists in Langfuse with correct name "classifier"
2. Verify label is set to "production"
3. Check Langfuse API keys are valid
4. System will automatically fall back to local prompt file

### Token Counts Not Showing

1. Verify metrics dict is properly returned from `_send_to_ollama`
2. Check `_update_classification_observation` is being called
3. Ensure observation object is valid

## Related Documentation

- [LANGFUSE_TRACING_FIXES.md](LANGFUSE_TRACING_FIXES.md) - Main tracing fixes for chat system
- [CURRENT_LANGFUSE_TRACE_STRUCTURE.md](CURRENT_LANGFUSE_TRACE_STRUCTURE.md) - Current trace structure
- [PROMPT_MANAGEMENT_IMPLEMENTATION.md](PROMPT_MANAGEMENT_IMPLEMENTATION.md) - Prompt management system
