#!/bin/bash

# 🚀 Giskard Startup Script
# This script starts all components of the Giskard productivity system

echo "🚀 Starting Giskard - AI-Powered Productivity Coach"
echo "=================================================="

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

echo "✅ Ollama ready with llama3.1:8b"

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
