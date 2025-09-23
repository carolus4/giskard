# Agent Orchestration Layer

## Overview

The Agent Orchestration Layer enables Giskard's chat UI to perform task operations through a single, server-side orchestrator endpoint that calls Ollama and invokes existing Task APIs. This is a minimal, stateless implementation focused on the `create_task` tool.

## Architecture

```
Chat UI → POST /api/agent/step → AgentService → Ollama → Tool Execution → Task API
```

### Components

1. **AgentService** (`utils/agent_service.py`) - Core orchestration logic
2. **AgentMetrics** (`utils/agent_metrics.py`) - Observability and metrics
3. **API Endpoints** (`api/routes_v2.py`) - HTTP interface
4. **Tool Schema** - Structured prompt for Ollama with tool definitions

## API Endpoints

### POST /api/agent/step

Process a single agent step with chat messages and UI context.

**Request:**
```json
{
  "messages": [
    {"type": "user", "content": "Create a task to review the quarterly report"},
    {"type": "assistant", "content": "I'll help you with that."}
  ],
  "ui_context": {
    "current_tasks": [],
    "user_preferences": {}
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Agent step completed",
  "data": {
    "assistant_text": "✅ Created task: Review quarterly report",
    "side_effects": [
      {
        "success": true,
        "action": "create_task",
        "task_id": 123,
        "task_title": "Review quarterly report",
        "message": "Created task: Review quarterly report"
      }
    ],
    "undo_token": "0280969a-7bbd-4250-8...",
    "success": true
  }
}
```

### POST /api/agent/undo

Undo the last agent mutation using an undo token.

**Request:**
```json
{
  "undo_token": "0280969a-7bbd-4250-8..."
}
```

**Response:**
```json
{
  "success": true,
  "message": "Undo completed",
  "data": {
    "success": true,
    "message": "Undid creation of task: Review quarterly report",
    "undone_task_id": 123
  }
}
```

### GET /api/agent/metrics

Get agent metrics and observability data.

**Response:**
```json
{
  "success": true,
  "message": "Metrics retrieved",
  "data": {
    "metrics": {
      "requests_total": 15,
      "requests_successful": 14,
      "requests_failed": 1,
      "tool_calls_total": 12,
      "create_task_calls": 12,
      "undo_operations": 3,
      "average_response_time": 2.5,
      "error_counts": {
        "ConnectionError": 1
      }
    }
  }
}
```

## Tool Schema

The agent uses a structured prompt with tool definitions:

```
You have access to the following tools:

1. create_task: Create a new task
   - title (string, required): The task title
   - description (string, optional): Task description
   - project (string, optional): Project name
   - categories (array of strings, optional): Task categories

When you want to create a task, respond with:
TOOL_CALL: create_task
ARGUMENTS: {"title": "Task title", "description": "Optional description", "project": "Optional project", "categories": ["category1", "category2"]}
```

## Features

### 1. Tool Execution
- **create_task**: Creates new tasks with validation
- Structured tool call parsing from Ollama responses
- Server-side validation of tool arguments

### 2. Idempotency
- Prevents duplicate task creation within the same session
- Title-based duplicate detection
- Graceful handling of existing tasks

### 3. Undo Functionality
- Server-owned undo tokens for each mutation
- Simple in-memory undo storage (stateless per request)
- Support for undoing task creation

### 4. Observability
- Request/response logging
- Performance metrics (response time, success rate)
- Error tracking and categorization
- Tool call statistics

### 5. Error Handling
- Graceful degradation when Ollama is unavailable
- Comprehensive error logging
- User-friendly error messages

## Usage Examples

### Basic Task Creation

```python
from utils.agent_service import AgentService

agent_service = AgentService()

messages = [
    {'type': 'user', 'content': 'Create a task to review the quarterly report'}
]

result = agent_service.process_step(messages, {})
print(result['assistant_text'])  # "✅ Created task: Review quarterly report"
```

### Undo Operation

```python
undo_token = result['undo_token']
undo_result = agent_service.undo_last_mutation(undo_token)
print(undo_result['message'])  # "Undid creation of task: Review quarterly report"
```

### Metrics Collection

```python
from utils.agent_metrics import agent_metrics

metrics = agent_metrics.get_metrics()
print(f"Total requests: {metrics['requests_total']}")
print(f"Success rate: {metrics['requests_successful'] / metrics['requests_total'] * 100:.1f}%")
```

## Testing

### Unit Tests
```bash
python -m unittest test_agent_integration.py
```

### Simple Test
```bash
python test_agent_simple.py
```

### Manual Testing
```bash
# Start the server
python app.py

# Test agent step
curl -X POST http://localhost:5001/api/agent/step \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"type": "user", "content": "Create a test task"}],
    "ui_context": {}
  }'

# Test undo
curl -X POST http://localhost:5001/api/agent/undo \
  -H "Content-Type: application/json" \
  -d '{"undo_token": "your-undo-token"}'

# Get metrics
curl http://localhost:5001/api/agent/metrics
```

## Configuration

### Ollama Configuration
The agent uses the existing Ollama configuration from `config/ollama_config.py`:
- Model: `gemma3:4b` (configurable)
- Temperature: 0.7 (for chat)
- Request timeout: 100 seconds

### Metrics Configuration
- Maximum response time history: 100 requests
- Automatic metrics reset capability
- Error categorization

## Limitations (MVP)

1. **Stateless**: No persistent session storage
2. **Single Tool**: Only `create_task` tool implemented
3. **Simple Undo**: In-memory undo tokens only
4. **No Streaming**: Synchronous requests only
5. **No Multi-tool Planning**: Single tool call per request

## Future Enhancements

1. **Persistent Sessions**: Thread-based conversation storage
2. **Additional Tools**: Update, complete, reorder tasks
3. **Streaming Support**: SSE for real-time responses
4. **Multi-tool Planning**: ReAct-style tool chaining
5. **Advanced Undo**: Persistent undo history
6. **Agent Memory**: Long-term conversation context

## Troubleshooting

### Common Issues

1. **Ollama Not Available**
   - Check if Ollama is running: `curl http://localhost:11434/api/tags`
   - Start Ollama: `ollama serve`

2. **Tool Call Parsing Errors**
   - Check Ollama response format
   - Verify tool schema in prompt

3. **Undo Token Issues**
   - Tokens are session-scoped and in-memory
   - Restart server clears all undo tokens

4. **Performance Issues**
   - Check Ollama model size and GPU usage
   - Monitor response times in metrics

### Debug Mode

Enable detailed logging:
```python
import logging
logging.getLogger('utils.agent_service').setLevel(logging.DEBUG)
```

## Security Considerations

1. **Input Validation**: All tool arguments are validated
2. **Rate Limiting**: Consider implementing for production
3. **Authentication**: Add authentication for production use
4. **Error Information**: Avoid exposing sensitive error details

## Performance

- **Response Time**: 2-6 seconds typical (depends on Ollama model)
- **Memory Usage**: Minimal (stateless design)
- **Concurrency**: Thread-safe for multiple requests
- **Scalability**: Limited by Ollama performance
