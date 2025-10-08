#!/usr/bin/env python3
"""
Giskard API - Backend API for Tauri desktop app

CORS Configuration:
- Dynamically allows any localhost port (127.0.0.1:* and localhost:*)
- Supports Tauri protocol (tauri://localhost)
- Maintains security by restricting to localhost only
- Includes comprehensive logging for debugging CORS issues
"""

from flask import Flask, request
from flask_cors import CORS
from api.routes import api
from server.routes.agent import agent
from database import init_database
from utils.classification_manager import ClassificationManager
import subprocess
import time
import requests
import logging
import os
import re

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

# Custom CORS handler for dynamic localhost ports
def is_localhost_origin(origin):
    """Check if origin is from localhost (any port) or Tauri protocol"""
    if not origin:
        logger.debug("CORS: No origin header provided")
        return False
    
    # Allow Tauri protocol
    if origin.startswith("tauri://"):
        logger.debug(f"CORS: Allowing Tauri origin: {origin}")
        return True
    
    # Allow localhost with any port
    localhost_patterns = [
        r'^http://127\.0\.0\.1:\d+$',
        r'^http://localhost:\d+$',
        r'^https://127\.0\.0\.1:\d+$',
        r'^https://localhost:\d+$'
    ]
    
    for pattern in localhost_patterns:
        if re.match(pattern, origin):
            logger.debug(f"CORS: Allowing localhost origin: {origin}")
            return True
    
    logger.warning(f"CORS: Rejecting origin: {origin}")
    return False

# Enable CORS with custom origin validation
# Use a list of common localhost patterns
CORS(app, origins=[
    r"http://127\.0\.0\.1:\d+",
    r"http://localhost:\d+", 
    r"https://127\.0\.0\.1:\d+",
    r"https://localhost:\d+",
    "tauri://localhost"
], supports_credentials=True)

# Add CORS headers for all responses
@app.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    origin = request.headers.get('Origin')
    if origin and is_localhost_origin(origin):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    return response

# Register API blueprints
app.register_blueprint(api)  # Clean API
app.register_blueprint(agent, url_prefix='/api/agent')  # Agent orchestrator

# Initialize database
init_database()

# Start Ollama service if available
_ensure_ollama_running()

# Initialize classification manager
classification_manager = ClassificationManager()
classification_manager.start_background_processing()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
