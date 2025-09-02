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

def parse_task_text(text):
    """Parse task text to extract title, description, and order"""
    if " | " in text:
        parts = text.split(" | ")
        title = parts[0].strip()
        description = parts[1].replace("\\n", "\n").strip() if len(parts) > 1 else ""
        # Check if there's an order number (third part)
        order = None
        if len(parts) >= 3 and parts[2].strip().isdigit():
            order = int(parts[2].strip())
        return title, description, order
    return text.strip(), "", None

def format_task_text(title, description="", order=None):
    """Format task title, description, and order for storage"""
    result = title
    if description:
        # Escape newlines in description to keep todo.txt single-line per task
        escaped_description = description.replace("\n", "\\n")
        result += f" | {escaped_description}"
    elif order is not None:
        # If we have an order but no description, add empty description with space
        result += " | "
    
    if order is not None:
        result += f" | {order}"
    
    return result

def assign_missing_orders():
    """Auto-assign order numbers to tasks that don't have them"""
    lines = read_lines()
    next_order = 1
    modified = False
    
    for i, line in enumerate(lines):
        if not line.strip():
            continue
            
        # Parse the current task to see if it has an order
        if line.startswith('x '):
            # Completed task: "x 2023-12-01 Task text" or "x Task text"
            line_after_x = line[2:].strip()
            parts = line_after_x.split(" ", 1)
            if len(parts) > 1 and len(parts[0]) == 10 and parts[0].count('-') == 2:
                # Looks like a date format (YYYY-MM-DD)
                task_text = parts[1]
            else:
                # No date, everything after "x " is the task text
                task_text = line_after_x
            title, description, order = parse_task_text(task_text)
        elif "status:in_progress" in line:
            task_text = line.replace("status:in_progress", "").strip()
            title, description, order = parse_task_text(task_text)
        else:
            title, description, order = parse_task_text(line)
            
        # If no order, assign one
        if order is None:
            order = next_order
            modified = True
            
            # Reconstruct the line with order
            if line.startswith('x '):
                if " " in line[2:] and line[2:].split(" ")[0].isdigit():
                    # Has completion date
                    completion_date = line[2:].split(" ")[0]
                    lines[i] = f"x {completion_date} {format_task_text(title, description, order)}"
                else:
                    lines[i] = f"x {format_task_text(title, description, order)}"
            elif "status:in_progress" in line:
                lines[i] = f"{format_task_text(title, description, order)} status:in_progress"
            else:
                lines[i] = format_task_text(title, description, order)
                
        next_order = max(next_order, (order or 0) + 1)
    
    if modified:
        write_lines(lines)
        print(f"Auto-assigned orders up to {next_order - 1}")
    
    return next_order

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
            # Completed task: "x 2024-01-15 Task title | description" or "x Task title"
            parts = line[2:].strip().split(" ", 1)
            if len(parts) >= 2 and parts[0].count('-') == 2:
                # Has date format YYYY-MM-DD
                task_text = parts[1]
            else:
                # No date, everything after "x " is the task text
                task_text = line[2:].strip()
            
            title, description, order = parse_task_text(task_text)
            done_tasks.append((idx, title, description, order))
            
        elif "status:in_progress" in line:
            # In progress task: "Task title | description status:in_progress"
            task_text = line.replace("status:in_progress", "").strip()
            title, description, order = parse_task_text(task_text)
            in_progress_tasks.append((idx, title, description, order))
            
        else:
            # Open task: just the plain text
            title, description, order = parse_task_text(line)
            open_tasks.append((idx, title, description, order))
    
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
    
    # Sort tasks by their order field (None orders go to end)
    def sort_by_order(tasks):
        return sorted(tasks, key=lambda x: x[3] if x[3] is not None else float('inf'))
    
    in_progress_tasks = sort_by_order(in_progress_tasks)
    open_tasks = sort_by_order(open_tasks) 
    done_tasks = sort_by_order(done_tasks)
    
    # Convert to UI format with continuous numbering
    task_num = 1
    ui_tasks = {
        'in_progress': [],
        'open': [],
        'done': []
    }
    
    # In progress tasks first (these show up in "Today")
    for file_idx, title, description, order in in_progress_tasks:
        ui_tasks['in_progress'].append({
            'id': task_num,
            'file_idx': file_idx,
            'title': title,
            'description': description,
            'order': order,
            'status': 'in_progress'
        })
        task_num += 1
    
    # Open tasks next
    for file_idx, title, description, order in open_tasks:
        ui_tasks['open'].append({
            'id': task_num,
            'file_idx': file_idx,
            'title': title,
            'description': description,
            'order': order,
            'status': 'open'
        })
        task_num += 1
    
    # Done tasks (no numbering needed)
    for file_idx, title, description, order in done_tasks:
        ui_tasks['done'].append({
            'file_idx': file_idx,
            'title': title,
            'description': description,
            'order': order,
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
        description = data.get('description', '').strip()
        
        if not title:
            return jsonify({'error': 'Task title is required'}), 400
        
        lines = read_lines()
        task_text = format_task_text(title, description)
        lines.append(task_text)
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
        
        file_idx, title, description, order = all_active_tasks[task_id-1]
        completion_date = datetime.now().strftime("%Y-%m-%d")
        task_text = format_task_text(title, description)
        lines[file_idx] = f"x {completion_date} {task_text}"
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
        
        file_idx, title, description, order = open_tasks[open_task_num-1]
        task_text = format_task_text(title, description)
        lines[file_idx] = f"{task_text} status:in_progress"
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
        
        file_idx, title, description, order = in_progress_tasks[task_id-1]
        task_text = format_task_text(title, description)
        lines[file_idx] = task_text
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
        
        # Extract the task text (remove "x 2025-09-02 " prefix)
        parts = line[2:].strip().split(" ", 1)
        if len(parts) >= 2 and parts[0].count('-') == 2:
            # Has date format YYYY-MM-DD
            task_text = parts[1]
        else:
            # No date, everything after "x " is the task text
            task_text = line[2:].strip()
        
        title, description, order = parse_task_text(task_text)
        
        # Make it an open task again
        lines[file_idx] = format_task_text(title, description, order)
        write_lines(lines)
        
        return jsonify({'success': True, 'message': f'Uncompleted: {title}'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:file_idx>/details')
def get_task_details(file_idx):
    """Get detailed information for a specific task"""
    try:
        lines = read_lines()
        if file_idx < 0 or file_idx >= len(lines):
            return jsonify({'error': 'Task not found'}), 404
        
        line = lines[file_idx].strip()
        if not line:
            return jsonify({'error': 'Task not found'}), 404
        
        # Parse the task
        if line.startswith("x "):
            # Completed task
            parts = line[2:].strip().split(" ", 1)
            if len(parts) >= 2 and parts[0].count('-') == 2:
                task_text = parts[1]
                completion_date = parts[0]
            else:
                task_text = line[2:].strip()
                completion_date = None
            
            title, description, order = parse_task_text(task_text)
            status = 'done'
        elif "status:in_progress" in line:
            # In progress task
            task_text = line.replace("status:in_progress", "").strip()
            title, description, order = parse_task_text(task_text)
            status = 'in_progress'
            completion_date = None
        else:
            # Open task
            title, description, order = parse_task_text(line)
            status = 'open'
            completion_date = None
        
        return jsonify({
            'file_idx': file_idx,
            'title': title,
            'description': description,
            'status': status,
            'completion_date': completion_date,
            'project': 'Inbox',  # Default for now
            'date': 'Today' if status != 'done' else completion_date,
            'priority': None,
            'labels': [],
            'reminders': [],
            'location': None
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:file_idx>/update', methods=['POST'])
def update_task(file_idx):
    """Update title and description for a specific task"""
    try:
        data = request.get_json()
        new_title = data.get('title', '').strip()
        new_description = data.get('description', '').strip()
        
        if not new_title:
            return jsonify({'error': 'Task title cannot be empty'}), 400
        
        lines = read_lines()
        if file_idx < 0 or file_idx >= len(lines):
            return jsonify({'error': 'Task not found'}), 404
        
        line = lines[file_idx].strip()
        if not line:
            return jsonify({'error': 'Task not found'}), 404
        
        # Parse the current task and update with new title and description
        if line.startswith("x "):
            # Completed task
            parts = line[2:].strip().split(" ", 1)
            if len(parts) >= 2 and parts[0].count('-') == 2:
                completion_prefix = f"x {parts[0]} "
            else:
                completion_prefix = "x "
            
            lines[file_idx] = completion_prefix + format_task_text(new_title, new_description)
            
        elif "status:in_progress" in line:
            # In progress task
            lines[file_idx] = format_task_text(new_title, new_description) + " status:in_progress"
            
        else:
            # Open task
            lines[file_idx] = format_task_text(new_title, new_description)
        
        write_lines(lines)
        return jsonify({'success': True, 'message': 'Task updated'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:file_idx>/update_description', methods=['POST'])
def update_task_description(file_idx):
    """Update description for a specific task (deprecated - use /update instead)"""
    try:
        data = request.get_json()
        new_description = data.get('description', '').strip()
        
        lines = read_lines()
        if file_idx < 0 or file_idx >= len(lines):
            return jsonify({'error': 'Task not found'}), 404
        
        line = lines[file_idx].strip()
        if not line:
            return jsonify({'error': 'Task not found'}), 404
        
        # Parse the current task to extract title
        if line.startswith("x "):
            # Completed task
            parts = line[2:].strip().split(" ", 1)
            if len(parts) >= 2 and parts[0].count('-') == 2:
                completion_prefix = f"x {parts[0]} "
                task_text = parts[1]
            else:
                completion_prefix = "x "
                task_text = line[2:].strip()
            
            title, _, _ = parse_task_text(task_text)
            lines[file_idx] = completion_prefix + format_task_text(title, new_description)
            
        elif "status:in_progress" in line:
            # In progress task
            task_text = line.replace("status:in_progress", "").strip()
            title, _, _ = parse_task_text(task_text)
            lines[file_idx] = format_task_text(title, new_description) + " status:in_progress"
            
        else:
            # Open task
            title, _, _ = parse_task_text(line)
            lines[file_idx] = format_task_text(title, new_description)
        
        write_lines(lines)
        return jsonify({'success': True, 'message': 'Description updated'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/reorder-simple', methods=['POST'])
def reorder_tasks_simple():
    """Reorder tasks using a complete new order sequence"""
    try:
        data = request.get_json()
        new_order_sequence = data.get('new_order_sequence')
        
        if not new_order_sequence or not isinstance(new_order_sequence, list):
            return jsonify({'error': 'Missing or invalid new_order_sequence'}), 400
        
        print(f"Reordering tasks to sequence: {new_order_sequence}")
        
        lines = read_lines()
        updated_lines = []
        
        # Create a mapping of old_order -> new_order
        order_mapping = {}
        for new_position, old_order in enumerate(new_order_sequence):
            order_mapping[old_order] = new_position + 1
        
        print(f"Order mapping: {order_mapping}")
        
        for line in lines:
            if not line.strip():
                updated_lines.append(line)
                continue
                
            # Parse the task to get its current order
            if line.startswith('x '):
                # Completed task
                line_after_x = line[2:].strip()
                parts = line_after_x.split(" ", 1)
                if len(parts) > 1 and len(parts[0]) == 10 and parts[0].count('-') == 2:
                    task_text = parts[1]
                    completion_prefix = f"x {parts[0]} "
                else:
                    task_text = line_after_x
                    completion_prefix = "x "
                title, description, order = parse_task_text(task_text)
            elif "status:in_progress" in line:
                task_text = line.replace("status:in_progress", "").strip()
                title, description, order = parse_task_text(task_text)
                completion_prefix = ""
                in_progress_suffix = " status:in_progress"
            else:
                title, description, order = parse_task_text(line)
                completion_prefix = ""
                in_progress_suffix = ""
            
            # Update the order based on the mapping
            new_order = order_mapping.get(order, order)  # Keep original if not in mapping
            
            # Reconstruct the line with the new order
            new_task_text = format_task_text(title, description, new_order)
            if line.startswith('x '):
                updated_lines.append(f"{completion_prefix}{new_task_text}")
            elif "status:in_progress" in line:
                updated_lines.append(f"{new_task_text}{in_progress_suffix}")
            else:
                updated_lines.append(new_task_text)
        
        write_lines(updated_lines)
        return jsonify({'success': True, 'message': 'Tasks reordered successfully'})
    
    except Exception as e:
        print(f"Error in reorder_tasks_simple: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/reorder', methods=['POST'])
def reorder_task():
    """Reorder a task by updating order numbers"""
    try:
        data = request.get_json()
        task_order = data.get('task_order')  # Current order of the task to move
        target_order = data.get('target_order')  # Where to move it
        
        if task_order is None or target_order is None:
            return jsonify({'error': 'Missing task_order or target_order'}), 400
        
        if task_order == target_order:
            return jsonify({'success': True, 'message': 'No change needed'})
        
        lines = read_lines()
        updated_lines = []
        
        for line in lines:
            if not line.strip():
                updated_lines.append(line)
                continue
                
            # Parse the task to get its current order
            if line.startswith('x '):
                # Completed task: "x 2023-12-01 Task text" or "x Task text"
                line_after_x = line[2:].strip()
                parts = line_after_x.split(" ", 1)
                if len(parts) > 1 and len(parts[0]) == 10 and parts[0].count('-') == 2:
                    # Has completion date
                    task_text = parts[1]
                    completion_date = parts[0]
                    completion_prefix = f"x {completion_date} "
                else:
                    # No date, everything after "x " is the task text
                    task_text = line_after_x
                    completion_prefix = "x "
                title, description, order = parse_task_text(task_text)
            elif "status:in_progress" in line:
                task_text = line.replace("status:in_progress", "").strip()
                title, description, order = parse_task_text(task_text)
                completion_prefix = ""
                in_progress_suffix = " status:in_progress"
            else:
                title, description, order = parse_task_text(line)
                completion_prefix = ""
                in_progress_suffix = ""
            
            # Update the order based on the reordering logic
            new_order = order
            
            # Only update order if task has an order number
            if order is not None:
                if order == task_order:
                    # This is the task being moved
                    new_order = target_order
                elif task_order < target_order and order > task_order and order <= target_order:
                    # Tasks that need to shift down
                    new_order = order - 1
                elif task_order > target_order and order >= target_order and order < task_order:
                    # Tasks that need to shift up
                    new_order = order + 1
            
            # Reconstruct the line with the new order
            new_task_text = format_task_text(title, description, new_order)
            if line.startswith('x '):
                updated_lines.append(f"{completion_prefix}{new_task_text}")
            elif "status:in_progress" in line:
                updated_lines.append(f"{new_task_text}{in_progress_suffix}")
            else:
                updated_lines.append(new_task_text)
        
        write_lines(updated_lines)
        return jsonify({'success': True, 'message': 'Task reordered successfully'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    ensure_file()  # Initialize todo.txt on startup
    app.run(debug=True, port=5001)
