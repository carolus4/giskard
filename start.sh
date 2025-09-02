#!/bin/bash
# Start the Mini Todo Web App

echo "Starting Mini Todo Web App..."
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting Flask server..."
echo "🚀 Your beautiful todo app will be available at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
