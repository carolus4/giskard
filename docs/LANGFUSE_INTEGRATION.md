# Langfuse Integration for Giskard Agent

This document explains how to set up and use Langfuse observability with your Giskard agent.

## Overview

Langfuse provides comprehensive observability for your Giskard agent, including:

- **Trace Tracking**: Complete visibility into agent execution flows
- **LLM Monitoring**: Detailed tracking of all LLM calls and responses
- **Performance Metrics**: Latency, token usage, and cost tracking
- **Error Tracking**: Automatic capture of errors and exceptions
- **User Analytics**: User behavior and interaction patterns

## Quick Start

### 1. Install and Configure

Run the setup script:

```bash
./setup_langfuse.sh
```

This will:
- Install the Langfuse SDK
- Guide you through environment variable setup
- Test the integration

### 2. Manual Setup

If you prefer manual setup:

```bash
# Install Langfuse and dependencies
pip install langfuse>=3.0.0 python-dotenv>=1.0.0

# Option A: Use .env file (Recommended)
cp env.example .env
# Edit .env with your API keys from https://cloud.langfuse.com

# Option B: Set environment variables
export LANGFUSE_PUBLIC_KEY="your-public-key"
export LANGFUSE_SECRET_KEY="your-secret-key"
export LANGFUSE_HOST="https://cloud.langfuse.com"  # Optional

# Test the integration
python test_langfuse_integration.py
```

## What's Being Traced

### 1. Router LLM Calls
- **Input**: User messages and conversation context
- **Output**: Tool decisions and assistant responses
- **Metadata**: Trace ID, user ID, session information

### 2. Tool Execution
- **Tool Calls**: All tool invocations with arguments
- **Results**: Tool execution results and errors
- **Performance**: Execution time and success rates

### 3. Synthesizer LLM Calls
- **Input**: Tool results and conversation context
- **Output**: Final assistant responses
- **Context**: Complete conversation history

### 4. Complete Workflows
- **Trace Hierarchy**: Nested traces for complex operations
- **State Management**: Agent state transitions
- **Error Handling**: Exception tracking and fallback behavior

## Configuration

### Using .env Files (Recommended)

The easiest way to configure Langfuse is using a `.env` file:

1. **Copy the example file**:
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` with your API keys**:
   ```bash
   # Get your keys from https://cloud.langfuse.com
   LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key-here
   LANGFUSE_SECRET_KEY=sk-lf-your-secret-key-here
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

3. **The `.env` file is automatically loaded** when the application starts.

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `LANGFUSE_PUBLIC_KEY` | Your Langfuse public key | Yes | - |
| `LANGFUSE_SECRET_KEY` | Your Langfuse secret key | Yes | - |
| `LANGFUSE_HOST` | Langfuse server URL | No | `https://cloud.langfuse.com` |

### Security Notes

- **Never commit `.env` files** to version control
- **Add `.env` to `.gitignore`** (already included in the project)
- **Use different keys** for development and production
- **Rotate keys regularly** for security

### Langfuse Configuration

The integration uses `config/langfuse_config.py` for centralized configuration:

```python
from config.langfuse_config import langfuse_config

# Check if Langfuse is enabled
if langfuse_config.enabled:
    print("Langfuse is configured and ready")

# Get a callback handler for tracing
handler = langfuse_config.get_callback_handler(
    trace_id="my-trace-123",
    user_id="user-456"
)

# Flush pending events
langfuse_config.flush()
```

## Integration Points

### 1. Router Integration

The router (`orchestrator/tools/router.py`) automatically traces:
- LLM calls for tool decision making
- Tool argument parsing and validation
- Error handling and fallback behavior

### 2. Orchestrator Integration

The main orchestrator (`orchestrator/orchestrator.py`) traces:
- Complete workflow execution
- State transitions between nodes
- Error propagation and handling

### 3. LangGraph Integration

