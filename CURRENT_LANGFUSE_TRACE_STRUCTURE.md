# Current Langfuse Trace Structure

## Overview

This document describes the actual Langfuse tracing implementation currently running in your Giskard agent (as of the code in `server/routes/agent.py`).

## Trace Hierarchy

```
📊 Trace: "chat.turn" (Root Trace Context)
│   - Type: TraceContext
│   - ID: trace_id (MD5 hash, 32 lowercase hex chars)
│   - Input: {input_text, session_id, domain}
│   - Created at: Line 250
│
└─── 🎯 Span: "chat.turn" (Root Span)
     │   - Type: Span
     │   - Parent: Root Trace Context
     │   - Input: {input_text, session_id, domain}
     │   - Created at: Line 318-322
     │
     ├─── 🤖 Generation: "planner.llm"
     │    │   - Type: Generation (Observation)
     │    │   - Parent: Root Span
     │    │   - Created at: Line 333-338
     │    │   - Input: {messages: [SystemMessage, ...context..., HumanMessage]}
     │    │   - Prompt: Langfuse prompt object (if available)
     │    │   - Model: gemma3:4b (via Ollama OpenAI-compatible endpoint)
     │    │   - LLM Call: Line 360-365 (with CallbackHandler)
     │    │   - Output: Planner decision JSON
     │    │   - Updated: Line 375 (output)
     │    │   - Ended: Line 379
     │    │
     │    └─── Additional Tracing:
     │         - Database Log: AgentStepDB (Line 404-415)
     │           - step_type: "planner_llm"
     │           - llm_model: "gemma3:4b"
     │           - rendered_prompt: Full compiled prompt
     │           - llm_input: Messages array
     │           - llm_output: Response content
     │
     ├─── ⚡ Span: "tool.execute.{action_name}" (for each action)
     │    │   - Type: Span
     │    │   - Parent: Root Span (✅ FIXED - now properly nested)
     │    │   - Created at: Line 447-450 (via root_span.start_span())
     │    │   - Input: {tool_name, tool_args}
     │    │   - Name: Dynamic (e.g., "tool.execute.create_task")
     │    │
     │    ├─── 📥 Event: "tool.request"
     │    │    - Type: Event
     │    │    - Parent: Tool Span
     │    │    - Created at: Line 453-456
     │    │    - Input: {tool_name, tool_args}
     │    │
     │    ├─── [Action Execution]
     │    │    - Actual tool execution: Line 462
     │    │    - orchestrator.action_executor.execute_action()
     │    │
     │    ├─── 📤 Event: "tool.response"
     │    │    - Type: Event
     │    │    - Parent: Tool Span
     │    │    - Created at: Line 467-470
     │    │    - Input: {success, result, error}
     │    │
     │    └─── Output & End
     │         - Update: Line 471 (output: {success, result})
     │         - End: Line 472
     │         - Database Log: AgentStepDB (Line 486-493)
     │           - step_type: "action_exec"
     │           - Multiple actions aggregated
     │
     └─── 🎨 Generation: "synthesizer.llm"
          │   - Type: Generation (Observation)
          │   - Parent: Root Span
          │   - Created at: Line 540-545
          │   - Input: {messages: [SystemMessage, ...context..., HumanMessage]}
          │   - Prompt: Langfuse prompt object (if available)
          │   - Model: gemma3:4b (via Ollama OpenAI-compatible endpoint)
          │   - LLM Call: Line 565-570 (with CallbackHandler)
          │   - Output: Final synthesized response
          │   - Updated: Line 575 (output)
          │   - Ended: Line 579
          │
          └─── Additional Tracing:
               - Database Log: AgentStepDB (Line 589-600)
                 - step_type: "synthesizer_llm"
                 - llm_model: "gemma3:4b"
                 - rendered_prompt: Full compiled prompt
                 - llm_input: Messages array
                 - llm_output: Response content
```

## Detailed Breakdown by Step

### Step 1: Planner LLM
- **Langfuse Trace Name**: `planner.llm`
- **Trace Type**: `generation`
- **Purpose**: Analyzes user input and decides which actions to take
- **Input**:
  - System message with compiled planner prompt
  - Conversation context (previous messages)
  - User message
- **Output**: JSON with `assistant_text` and `actions` array
- **Prompt Management**:
  - Tries to load from Langfuse first (label: "production")
  - Falls back to local file: `langfuse-prompts/planner.txt`
- **Database Logging**:
  - Table: `agent_steps`
  - Fields: trace_id, step_number, step_type, input_data, output_data, rendered_prompt, llm_input, llm_model, llm_output

### Step 2: Action Execution (Multiple Tool Spans)
- **Langfuse Trace Name**: `tool.execute.{action_name}` (one span per action)
- **Trace Type**: `span`
- **Purpose**: Executes each action decided by the planner
- **For Each Action**:
  - Creates a separate span
  - Logs "tool.request" event (input)
  - Executes the action via `orchestrator.action_executor.execute_action()`
  - Logs "tool.response" event (output)
  - Captures success/failure and result
- **Example Action Names**:
  - `tool.execute.create_task`
  - `tool.execute.update_task`
  - `tool.execute.search_tasks`
  - `tool.execute.no_op`
- **Database Logging**:
  - Single aggregated entry for all actions in this step
  - Table: `agent_steps`
  - Fields: trace_id, step_number, step_type='action_exec', input_data (all actions), output_data (all results)

### Step 3: Synthesizer LLM
- **Langfuse Trace Name**: `synthesizer.llm`
- **Trace Type**: `generation`
- **Purpose**: Creates natural language response based on action results
- **Input**:
  - System message with compiled synthesizer prompt
  - Conversation context
  - User message
  - Action results (embedded in system prompt)
