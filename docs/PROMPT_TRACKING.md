# Prompt Tracking System

A comprehensive system for tracking and analyzing prompt performance over time, designed to help you optimize your AI prompts and understand their effectiveness.

## Features

- **Centralized Prompt Registry**: Store and manage all your prompts with version control
- **Performance Tracking**: Monitor execution times, success rates, and output quality
- **Version Comparison**: Compare performance across different prompt versions
- **Trend Analysis**: Track performance improvements over time
- **Export Capabilities**: Export data for external analysis

## Quick Start

### 1. List Available Prompts

```bash
python scripts/prompt_manager.py list
```

### 2. View Prompt Details

```bash
python scripts/prompt_manager.py show coaching_system
python scripts/prompt_manager.py show coaching_system --version 1.0
```

### 3. Check Performance Metrics

```bash
python scripts/prompt_manager.py performance coaching_system
python scripts/prompt_manager.py performance coaching_system --days 7
```

### 4. Compare Versions

```bash
python scripts/prompt_manager.py compare coaching_system
```

### 5. View Trends

```bash
python scripts/prompt_manager.py trends coaching_system --days 30
```

### 6. Create New Prompts

```bash
python scripts/prompt_manager.py create
```

### 7. Export Data

```bash
python scripts/prompt_manager.py export --prompt coaching_system --format json
python scripts/prompt_manager.py export --format csv
```

## Prompt Attributes

Each prompt in the system includes the following attributes:

- **Name**: Unique identifier for the prompt
- **Version**: Version number (e.g., "1.0", "1.1")
- **Goal**: One-sentence description of the prompt's purpose
- **Model**: AI model name and version (e.g., "llama3.1:8b")
- **Temperature**: Randomness parameter (0-1)
- **Token Limit**: Maximum tokens for the response
- **Top-K**: Number of top tokens to consider
- **Top-P**: Nucleus sampling parameter (0-1)
- **Prompt**: The full prompt text
- **Output**: Last output (if any)
- **Created At**: Timestamp when the prompt was created

## Performance Metrics

The system tracks the following performance metrics:

- **Execution Time**: How long the prompt took to execute (milliseconds)
- **Token Count**: Number of tokens in the response
- **Output Length**: Character count of the response
- **Success Rate**: Percentage of successful executions
- **Quality Score**: User-provided quality rating (1-10 scale)
- **User Feedback**: Optional feedback on the output quality

## Data Storage

All data is stored in JSON files in the `data/` directory:

- `prompt_registry.json`: Prompt definitions and configurations
- `prompt_performance.json`: Execution logs and performance data
- `prompt_metrics.json`: Cached performance metrics for quick access

## Programmatic Usage

### Using the Prompt Registry

```python
from config.prompt_registry import prompt_registry, PromptConfig

# Get a prompt
coaching_prompt = prompt_registry.get_latest_prompt("coaching_system")

# Create a new prompt
new_prompt = PromptConfig(
    name="my_prompt",
    version="1.0",
    goal="Do something useful",
    model="llama3.1:8b",
    temperature=0.7,
    token_limit=500,
    prompt="Your prompt text here"
)

# Register the prompt
prompt_registry.register_prompt(new_prompt)
```

### Using Performance Tracking

```python
from utils.prompt_performance_tracker import performance_tracker, PerformanceMetrics

# Log a prompt execution
metrics = PerformanceMetrics(
    execution_time_ms=1200,
    token_count=150,
    output_length=800,
    success=True,
    quality_score=8.5
)

performance_tracker.log_execution(
    prompt_name="coaching_system",
    prompt_version="1.0",
    output="The AI response here",
    metrics=metrics,
    input_data={"user_input": "Help me with my tasks"}
)

# Get performance summary
summary = performance_tracker.get_performance_summary("coaching_system", days=30)
print(f"Success rate: {summary['success_rate']:.1%}")
```

### Using the Updated Configuration

```python
from config.ollama_config import get_chat_config, get_classification_config

# Get current configuration based on latest prompts
chat_config = get_chat_config()
classification_config = get_classification_config()

# Use in your Ollama API calls
import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": chat_config["model"],
        "prompt": "Your prompt here",
        "stream": chat_config["stream"],
        "options": chat_config["options"]
    }
)
```

## Example: Running the Demo

```bash
python examples/prompt_tracking_example.py
```

This will:
1. Show available prompts
2. Simulate some prompt executions
3. Display performance summaries
4. Show version comparisons
5. Create a custom prompt example

## Integration with Existing Code

The new system is backward compatible with your existing code. The old `prompts.py` file still works, but now uses the registry system under the hood.

### Before (Old Way)
```python
from config.prompts import COACHING_SYSTEM_PROMPT
prompt = COACHING_SYSTEM_PROMPT.format(task_context="My tasks...")
```

### After (New Way)
```python
from config.prompts import get_coaching_prompt
prompt = get_coaching_prompt("My tasks...")
```

Both approaches work, but the new way gives you access to the tracking system.

## Best Practices

1. **Version Your Prompts**: Always increment the version when making changes
2. **Set Clear Goals**: Write specific, measurable goals for each prompt
3. **Track Performance**: Log executions with meaningful metrics
4. **Compare Versions**: Use the comparison tools to identify improvements
5. **Monitor Trends**: Watch for performance degradation over time
6. **Export Data**: Regularly export data for external analysis

## Troubleshooting

### No Prompts Found
If you see "No prompts found in registry", run the example script to initialize default prompts:
```bash
python examples/prompt_tracking_example.py
```

### Import Errors
Make sure you're running scripts from the project root directory, or add the project root to your Python path.

### Performance Data Missing
Performance data is only available after logging executions. Use the example script or integrate the tracking into your application.

## Future Enhancements

- Web dashboard for visualizing performance metrics
- A/B testing framework for prompt variants
- Automatic prompt optimization suggestions
- Integration with external monitoring tools
- Real-time performance alerts
