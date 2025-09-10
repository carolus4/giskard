# Auto-Categorization Feature

## Overview

The auto-categorization feature automatically assigns 0..n labels from `{health, career, learning}` to each task using an on-device LLM (llama3.1:8b). This is a 100% AI-driven system with high precision - if the LLM is unsure, it assigns no categories.

## Features

- **On-device LLM**: Uses Ollama with llama3.1:8b model
- **Automatic classification**: Tasks are classified on startup and when created/updated
- **High precision**: Conservative approach - only assigns categories when confident
- **Background processing**: Classification happens asynchronously in the background
- **Comprehensive logging**: All predictions are logged to `classification_predictions_log.txt`
- **Visual indicators**: Categories are displayed as colored badges in the UI

## Categories

- **health**: Physical health, fitness, medical, wellness, self-care
- **career**: Work, professional development, job-related, business  
- **learning**: Education, skill development, studying, knowledge acquisition

## Setup

### Prerequisites

1. **Ollama installed and running**
   ```bash
   # Install Ollama (if not already installed)
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull the required model
   ollama pull llama3.1:8b
   
   # Start Ollama server
   ollama serve
   ```

2. **Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Configuration

The system is configured to use:
- **Model**: `llama3.1:8b`
- **Ollama URL**: `http://localhost:11434/api/generate`
- **Log file**: `classification_predictions_log.txt`

## Usage

### Automatic Classification

The system automatically classifies tasks in these scenarios:

1. **On startup**: All uncategorized tasks are classified
2. **On task creation**: New tasks are queued for classification
3. **On task update**: Modified tasks are re-classified

### Manual Testing

Run the test script to verify the implementation:

```bash
python test_classification.py
```

### API Endpoints

- `POST /api/classification/startup` - Trigger classification of all uncategorized tasks
- `GET /api/classification/status` - Get classification queue status
- `POST /api/classification/start` - Start background classification processing

## Implementation Details

### Task Model Updates

The `Task` model now includes:
- `categories` field: List of category strings
- Updated parsing for `categories:"health,career"` format in todo.txt
- Categories are stored inline within the task

### Classification Service

`utils/classification_service.py`:
- Handles LLM communication with Ollama
- Implements strict JSON prompt for consistent responses
- Includes error handling and logging
- Validates categories against allowed set

### Classification Manager

`utils/classification_manager.py`:
- Manages classification queue
- Handles background processing
- Coordinates with file manager for persistence
- Provides startup classification functionality

### Frontend Updates

- Task template updated to display category badges
- CSS styles for category badges with distinct colors
- Real-time updates when categories change

## File Format

Tasks with categories are stored in todo.txt as:

```
project:"Work" Complete Python course categories:"career,learning" note:"Finish by end of month"
```

## Logging

All classification attempts are logged to `classification_predictions_log.txt` in JSON format:

```json
{
  "timestamp": "2024-01-15 10:30:45",
  "task": "Go to the gym - Work out for 30 minutes",
  "categories": ["health"],
  "raw_response": "[\"health\"]"
}
```

## Error Handling

- **Ollama unavailable**: System gracefully handles missing Ollama service
- **Invalid responses**: Malformed LLM responses are logged and ignored
- **Network timeouts**: 30-second timeout with retry logic
- **JSON parsing errors**: Fallback to empty categories list

## Performance

- **Background processing**: Classification doesn't block UI
- **Batch processing**: Up to 10 tasks processed per batch
- **Low temperature**: 0.1 temperature for consistent results
- **Conservative approach**: High precision over recall

## Troubleshooting

### Ollama Not Available
```
ERROR: Failed to connect to Ollama: Connection refused
```
**Solution**: Start Ollama server with `ollama serve`

### Model Not Found
```
ERROR: Model llama3.1:8b not found
```
**Solution**: Pull the model with `ollama pull llama3.1:8b`

### Classification Not Working
1. Check Ollama is running: `curl http://localhost:11434/api/tags`
2. Verify model is available: `ollama list`
3. Check logs in `classification_predictions_log.txt`

## Future Enhancements

- Custom category definitions
- User feedback on classification accuracy
- Confidence scores for categories
- Category-based task filtering
- Learning from user corrections
