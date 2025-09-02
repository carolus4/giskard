#!/bin/bash
# Start the Mini Todo Web App

echo "🎯 Starting Mini Todo Web App..."
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

echo "🚀 Launching at: http://localhost:5001"
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
