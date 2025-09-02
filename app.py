#!/usr/bin/env python3
"""
Mini Todo - Beautiful Todoist-like web app
"""

from flask import Flask, render_template
from api.routes import api
from utils.file_manager import TodoFileManager

# Create Flask app
app = Flask(__name__)

# Register API blueprint
app.register_blueprint(api)

# Initialize file manager to ensure todo.txt exists
file_manager = TodoFileManager()

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')

if __name__ == '__main__':
    # File manager already initialized above
    app.run(debug=True, port=5001)
