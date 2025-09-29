# Giskard Environment Setup

This document explains how to properly set up and manage the Python environment for the Giskard project.

## Why Use Project-Specific Environments?

**Problems with using system Python:**
- Version conflicts between different projects
- Permission issues when installing packages globally
- Risk of breaking system tools that depend on Python
- Difficulty managing different package versions for different projects

**Benefits of project-specific environments:**
- Isolated dependencies per project
- Easy to reproduce the exact environment
- No conflicts between projects
- Clean, reproducible deployments

## Current Setup

### Environment Details
- **Environment Name**: `giskard`
- **Python Version**: 3.11.13
- **Package Manager**: conda + pip
- **Location**: `/Users/charlesdupont/miniconda3/envs/giskard`

### Dependencies
- Flask==2.3.3
- flask-cors==4.0.0
- langgraph>=0.6.0
- langchain-core>=0.3.0
- langchain-community>=0.3.0
- langchain-ollama>=0.2.0

## Quick Start

### Option 1: Use the Startup Script (Recommended)
```bash
./start_giskard.sh
```

### Option 2: Manual Environment Activation
```bash
# Activate the environment
conda activate giskard

# Start the application
python app.py
```

## Environment Management Commands

### Create Environment from Scratch
```bash
# Create new environment
conda create -n giskard python=3.11 -y

# Activate environment
conda activate giskard

# Install dependencies
pip install -r requirements.txt
```

### Create Environment from environment.yml
```bash
conda env create -f environment.yml
conda activate giskard
```

### Update Dependencies
```bash
conda activate giskard
pip install -r requirements.txt --upgrade
```

### Export Current Environment
```bash
conda activate giskard
conda env export > environment.yml
```

## Troubleshooting

### Environment Not Found
```bash
# List all environments
conda env list

# If giskard environment doesn't exist, create it
conda create -n giskard python=3.11 -y
```

### Wrong Python Version
```bash
# Check current Python
python --version
which python

# Should show:
# Python 3.11.13
# /Users/charlesdupont/miniconda3/envs/giskard/bin/python
```

### Missing Dependencies
```bash
conda activate giskard
pip install -r requirements.txt
```

### Environment Conflicts
```bash
# Remove and recreate environment
conda env remove -n giskard
conda create -n giskard python=3.11 -y
conda activate giskard
pip install -r requirements.txt
```

## Best Practices

1. **Always activate the environment** before working on the project
2. **Use the startup script** for consistency
3. **Keep requirements.txt updated** when adding new dependencies
4. **Export environment.yml** periodically for backup
5. **Don't install packages globally** - always use the project environment

## IDE Integration

### VS Code
1. Open Command Palette (Cmd+Shift+P)
2. Type "Python: Select Interpreter"
3. Choose: `/Users/charlesdupont/miniconda3/envs/giskard/bin/python`

### PyCharm
1. Go to Settings > Project > Python Interpreter
2. Add New Interpreter > Conda Environment
3. Select Existing Environment: `/Users/charlesdupont/miniconda3/envs/giskard`
