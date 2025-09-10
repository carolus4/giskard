#!/usr/bin/env python3
"""
Giskard API - Backend API for Tauri desktop app
"""

from flask import Flask
from flask_cors import CORS
from api.routes import api, classification_manager
from utils.file_manager import TodoFileManager

# Create Flask app
app = Flask(__name__)

# Enable CORS for Tauri desktop app (any localhost port)
CORS(app, origins=[
    "http://127.0.0.1:1430", "http://localhost:1430",  # Original port
    "http://127.0.0.1:1431", "http://localhost:1431",  # New port  
    "http://127.0.0.1:1432", "http://localhost:1432",  # Future ports
    "tauri://localhost"
], supports_credentials=True)

# Register API blueprint
app.register_blueprint(api)

# Initialize file manager to ensure todo.txt exists
file_manager = TodoFileManager()

# Start classification processing on startup
classification_manager.start_background_processing()

if __name__ == '__main__':
    # File manager already initialized above
    app.run(debug=True, port=5001)
