# Simple Prompt Management System

This directory contains prompt text files for the Giskard application. Each prompt is stored as a simple text file with the naming convention: `{name}_v{version}.txt`

**Key Philosophy**: Only the prompt text is versioned and editable. Configuration (model, temperature, etc.) is handled in code where it belongs.

## File Structure

```
prompts/
├── README.md                           # This file
├── coaching_system_v1.0.txt           # Coaching system prompt text
├── task_classification_v3.0.txt       # Task classification prompt text
└── ...                                # Additional prompt text files
```

## File Format

Each prompt is a simple text file with natural formatting:

```
You are Giscard, a productivity coach and personal assistant.

Your personality:
- Supportive and encouraging
- Direct and practical

Guidelines:
- Keep responses concise
- Offer specific advice

Current task context:
{task_context}
```

**Configuration is in code** - Model settings, temperature, token limits, etc. are defined in `config/simple_prompt_registry.py` where they belong as application logic.

## Managing Prompts

### Using the Command Line Tools

1. **List all prompts:**
   ```bash
   python scripts/simple_prompt_manager.py list
   ```

2. **View a specific prompt:**
   ```bash
   python scripts/simple_prompt_manager.py show coaching_system
   python scripts/simple_prompt_manager.py show coaching_system 1.0
   ```

3. **Create a new prompt:**
   ```bash
   python scripts/simple_prompt_manager.py create
   ```

4. **Edit an existing prompt:**
   ```bash
   python scripts/simple_prompt_manager.py edit coaching_system 1.0
   ```

5. **Open prompt in editor:**
   ```bash
   python scripts/simple_prompt_manager.py edit-file coaching_system 1.0
   ```

6. **Delete a prompt version:**
   ```bash
   python scripts/simple_prompt_manager.py delete coaching_system 1.0
   ```

### Manual Editing

You can edit prompt files directly using any text editor:

```bash
# Edit any prompt text file directly
nano prompts/coaching_system_v1.0.txt
# or
code prompts/coaching_system_v1.0.txt
```

**Important:** When editing manually:
- Edit the `.txt` files directly - they support natural formatting with newlines
- No JSON to worry about - just plain text
- Consider creating a new version instead of modifying existing ones
- Configuration changes go in `config/simple_prompt_registry.py`

## Version Management

- Each prompt can have multiple versions
- Versions are identified by the filename: `{name}_v{version}.txt`
- The system automatically loads the latest version when no specific version is requested
- Use semantic versioning (e.g., 1.0, 1.1, 2.0) for better organization

## Benefits of Simple Text-Only Prompts

1. **Super Easy Editing:** Just edit text files with any editor
2. **Natural Formatting:** Newlines, indentation, and structure preserved
3. **No JSON Complexity:** No escaping, no nested structures
4. **Version Control Friendly:** Clean diffs in Git
5. **Collaboration:** Multiple people can work on different prompts
6. **Configuration in Code:** Model settings where they belong
7. **Triple-Quote Style:** Edit prompts like Python docstrings

## Integration

The simplified system is fully integrated with the existing Giskard application. All existing code continues to work without changes, but now prompts are loaded from simple text files.