- **Output**: Natural language response to user
- **Prompt Management**:
  - Tries to load from Langfuse first (label: "production")
  - Falls back to local file: `langfuse-prompts/synthesizer.txt`
- **Database Logging**:
  - Table: `agent_steps`
  - Fields: trace_id, step_number, step_type, input_data, output_data, rendered_prompt, llm_input, llm_model, llm_output

## Trace Lifecycle

### 1. Initialization (Lines 232-255)
```python
# Generate trace_id
trace_id = hashlib.md5(f"trace-{int(time.time())}".encode()).hexdigest()

# Create database trace record
trace = TraceDB.create(session_id, user_message, metadata)

# Create Langfuse trace context
langfuse_trace_context = langfuse_config.create_trace_context(
    name="chat.turn",
    trace_id=trace_id,
    user_id=session_id,
    input_data={...}
)
```

### 2. Root Span Creation (Lines 314-325)
```python
root_span = client.start_span(
    trace_context=langfuse_trace_context,
    name="chat.turn",
    input={input_text, session_id, domain}
)
```

### 3. Child Observations (Lines 327-580)
Each LLM call and tool execution creates child observations under the root span.

### 4. Finalization (Lines 613-632)
```python
# End root span
root_span.update(output={final_message, total_steps})
root_span.end()

# Update trace
client.update_current_trace(output={...})

# Mark database trace as completed
trace.mark_completed(response_content)

# Flush to Langfuse
langfuse_config.flush()
```

## Key Features

### ✅ What's Being Tracked

1. **Trace Context**
   - Unique trace ID per conversation turn
   - Session ID for multi-turn conversations
   - Domain metadata (chat, productivity, etc.)
   - User input and final output

2. **LLM Generations**
   - Planner and Synthesizer as separate generations
   - Full message history (system + context + user)
   - Token counts (via CallbackHandler)
   - Model: gemma3:4b
   - Prompt linking (when prompts exist in Langfuse)

3. **Tool Executions**
   - Individual spans for each tool call
   - Request and response events
   - Success/failure tracking
   - Execution results and errors

4. **Database Logging** (Parallel System)
   - Complete step-by-step history in SQLite
   - Full prompts and responses
   - Metadata for debugging
   - Query-able for analytics

### ⚠️ Limitations (Current Implementation)

1. **No Model Metadata in Observations**
   - Model name not explicitly set on observations
   - Temperature not tracked
   - Would require `langfuse_context.update_current_observation()`

2. **Tool Events vs Observations**
   - Tools use events instead of full observations
   - Events don't track duration as precisely
   - No hierarchical tool metrics

3. **Session Tracking**
   - Session ID passed but not set as trace attribute
   - Tags not applied to traces
   - Would require `langfuse_context.update_current_trace()`

4. **Prompt Linking**
   - Prompts passed but linking may not work consistently
   - Depends on prompt object format

## Langfuse Dashboard View

When you view traces in Langfuse, you should see:

```
Traces
└─ chat.turn (trace_id: abc123...)
   ├─ planner.llm [GENERATION]
   │  ├─ Input: System + Context + User messages
   │  ├─ Output: {"assistant_text": "...", "actions": [...]}
   │  └─ Tokens: Input + Output counts
   │
   ├─ tool.execute.create_task [SPAN]
   │  ├─ Event: tool.request
   │  ├─ Event: tool.response
   │  └─ Duration: X ms
   │
   └─ synthesizer.llm [GENERATION]
      ├─ Input: System + Context + User messages + Action results
      ├─ Output: "I've created the task..."
      └─ Tokens: Input + Output counts
```

## Configuration

### Langfuse Setup (config/langfuse_config.py)
- Environment variables: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`
- Client initialization with fallback
- Callback handler creation for LangChain integration
- Trace context creation

### Prompt Management (config/prompt_manager.py)
- Tries Langfuse first (with label "production")
- Falls back to local files in `langfuse-prompts/`
- Template variable compilation with `{{variable}}` syntax

### Database Logging (models/task_db.py, models/session_db.py)
- `AgentStepDB`: Step-by-step execution log
- `SessionDB`: User session tracking
- `TraceDB`: Conversation trace records

## Comparison: Current vs Proposed

| Feature | Current | Proposed (with decorators) |
|---------|---------|----------------------------|
| **Code Complexity** | High (manual span management) | Low (@observe decorators) |
| **Lines of Code** | ~850 lines | ~616 lines (-27%) |
| **Model Metadata** | ❌ Not tracked | ✅ Tracked automatically |
| **Session Tracking** | ⚠️ Partial (via trace_id) | ✅ Full (via context.update_current_trace) |
| **Tool Observations** | ⚠️ Events only | ✅ Full observations |
| **Prompt Linking** | ⚠️ Inconsistent | ✅ Reliable |
| **Error Handling** | ✅ Try-except blocks | ✅ Automatic via decorators |
| **Token Counting** | ✅ Via CallbackHandler | ✅ Automatic |
| **Maintainability** | ⚠️ Complex | ✅ Simple |

## Summary

Your current implementation provides:
- ✅ **Complete trace hierarchy** with root span and nested observations
- ✅ **LLM generation tracking** with token counts
- ✅ **Tool execution tracking** with events
- ✅ **Database logging** for persistence and queries
- ✅ **Prompt management** with Langfuse integration
- ✅ **Error handling** with fallbacks
- ✅ **Session tracking** via trace_id

The tracing works well but could be simplified with the decorator pattern (requires Langfuse 3.9+).
