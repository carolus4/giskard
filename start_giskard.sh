#!/bin/bash

# Giskard Startup Script
# Works for both daily use and development

# Cleanup function to stop all applications
cleanup() {
    echo ""
    echo "🛑 Stopping Giskard..."
    if [ ! -z "$DESKTOP_PID" ]; then
        echo "   Stopping Desktop app (PID: $DESKTOP_PID)"
        kill $DESKTOP_PID 2>/dev/null || true
    fi
    if [ ! -z "$FLASK_PID" ]; then
        echo "   Stopping Flask backend (PID: $FLASK_PID)"
        kill $FLASK_PID 2>/dev/null || true
    fi
    if [ ! -z "$OLLAMA_PID" ]; then
        echo "   Stopping Ollama service (PID: $OLLAMA_PID)"
        kill $OLLAMA_PID 2>/dev/null || true
    fi
    echo "✅ Giskard stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

echo "🚀 Starting Giskard..."

# Use the direct path to the conda environment's Python
PYTHON_PATH="/Users/charlesdupont/miniconda3/envs/giskard/bin/python"

# Check if the Python executable exists
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Python not found at $PYTHON_PATH"
    echo "Please create the giskard conda environment first:"
    echo "conda create -n giskard python=3.11 -y"
    echo "conda activate giskard"
    echo "pip install -r requirements.txt"
    exit 1
fi

# Check if required packages are installed
echo "🔍 Checking dependencies..."
$PYTHON_PATH -c "import langgraph, langchain_core, langchain_community, langchain_ollama; print('✅ All dependencies are available')" || {
    echo "❌ Missing dependencies. Installing..."
    /Users/charlesdupont/miniconda3/envs/giskard/bin/pip install -r requirements.txt
}

# Check if Ollama is running
echo "🤖 Checking Ollama service..."
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✅ Ollama is already running"
else
    echo "🚀 Starting Ollama service..."
    if command -v ollama >/dev/null 2>&1; then
        # Set GPU acceleration environment variable
        export OLLAMA_GPU_LAYERS=999
        
        # Start Ollama in background
        ollama serve >/dev/null 2>&1 &
        OLLAMA_PID=$!
        
        # Wait for Ollama to start (up to 10 seconds)
        echo "   Waiting for Ollama to start..."
        for i in {1..20}; do
            sleep 0.5
            if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
                echo "✅ Ollama started successfully"
                break
            fi
            if [ $i -eq 20 ]; then
                echo "⚠️  Ollama failed to start within 10 seconds"
            fi
        done
    else
        echo "⚠️  Ollama not found in PATH - please install Ollama first"
        echo "   Visit: https://ollama.ai/download"
    fi
fi

# Check if database directory exists
echo "🗄️  Checking database..."
if [ ! -d "data" ]; then
    echo "   Creating data directory..."
    mkdir -p data
fi

# Check if port 5001 is already in use
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 5001 is already in use. Stopping existing processes..."
    
    # Get PIDs of processes using port 5001
    PIDS=$(lsof -Pi :5001 -sTCP:LISTEN -t)
    if [ ! -z "$PIDS" ]; then
        echo "   Killing processes: $PIDS"
        echo $PIDS | xargs kill -9 2>/dev/null || true
    fi
    
    # Also try to kill any Python processes that might be running the app
    pkill -f "python.*app.py" || true
    pkill -f "flask" || true
    
    # Wait for processes to actually stop
    sleep 3
    
    # Double-check that port is free
    if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null ; then
        echo "❌ Port 5001 is still in use after cleanup attempts"
        echo "Please manually stop the processes using port 5001:"
        lsof -Pi :5001 -sTCP:LISTEN
        exit 1
    fi
fi

# Start the Flask application
echo "🌐 Starting Flask API backend on http://127.0.0.1:5001"
$PYTHON_PATH app.py &
FLASK_PID=$!

# Wait a moment for Flask to start
sleep 3

# Check if Flask started successfully
if ! kill -0 $FLASK_PID 2>/dev/null; then
    echo "❌ Failed to start Flask backend"
    exit 1
fi

echo "✅ Flask backend started successfully (PID: $FLASK_PID)"

# Start the Tauri desktop application
echo "🖥️  Starting Giskard desktop application..."
TAURI_APP="/Users/charlesdupont/Dev/giskard/giskard-desktop/src-tauri/target/release/giskard-desktop"

if [ -f "$TAURI_APP" ]; then
    echo "🚀 Launching desktop app..."
    "$TAURI_APP" &
    DESKTOP_PID=$!
    echo "✅ Desktop app started (PID: $DESKTOP_PID)"
    echo ""
    echo "🎉 Giskard is now running!"
    echo "   - API Backend: http://127.0.0.1:5001"
    echo "   - Desktop App: Running in background"
    echo "   - Ollama Service: Running with GPU acceleration"
    echo ""
    echo "Press Ctrl+C to stop all applications"
    
    # Wait for user to stop
    wait
else
    echo "❌ Desktop app not found at $TAURI_APP"
    echo "Please build the desktop app first:"
    echo "cd giskard-desktop && ./build-dmg.sh"
    echo ""
    echo "Flask backend is still running on http://127.0.0.1:5001"
    wait $FLASK_PID
fi