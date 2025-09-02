"""
API routes for the todo application
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Dict, Any

from models.task import Task, TaskCollection
from utils.file_manager import TodoFileManager


# Create Blueprint
api = Blueprint('api', __name__, url_prefix='/api')

# Initialize file manager
file_manager = TodoFileManager()


class APIResponse:
    """Helper class for consistent API responses"""
    
    @staticmethod
    def success(message: str = "Success", data: Any = None) -> Dict[str, Any]:
        response = {"success": True, "message": message}
        if data is not None:
            response.update(data)
        return response
    
    @staticmethod
    def error(message: str, status_code: int = 400) -> tuple:
        return jsonify({"error": message}), status_code


@api.route('/tasks')
def get_tasks():
    """Get all tasks in a format suitable for the UI"""
    try:
        collection = file_manager.load_tasks()
        open_tasks, in_progress_tasks, done_tasks = collection.get_by_status()
        
        # Convert to UI format with continuous numbering
        task_num = 1
        ui_tasks = {
            'in_progress': [],
            'open': [],
            'done': []
        }
        
        # In progress tasks first (these show up in "Today")
        for task in in_progress_tasks:
            ui_tasks['in_progress'].append(task.to_dict(ui_id=task_num))
            task_num += 1
        
        # Open tasks next
        for task in open_tasks:
            ui_tasks['open'].append(task.to_dict(ui_id=task_num))
            task_num += 1
        
        # Done tasks (no numbering needed)
        for task in done_tasks:
            ui_tasks['done'].append(task.to_dict())
        
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
        
    except Exception as e:
        return APIResponse.error(f"Failed to load tasks: {str(e)}", 500)


@api.route('/tasks/add', methods=['POST'])
def add_task():
    """Add a new task"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        
        if not title:
            return APIResponse.error('Task title is required')
        
        collection = file_manager.load_tasks()
        task = collection.add_task(title, description)
        file_manager.save_tasks(collection)
        
        return jsonify(APIResponse.success(f'Added: {title}'))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api.route('/tasks/<int:task_id>/done', methods=['POST'])
def mark_done(task_id):
    """Mark a task as done"""
    try:
        collection = file_manager.load_tasks()
        open_tasks, in_progress_tasks, _ = collection.get_by_status()
        
        # Match the display order: in_progress first, then open
        all_active_tasks = in_progress_tasks + open_tasks
        if task_id < 1 or task_id > len(all_active_tasks):
            return APIResponse.error('Invalid task ID')
        
        task = all_active_tasks[task_id - 1]
        task.mark_done()
        file_manager.save_tasks(collection)
        
        return jsonify(APIResponse.success(f'Done: {task.title}'))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api.route('/tasks/<int:task_id>/start', methods=['POST'])
