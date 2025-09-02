#!/usr/bin/env python3
"""
Flask web app for mini_todo - Beautiful Todoist-like UI
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from pathlib import Path
import sys
from datetime import datetime
import os

# Import the existing mini_todo logic
from mini_todo import (
    read_lines, write_lines, parse_tasks, 
    cmd_add as mini_todo_add,
    cmd_done as mini_todo_done,
    cmd_start as mini_todo_start,
    cmd_stop as mini_todo_stop,
    ensure_file
)

app = Flask(__name__)

# Ensure todo.txt exists
ensure_file()

@app.route('/')
def index():
    """Serve the main UI"""
    return render_template('index.html')

@app.route('/api/tasks')
def get_tasks():
    """Get all tasks in a format suitable for the UI"""
    lines = read_lines()
    open_tasks, in_progress_tasks, done_tasks = parse_tasks(lines)
    
    # Convert to UI format with continuous numbering
    task_num = 1
    ui_tasks = {
        'in_progress': [],
        'open': [],
        'done': []
    }
    
    # In progress tasks first (these show up in "Today")
    for file_idx, title in in_progress_tasks:
        ui_tasks['in_progress'].append({
            'id': task_num,
            'file_idx': file_idx,
            'title': title,
            'status': 'in_progress'
        })
        task_num += 1
    
    # Open tasks next
    for file_idx, title in open_tasks:
        ui_tasks['open'].append({
            'id': task_num,
            'file_idx': file_idx,
            'title': title,
            'status': 'open'
        })
        task_num += 1
    
    # Done tasks (no numbering needed)
    for file_idx, title in done_tasks:
        ui_tasks['done'].append({
            'file_idx': file_idx,
            'title': title,
            'status': 'done'
        })
    
    # Calculate counts for sidebar
    today_count = len(in_progress_tasks) + len(open_tasks)
    inbox_count = today_count  # Inbox only shows active tasks
    
    return jsonify({
        'tasks': ui_tasks,
        'counts': {
            'inbox': inbox_count,
            'today': today_count,
            'upcoming': 0,  # No due dates yet
            'completed': len(done_tasks)
        },
        'today_date': datetime.now().strftime('%b %d - Today - %A')
    })

@app.route('/api/tasks/add', methods=['POST'])
def add_task():
    """Add a new task"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        
        if not title:
            return jsonify({'error': 'Task title is required'}), 400
        
        # Use existing mini_todo logic
        lines = read_lines()
        lines.append(title)
        write_lines(lines)
        
        return jsonify({'success': True, 'message': f'Added: {title}'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/done', methods=['POST'])
def mark_done(task_id):
    """Mark a task as done"""
    try:
        mini_todo_done(task_id)
        return jsonify({'success': True})
    except SystemExit:
        return jsonify({'error': 'Invalid task ID'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """Start a task (mark as in progress)"""
    try:
        # We need to calculate which task in the open list this corresponds to
        lines = read_lines()
        open_tasks, in_progress_tasks, _ = parse_tasks(lines)
        
        # The task_id for start is based on open tasks only
        open_task_num = task_id - len(in_progress_tasks)
        if open_task_num < 1 or open_task_num > len(open_tasks):
            return jsonify({'error': 'Invalid task ID for starting'}), 400
        
        mini_todo_start(open_task_num)
        return jsonify({'success': True})
    except SystemExit:
        return jsonify({'error': 'Invalid task ID'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """Stop a task (remove in progress status)"""
    try:
        # For stop, we need to find which in_progress task this is
        lines = read_lines()
        _, in_progress_tasks, _ = parse_tasks(lines)
        
        if task_id < 1 or task_id > len(in_progress_tasks):
            return jsonify({'error': 'Invalid task ID for stopping'}), 400
        
        mini_todo_stop(task_id)
        return jsonify({'success': True})
    except SystemExit:
        return jsonify({'error': 'Invalid task ID'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
