# New Prompt Management System Implementation

## Overview

We've successfully implemented a new prompt management system that follows the approach you suggested:

```python
try:
    prompt = langfuse.get_prompt("router", label="production")
except Exception:
    prompt = load_local_prompt("langfuse-prompts/router.txt")

compiled = prompt.compile(
    current_datetime=datetime.now().isoformat(),
    tool_descriptions=describe_tools(),
)
response = llm.invoke(compiled.text)
```

## Implementation Details

### 1. New Prompt Manager (`config/prompt_manager.py`)

- **Langfuse Integration**: Tries to load prompts from Langfuse first
- **Local Fallback**: Falls back to local files in `langfuse-prompts/` directory
- **Template Compilation**: Handles Langfuse template syntax `{{variable}}`
- **Error Handling**: Graceful fallback when Langfuse is unavailable

### 2. Updated Router (`orchestrator/tools/router.py`)

- **New Constructor Parameters**: 
  - `prompt_name`: Name of the prompt (default: "router")
  - `prompt_label`: Langfuse label (default: "staging")
- **Template Handling**: Uses compiled prompts directly to avoid ChatPromptTemplate issues
- **Backward Compatibility**: Maintains existing functionality

### 3. Prompt Template Format

The `langfuse-prompts/router.txt` file uses Langfuse template syntax:

```
Current datetime: {{current_datetime}}
Available tools: {{tool_descriptions}}
```

## Key Features

### ✅ Langfuse First, Local Fallback
- Attempts to load from Langfuse with specified label
- Falls back to local file if Langfuse fails or is unavailable
- Logs the source of each prompt for debugging

### ✅ Proper Template Compilation
- Handles Langfuse `{{variable}}` syntax correctly
- Preserves JSON braces in prompt examples
- Supports custom template variables

### ✅ Seamless Integration
- Router automatically uses new prompt management
- No breaking changes to existing code
- Maintains all existing functionality

## Usage Examples

### Basic Usage
```python
from config.prompt_manager import get_compiled_prompt

# Get compiled prompt (tries Langfuse first, falls back to local)
compiled = get_compiled_prompt(
    "router", 
    label="staging",
    tool_descriptions="Your tool descriptions here"
)
```

### Router Integration
```python
from orchestrator.tools.router import Router

# Router automatically uses new prompt management
router = Router(
    prompt_name="router",
    prompt_label="staging"
)

# Use as before
result = router.plan_actions("Hello, can you help me?")
```

### Direct Prompt Loading
```python
from config.prompt_manager import get_prompt, load_local_prompt

# Get prompt data (with source information)
prompt_data = get_prompt("router", label="staging")
print(f"Source: {prompt_data['source']}")  # "langfuse" or "local"

# Load local prompt directly
local_prompt = load_local_prompt("router")
```

## Agent Integration

The new prompt management system is fully integrated with the agent's conversation flow:

### Planner Integration
```python
# In server/routes/agent.py - Step 1: Planner LLM
from config.prompt_manager import get_prompt, get_compiled_prompt

# Get the prompt (tries Langfuse first, falls back to local)
prompt_data = get_prompt("planner", label="staging")
prompt = prompt_data  # Store for Langfuse tracing

# Compile the prompt with template variables
compiled_prompt = get_compiled_prompt("planner", label="staging")

# Use in Langfuse generation with prompt reference
planner_generation = planner_span.start_observation(
    name="planner.llm",
    as_type="generation",
    input={"messages": [...]},
    prompt=prompt if prompt_data.get("source") == "langfuse" else None
)
```

### Synthesizer Integration
```python
# In server/routes/agent.py - Step 3: Synthesize final response
synthesizer_prompt_data = get_prompt("synthesizer", label="staging")
synthesizer_prompt = synthesizer_prompt_data

# Compile with template variables
full_prompt = get_compiled_prompt(
    "synthesizer", 
    label="staging",
    user_input=input_text,
    action_results=action_results_str
)

# Use in Langfuse generation with prompt reference
synthesizer_generation = synthesizer_span.start_observation(
    name="synthesizer.llm",
    as_type="generation",
    input={"messages": [...]},
    prompt=synthesizer_prompt if synthesizer_prompt_data.get("source") == "langfuse" else None
)
```

## File Structure

```
langfuse-prompts/
├── router.txt          # Router prompt with {{variable}} syntax
├── planner.txt         # Planner prompt with {{variable}} syntax
└── synthesizer.txt     # Synthesizer prompt with {{variable}} syntax

config/
├── prompt_manager.py   # New prompt management system
└── langfuse_config.py  # Existing Langfuse configuration

orchestrator/tools/
└── router.py           # Updated to use new prompt management

server/routes/
└── agent.py            # Updated planner and synthesizer to use new system
```

## Benefits

1. **Flexibility**: Can use Langfuse for production, local files for development
2. **Reliability**: Automatic fallback ensures system always works
3. **Observability**: Clear logging of prompt sources and compilation
4. **Maintainability**: Centralized prompt management
5. **Compatibility**: Works with existing Langfuse infrastructure

## Testing

The system has been tested and verified to work correctly:
- ✅ Langfuse integration (when available)
- ✅ Local fallback (when Langfuse unavailable)
- ✅ Template compilation with `{{variable}}` syntax
- ✅ Router integration and functionality
- ✅ Error handling and graceful degradation

## Next Steps

1. **Deploy to Production**: The system is ready for production use
2. **Add More Prompts**: Add other prompts to `langfuse-prompts/` directory
3. **Langfuse Setup**: Configure Langfuse prompts with proper labels
4. **Monitoring**: Monitor prompt usage and performance through Langfuse dashboard