def start_task(task_id):
    """Start a task (mark as in progress)"""
    try:
        collection = file_manager.load_tasks()
        open_tasks, in_progress_tasks, _ = collection.get_by_status()
        
        # The task_id for start is based on open tasks only
        open_task_num = task_id - len(in_progress_tasks)
        if open_task_num < 1 or open_task_num > len(open_tasks):
            return APIResponse.error('Invalid task ID for starting')
        
        task = open_tasks[open_task_num - 1]
        task.mark_in_progress()
        file_manager.save_tasks(collection)
        
        return jsonify(APIResponse.success(f'Started: {task.title}'))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api.route('/tasks/<int:task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """Stop a task (remove in progress status)"""
    try:
        collection = file_manager.load_tasks()
        _, in_progress_tasks, _ = collection.get_by_status()
        
        if task_id < 1 or task_id > len(in_progress_tasks):
            return APIResponse.error('Invalid task ID for stopping')
        
        task = in_progress_tasks[task_id - 1]
        task.mark_open()
        file_manager.save_tasks(collection)
        
        return jsonify(APIResponse.success(f'Stopped: {task.title}'))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api.route('/tasks/uncomplete', methods=['POST'])
def uncomplete_task():
    """Uncomplete a completed task (make it open again)"""
    try:
        data = request.get_json()
        file_idx = data.get('file_idx')
        
        if file_idx is None:
            return APIResponse.error('file_idx is required')
        
        collection = file_manager.load_tasks()
        task = collection.get_task_by_file_idx(file_idx)
        
        if not task:
            return APIResponse.error('Task not found')
        
        if task.status != 'done':
            return APIResponse.error('Task is not completed')
        
        task.mark_open()
        file_manager.save_tasks(collection)
        
        return jsonify(APIResponse.success(f'Uncompleted: {task.title}'))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api.route('/tasks/<int:file_idx>/details')
def get_task_details(file_idx):
    """Get detailed information for a specific task"""
    try:
        collection = file_manager.load_tasks()
        task = collection.get_task_by_file_idx(file_idx)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        details = task.to_dict()
        details.update({
            'project': 'Inbox',  # Default for now
            'date': 'Today' if task.status != 'done' else task.completion_date,
            'priority': None,
            'labels': [],
            'reminders': [],
            'location': None
        })
        
        return jsonify(details)
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api.route('/tasks/<int:file_idx>/update', methods=['POST'])
def update_task(file_idx):
    """Update title and description for a specific task"""
    try:
        data = request.get_json()
        new_title = data.get('title', '').strip()
        new_description = data.get('description', '').strip()
        
        if not new_title:
            return APIResponse.error('Task title cannot be empty')
        
        collection = file_manager.load_tasks()
        task = collection.get_task_by_file_idx(file_idx)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        task.update_content(new_title, new_description)
        file_manager.save_tasks(collection)
        
        return jsonify(APIResponse.success('Task updated'))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api.route('/tasks/<int:file_idx>/update_description', methods=['POST'])
def update_task_description(file_idx):
    """Update description for a specific task (deprecated - use /update instead)"""
    try:
        data = request.get_json()
        new_description = data.get('description', '').strip()
        
        collection = file_manager.load_tasks()
        task = collection.get_task_by_file_idx(file_idx)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        task.description = new_description
        file_manager.save_tasks(collection)
        
        return jsonify(APIResponse.success('Description updated'))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api.route('/tasks/reorder-simple', methods=['POST'])
def reorder_tasks_simple():
    """Reorder tasks using a complete new order sequence"""
    try:
        data = request.get_json()
        new_order_sequence = data.get('new_order_sequence')
        file_idx_sequence = data.get('file_idx_sequence')
        
        collection = file_manager.load_tasks()
        
        if file_idx_sequence and isinstance(file_idx_sequence, list):
            # Use the new file index based reordering (preferred)
            collection.reorder_by_file_indices(file_idx_sequence)
        elif new_order_sequence and isinstance(new_order_sequence, list):
            # Fallback to order-based reordering for backward compatibility
            collection.reorder_tasks(new_order_sequence)
        else:
            return APIResponse.error('Missing or invalid reorder sequence')
        
        file_manager.save_tasks(collection)
        
        return jsonify(APIResponse.success('Tasks reordered successfully'))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api.route('/tasks/reorder', methods=['POST'])
def reorder_task():
    """Reorder a task by updating order numbers (legacy endpoint)"""
    try:
        data = request.get_json()
        task_order = data.get('task_order')
        target_order = data.get('target_order')
        
        if task_order is None or target_order is None:
            return APIResponse.error('Missing task_order or target_order')
        
        if task_order == target_order:
            return jsonify(APIResponse.success('No change needed'))
        
        collection = file_manager.load_tasks()
        
        # Find tasks and update their orders using legacy logic
        for task in collection.tasks:
            if task.order is not None:
                if task.order == task_order:
                    task.order = target_order
                elif task_order < target_order and target_order >= task.order > task_order:
                    task.order -= 1
                elif task_order > target_order and target_order <= task.order < task_order:
                    task.order += 1
        
        file_manager.save_tasks(collection)
        
        return jsonify(APIResponse.success('Task reordered successfully'))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)
