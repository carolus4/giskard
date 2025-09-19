#!/usr/bin/env python3
"""
Giskard API - Backend API for Tauri desktop app
"""

from flask import Flask
from flask_cors import CORS
from api.routes import api, classification_manager
from utils.file_manager import TodoFileManager
import subprocess
import time
import requests
import logging
import os

logger = logging.getLogger(__name__)

def _ensure_ollama_running():
    """Ensure Ollama service is running, start it if necessary"""
    try:
        # Check if Ollama is already running
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            logger.info("✅ Ollama is already running")
            return
    except:
        pass  # Ollama not running, continue to start it
    
    try:
        # Check if ollama command exists
        result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
        if result.returncode != 0:
            logger.warning("⚠️  Ollama not found in PATH, skipping auto-start")
            return
        
        logger.info("🚀 Starting Ollama service with GPU acceleration...")
        
        # Set GPU acceleration environment variable
        env = os.environ.copy()
        env['OLLAMA_GPU_LAYERS'] = '999'
        
        # Start Ollama in background with GPU configuration
        subprocess.Popen(['ollama', 'serve'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL,
                        env=env)
        
        # Wait for Ollama to start (up to 10 seconds)
        for i in range(20):  # 20 * 0.5s = 10s max
            time.sleep(0.5)
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=1)
                if response.status_code == 200:
                    logger.info("✅ Ollama started successfully")
                    return
            except:
                continue
        
        logger.warning("⚠️  Ollama failed to start within 10 seconds")
        
    except Exception as e:
        logger.warning(f"⚠️  Failed to start Ollama: {str(e)}")

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

# Initialize file manager to ensure data/todo.txt exists
file_manager = TodoFileManager()

# Start Ollama service if available
_ensure_ollama_running()

# Start classification processing on startup
classification_manager.start_background_processing()

if __name__ == '__main__':
    # File manager already initialized above
    app.run(debug=True, port=5001)
