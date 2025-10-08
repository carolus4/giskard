# Session-Based Data Model Design

## Problem Statement

The current data model incorrectly uses `trace_id` as both:
- **Session identifier** (grouping multiple conversations)
- **Individual trace identifier** (single LLM interaction)

This creates confusion and prevents proper session management.

## Proposed Solution

### 1. **Session Table**
```sql
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,                    -- session_id (UUID)
    user_id TEXT,                          -- Optional user identifier
    created_at TEXT NOT NULL,              -- Session start time
    updated_at TEXT NOT NULL,              -- Last activity time
    metadata TEXT DEFAULT '{}'             -- Additional session data
);
```

### 2. **Updated Agent Steps Table**
```sql
CREATE TABLE agent_steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,              -- Links to sessions table
    trace_id TEXT NOT NULL,                -- Individual trace identifier
    step_number INTEGER NOT NULL,
    step_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    input_data TEXT DEFAULT '{}',
    output_data TEXT DEFAULT '{}',
    rendered_prompt TEXT,
    llm_input TEXT DEFAULT '{}',
    llm_output TEXT,
    llm_model TEXT,
    error TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

### 3. **Trace Table** (New)
```sql
CREATE TABLE traces (
    id TEXT PRIMARY KEY,                   -- trace_id (UUID)
    session_id TEXT NOT NULL,              -- Links to sessions table
    user_message TEXT NOT NULL,            -- User's input message
    assistant_response TEXT,               -- Assistant's response
    created_at TEXT NOT NULL,              -- Trace start time
    completed_at TEXT,                      -- Trace completion time
    status TEXT DEFAULT 'in_progress',     -- in_progress, completed, failed
    metadata TEXT DEFAULT '{}',           -- Additional trace data
    
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

## Data Model Hierarchy

```
Session (session_id)
├── Trace 1 (trace_id_1)
│   ├── Step 1: planner-node
│   ├── Step 2: action-node (optional)
│   └── Step 3: synthesizer-node
├── Trace 2 (trace_id_2)
│   ├── Step 1: planner-node
│   ├── Step 2: action-node (optional)
│   └── Step 3: synthesizer-node
└── Trace N (trace_id_N)
    └── ...
```

## API Changes

### Current API
```javascript
// Current: trace_id used as session identifier
POST /api/agent/conversation
{
  "input_text": "What should I focus on today?",
  "session_id": "chat-1759940138959-smagnz1tz",  // This is actually a trace_id
  "trace_id": "chat-1759940138959-smagnz1tz"     // Same value!
}
```

### Proposed API
```javascript
// New: Proper session/trace separation
POST /api/agent/conversation
{
  "input_text": "What should I focus on today?",
  "session_id": "session-abc123-def456-ghi789",  // Persistent session
  "trace_id": "trace-xyz789-uvw456-rst123"        // Individual trace
}
```

## Langfuse Integration

### Current (Incorrect)
```
Langfuse Dashboard:
├── Trace: chat-1759940138959-smagnz1tz
├── Trace: chat-1759940138960-smagnz1tz  
└── Trace: chat-1759940138961-smagnz1tz
```

### Proposed (Correct)
```
Langfuse Dashboard:
├── Session: session-abc123-def456-ghi789
│   ├── Trace: trace-xyz789-uvw456-rst123
│   ├── Trace: trace-abc456-def789-ghi012
│   └── Trace: trace-xyz012-uvw345-rst678
```

## Benefits

1. **Clear Separation**: Sessions group conversations, traces track individual interactions
2. **Better Analytics**: Session-level metrics and user behavior tracking
3. **Proper Langfuse Integration**: Each trace is a single LLM interaction
4. **Scalability**: Support for long-running sessions with multiple traces
5. **Debugging**: Easier to trace issues across session boundaries

## Migration Strategy

1. **Create new tables** (sessions, traces)
2. **Migrate existing data** from agent_steps to new structure
3. **Update API endpoints** to use session_id/trace_id separation
4. **Update Langfuse integration** to use proper trace hierarchy
5. **Test with existing data** to ensure no data loss

## Implementation Plan

1. ✅ Analyze current model
2. 🔄 Design session-based model
3. ⏳ Update database schema
4. ⏳ Update agent endpoints
5. ⏳ Update Langfuse integration
6. ⏳ Test new model