The LangGraph orchestrator (`orchestrator/langgraph_orchestrator.py`) traces:
- Graph node execution
- Message passing between nodes
- Tool execution within the graph

## Viewing Traces

### 1. Langfuse Dashboard

Visit [https://cloud.langfuse.com](https://cloud.langfuse.com) to view:
- **Traces**: Complete execution flows
- **Sessions**: User conversation sessions
- **Analytics**: Performance and usage metrics
- **Evaluations**: Model performance analysis

### 2. Trace Structure

Each agent execution creates a trace with:
```
Trace (User Input)
├── Router LLM Call
│   ├── Input: User message
│   ├── Prompt: Router prompt template
│   └── Output: Tool decision
├── Tool Execution
│   ├── Tool: Tool name and arguments
│   └── Result: Execution result
└── Synthesizer LLM Call
    ├── Input: Tool results
    ├── Prompt: Synthesis prompt
    └── Output: Final response
```

## Advanced Usage

### 1. Custom Trace Attributes

Add custom attributes to traces:

```python
# In your agent code
handler = langfuse_config.get_callback_handler(
    trace_id="custom-trace",
    user_id="user-123"
)

# Add custom metadata
handler.metadata = {
    "custom_attribute": "value",
    "experiment_id": "exp-001"
}
```

### 2. Trace Grouping

Group related operations:

```python
# Use the same trace_id for related operations
trace_id = f"session-{session_id}"

# All operations in this session will be grouped
router_output = router.plan_actions(input_text, trace_id=trace_id)
```

### 3. Performance Monitoring

Monitor key metrics:
- **Latency**: Time per LLM call and total execution
- **Token Usage**: Input/output tokens per model
- **Cost**: Estimated costs based on token usage
- **Success Rate**: Percentage of successful executions

## Troubleshooting

### Common Issues

1. **"Langfuse not configured"**
   - Check environment variables are set
   - Verify API keys are correct
   - Ensure network connectivity to Langfuse

2. **"Failed to create callback handler"**
   - Check Langfuse SDK installation
   - Verify API key permissions
   - Check for network issues

3. **"No traces appearing in dashboard"**
   - Ensure `langfuse_config.flush()` is called
   - Check trace IDs are being passed correctly
   - Verify API keys have write permissions

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger("langfuse").setLevel(logging.DEBUG)
```

### Testing Integration

Run the test script to verify everything works:

```bash
python test_langfuse_integration.py
```

## Best Practices

### 1. Trace Naming
- Use descriptive trace IDs: `session-{user_id}-{timestamp}`
- Include context in trace names: `task-creation-{task_id}`

### 2. User Tracking
- Always pass user IDs for user analytics
- Group traces by user sessions
- Track user behavior patterns

### 3. Error Handling
- Ensure traces are created even on errors
- Include error context in trace metadata
- Use fallback behavior when Langfuse is unavailable

### 4. Performance
- Call `flush()` after important operations
- Don't block on Langfuse API calls
- Use async operations for high-volume scenarios

## Security Considerations

- **API Keys**: Store securely, never commit to version control
- **Data Privacy**: Review what data is being sent to Langfuse
- **Network**: Use HTTPS for all communications
- **Access Control**: Limit API key permissions to minimum required

## Support

- **Documentation**: [Langfuse Docs](https://langfuse.com/docs)
- **Community**: [Langfuse Discord](https://discord.gg/langfuse)
- **Issues**: Report issues in the Giskard repository

## Example Usage

```python
from orchestrator.langgraph_orchestrator import LangGraphOrchestrator

# Initialize orchestrator (Langfuse is automatically integrated)
orchestrator = LangGraphOrchestrator()

# Run agent with automatic tracing
result = orchestrator.run(
    input_text="Create a task to review the quarterly report",
    session_id="user-session-123",
    domain="productivity"
)

# Traces are automatically sent to Langfuse
# View them at https://cloud.langfuse.com
```

That's it! Your Giskard agent now has comprehensive observability through Langfuse. 🎉
