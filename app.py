#!/usr/bin/env python3
"""
Mini Todo - Beautiful Todoist-like web app
"""

from flask import Flask, render_template, request, jsonify
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

# Configuration
TODO_PATH = Path("todo.txt")

def ensure_file():
    """Ensure todo.txt exists"""
    if not TODO_PATH.exists():
        TODO_PATH.write_text("", encoding="utf-8")

def read_lines():
    """Read all lines from todo.txt"""
    ensure_file()
    content = TODO_PATH.read_text(encoding="utf-8").strip()
    if not content:
        return []
    return content.splitlines()

def write_lines(lines):
    """Write lines to todo.txt"""
    if lines:
        TODO_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    else:
        TODO_PATH.write_text("", encoding="utf-8")

def parse_tasks(lines):
    """Parse tasks into categories: (open, in_progress, done)"""
    open_tasks = []
    in_progress_tasks = []
    done_tasks = []
    
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        if line.startswith("x "):
            # Completed task: "x 2024-01-15 Task title" or "x Task title"
            parts = line[2:].strip().split(" ", 1)
            if len(parts) >= 2 and parts[0].count('-') == 2:
                # Has date format YYYY-MM-DD
                title = parts[1]
            else:
                # No date, everything after "x " is the title
                title = line[2:].strip()
            done_tasks.append((idx, title))
            
        elif "status:in_progress" in line:
            # In progress task: "Task title status:in_progress"
            title = line.replace("status:in_progress", "").strip()
            in_progress_tasks.append((idx, title))
            
        else:
            # Open task: just the plain text
            open_tasks.append((idx, line))
    
    return open_tasks, in_progress_tasks, done_tasks

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
        lines = read_lines()
        open_tasks, in_progress_tasks, _ = parse_tasks(lines)
        
        # Match the display order: in_progress first, then open
        all_active_tasks = in_progress_tasks + open_tasks
        if task_id < 1 or task_id > len(all_active_tasks):
            return jsonify({'error': 'Invalid task ID'}), 400
        
        file_idx, title = all_active_tasks[task_id-1]
        completion_date = datetime.now().strftime("%Y-%m-%d")
        lines[file_idx] = f"x {completion_date} {title}"
        write_lines(lines)
        
        return jsonify({'success': True, 'message': f'Done: {title}'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """Start a task (mark as in progress)"""
    try:
        lines = read_lines()
        open_tasks, in_progress_tasks, _ = parse_tasks(lines)
        
        # The task_id for start is based on open tasks only
        open_task_num = task_id - len(in_progress_tasks)
        if open_task_num < 1 or open_task_num > len(open_tasks):
            return jsonify({'error': 'Invalid task ID for starting'}), 400
        
        file_idx, title = open_tasks[open_task_num-1]
        lines[file_idx] = f"{title} status:in_progress"
        write_lines(lines)
        
        return jsonify({'success': True, 'message': f'Started: {title}'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """Stop a task (remove in progress status)"""
    try:
        lines = read_lines()
        _, in_progress_tasks, _ = parse_tasks(lines)
        
        if task_id < 1 or task_id > len(in_progress_tasks):
            return jsonify({'error': 'Invalid task ID for stopping'}), 400
        
        file_idx, title = in_progress_tasks[task_id-1]
        lines[file_idx] = title
        write_lines(lines)
        
        return jsonify({'success': True, 'message': f'Stopped: {title}'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/uncomplete', methods=['POST'])
def uncomplete_task():
    """Uncomplete a completed task (make it open again)"""
    try:
        data = request.get_json()
        file_idx = data.get('file_idx')
        
        if file_idx is None:
            return jsonify({'error': 'file_idx is required'}), 400
        
        lines = read_lines()
        if file_idx < 0 or file_idx >= len(lines):
            return jsonify({'error': 'Invalid file index'}), 400
        
        # Get the completed task line
        line = lines[file_idx].strip()
        if not line.startswith("x "):
            return jsonify({'error': 'Task is not completed'}), 400
        
        # Extract the task title (remove "x 2025-09-02 " prefix)
        parts = line[2:].strip().split(" ", 1)
        if len(parts) >= 2 and parts[0].count('-') == 2:
            # Has date format YYYY-MM-DD
            title = parts[1]
        else:
            # No date, everything after "x " is the title
            title = line[2:].strip()
        
        # Make it an open task again
        lines[file_idx] = title
        write_lines(lines)
        
        return jsonify({'success': True, 'message': f'Uncompleted: {title}'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    ensure_file()  # Initialize todo.txt on startup
    app.run(debug=True, port=5001)
