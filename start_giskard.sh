#!/bin/bash

# Giskard Startup Script
# Works for both daily use and development

# Set default mode to "dev" if not specified externally
MODE="${MODE:-dev}"

# Ensure cargo binaries are in PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Define the Tauri desktop project directory
TAURI_DIR="/Users/charlesdupont/Dev/giskard/giskard-desktop"

# Helper function to start Tauri in development mode
start_tauri_dev() {
    echo "   Starting Tauri in development mode..."
    cd "$TAURI_DIR"
    cargo tauri dev &
    DESKTOP_PID=$!
    echo "✅ Tauri dev server started (PID: $DESKTOP_PID)"
    cd - >/dev/null
}

# Helper function to start Tauri bundle
start_tauri_bundle() {
    local APP_BUNDLE="$TAURI_DIR/src-tauri/target/release/bundle/macos/Giskard Desktop.app"

    if [ -d "$APP_BUNDLE" ]; then
        echo "   Launching Tauri app bundle..."
        open -n "$APP_BUNDLE" &
        DESKTOP_PID=$!
        echo "✅ App bundle launched (PID: $DESKTOP_PID)"
    else
        echo "   App bundle not found, building first..."
        cd "$TAURI_DIR"
        cargo tauri build

        if [ -d "$APP_BUNDLE" ]; then
            echo "   Build completed, launching bundle..."
            open -n "$APP_BUNDLE" &
            DESKTOP_PID=$!
            echo "✅ App bundle launched (PID: $DESKTOP_PID)"
        else
            echo "❌ Failed to build app bundle"
            exit 1
        fi
        cd - >/dev/null
    fi
}

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

    # Clean up any remaining Ollama processes on port 11434
    if lsof -ti:11434 >/dev/null 2>&1; then
        echo "   Cleaning up remaining Ollama processes..."
        lsof -ti:11434 | xargs kill -9 >/dev/null 2>&1 || true
    fi

    # Clean up temporary log files
    rm -f /tmp/ollama.log /tmp/ollama_startup.log

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

# Function to check if Ollama is responding
check_ollama() {
    # Try multiple times with timeout to avoid hanging
    for i in {1..3}; do
        if curl -s --max-time 3 http://localhost:11434/api/tags >/dev/null 2>&1; then
            return 0
        fi
        sleep 1
    done
    return 1
}

# Check if port 11434 is in use and kill any existing Ollama processes
if lsof -ti:11434 >/dev/null 2>&1; then
    echo "   Found existing process on port 11434, cleaning up..."
    lsof -ti:11434 | xargs kill -9 >/dev/null 2>&1 || true
    sleep 2
fi

if check_ollama; then
    echo "✅ Ollama is already running and responding"
else
    echo "🚀 Starting Ollama service..."
    if command -v ollama >/dev/null 2>&1; then
        # Set GPU acceleration environment variable
        export OLLAMA_GPU_LAYERS=999

        # Start Ollama in background with logging
        ollama serve >/tmp/ollama_startup.log 2>&1 &
        OLLAMA_PID=$!

        # Wait for Ollama to start (up to 15 seconds with better feedback)
        echo "   Waiting for Ollama to start..."
        for i in {1..15}; do
            sleep 1
            if check_ollama; then
                echo "✅ Ollama started successfully"
                break
            fi
            if [ $i -eq 5 ]; then
                echo "   Still waiting... (this can take a moment on first run)"
            fi
            if [ $i -eq 15 ]; then
                echo "❌ Ollama failed to start within 15 seconds"
                echo "   Check /tmp/ollama_startup.log for details"
                echo "   You may need to pull a model first: ollama pull gemma3:4b"
            fi
        done
    else
        echo "❌ Ollama not found in PATH - please install Ollama first"
        echo "   Visit: https://ollama.ai/download"
        echo "   Or install via Homebrew: brew install ollama"
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
echo "🖥️  Starting Giskard desktop application (MODE=$MODE)..."

case "$MODE" in
  dev)
    start_tauri_dev
    ;;
  bundle)
    start_tauri_bundle
    ;;
  *)
    echo "❌ Unknown MODE=$MODE (use dev or bundle)"
    exit 1
    ;;
esac

echo ""
echo "🎉 Giskard is now running!"
echo "   - API Backend: http://127.0.0.1:5001"
echo "   - Desktop App: Running in background"
echo "   - Ollama Service: Running with GPU acceleration"
echo ""
echo "Press Ctrl+C to stop all applications"

# Wait for user to stop
wait