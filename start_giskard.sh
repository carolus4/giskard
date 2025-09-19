#!/bin/bash

# 🚀 Giskard Startup Script
# This script starts all components of the Giskard productivity system

echo "🚀 Starting Giskard - AI-Powered Productivity Coach"
echo "=================================================="

# Set GPU acceleration for Ollama
export OLLAMA_GPU_LAYERS=999
echo "🔧 Configured Ollama for GPU acceleration (OLLAMA_GPU_LAYERS=999)"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install it from https://ollama.ai"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed."
    exit 1
fi

echo "✅ All prerequisites found"

# Function to check if a model is currently running
check_model_running() {
    local model_name="$1"
    if ollama ps | grep -q "$model_name"; then
        return 0  # Model is running
    else
        return 1  # Model is not running
    fi
}

# Function to check if a model is using GPU
check_model_gpu() {
    local model_name="$1"
    local ps_output=$(ollama ps)
    if echo "$ps_output" | grep -q "$model_name.*gpu"; then
        return 0  # Model is using GPU
    else
        return 1  # Model is not using GPU
    fi
}

# Function to start a model with GPU acceleration
start_model_gpu() {
    local model_name="$1"
    echo "🚀 Starting $model_name with GPU acceleration..."
    ollama run "$model_name" &
    sleep 2  # Give it a moment to start
}

# Start Ollama if not running
echo "🤖 Starting Ollama server..."
if ! pgrep -f "ollama serve" > /dev/null; then
    ollama serve > /dev/null 2>&1 &
    echo "⏳ Waiting for Ollama to start..."
    sleep 3
fi

# Check if llama3.1:8b model is available
echo "🧠 Checking for llama3.1:8b model..."
if ! ollama list | grep -q "llama3.1:8b"; then
    echo "📥 Pulling llama3.1:8b model (this may take a while)..."
    ollama pull llama3.1:8b
fi

# Check if the model is running and using GPU
TARGET_MODEL="llama3.1:8b"
echo "🔍 Checking if $TARGET_MODEL is running..."

if check_model_running "$TARGET_MODEL"; then
    echo "✅ $TARGET_MODEL is running"
    
    # Check if it's using GPU
    if check_model_gpu "$TARGET_MODEL"; then
        echo "🚀 $TARGET_MODEL is running on GPU - Excellent!"
    else
        echo "⚠️  $TARGET_MODEL is running but NOT using GPU - Performance may be slow"
        echo "🔄 Restarting model to ensure GPU usage..."
        # Kill the current model process
        pkill -f "ollama run $TARGET_MODEL" 2>/dev/null || true
        sleep 1
        start_model_gpu "$TARGET_MODEL"
    fi
else
    echo "🚀 Starting $TARGET_MODEL with GPU acceleration..."
    start_model_gpu "$TARGET_MODEL"
fi

echo "✅ Ollama ready with $TARGET_MODEL"

# Start Flask backend
echo "🌐 Starting Flask backend..."
python3 app.py &
FLASK_PID=$!

# Wait for Flask to start
sleep 2

# Test if Flask is responding
if curl -s http://localhost:5001/api/tasks > /dev/null; then
    echo "✅ Flask backend running on http://localhost:5001"
else
    echo "❌ Flask backend failed to start"
    kill $FLASK_PID 2>/dev/null
    exit 1
fi

# Start Tauri desktop app
echo "🖥️ Starting Giskard desktop app..."
cd giskard-desktop

if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

echo "🎉 Launching Giskard desktop app..."
npm run tauri dev

# Cleanup on exit
trap 'kill $FLASK_PID 2>/dev/null; echo "🛑 Stopping Giskard components..."; exit 0' INT TERM

wait
