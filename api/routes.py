"""
API routes for the todo application
"""
from flask import Blueprint, request, jsonify
from datetime import datetime
from typing import Dict, Any
import requests
import json

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
        
        return jsonify({
            'tasks': ui_tasks,
            'counts': {
                'today': today_count
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
        
        # Calculate UI ID using the same logic as the main tasks endpoint
        open_tasks, in_progress_tasks, done_tasks = collection.get_by_status()
        all_active_tasks = in_progress_tasks + open_tasks
        
        # Find the task in the active tasks list to get its UI ID
        ui_id = None
        for i, active_task in enumerate(all_active_tasks):
            if active_task.file_idx == file_idx:
                ui_id = i + 1
                break
        
        details = task.to_dict(ui_id=ui_id)
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


@api.route('/tasks/<int:file_idx>/delete', methods=['DELETE'])
def delete_task(file_idx):
    """Delete a specific task permanently"""
    try:
        collection = file_manager.load_tasks()
        task = collection.get_task_by_file_idx(file_idx)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        # Store task title for response message
        task_title = task.title
        
        # Remove the task from the collection
        collection.remove_task_by_file_idx(file_idx)
        file_manager.save_tasks(collection)
        
        return jsonify(APIResponse.success(f'Deleted: {task_title}'))
    
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


@api.route('/chat', methods=['POST'])
def chat():
    """Chat with Ollama AI assistant"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        conversation_history = data.get('conversation_history', [])
        
        if not message:
            return APIResponse.error('Message is required')
        
        # Load current tasks for context
        collection = file_manager.load_tasks()
        open_tasks, in_progress_tasks, done_tasks = collection.get_by_status()
        
        # Build context about tasks
        task_context = _build_task_context(open_tasks, in_progress_tasks, done_tasks)
        
        # Build conversation context
        conversation_context = _build_conversation_context(conversation_history)
        
        # Create the coaching prompt
        system_prompt = _get_coaching_system_prompt(task_context)
        
        # Send to Ollama
        response = _send_to_ollama(system_prompt, conversation_context + "\n\nHuman: " + message)
        
        return jsonify({
            'success': True,
            'response': response
        })
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


def _build_task_context(open_tasks, in_progress_tasks, done_tasks):
    """Build context about current tasks with descriptions"""
    context = []
    
    if in_progress_tasks:
        context.append("Currently in progress:")
        for task in in_progress_tasks[:5]:  # Limit to 5 most recent
            if task.description and task.description.strip():
                context.append(f"- {task.title}: {task.description}")
            else:
                context.append(f"- {task.title}")
    
    if open_tasks:
        context.append("\nOpen tasks:")
        for task in open_tasks[:10]:  # Limit to 10 most recent
            if task.description and task.description.strip():
                context.append(f"- {task.title}: {task.description}")
            else:
                context.append(f"- {task.title}")
    
    completed_today = [t for t in done_tasks if t.completion_date == datetime.now().strftime("%Y-%m-%d")]
    if completed_today:
        context.append(f"\nCompleted today ({len(completed_today)} tasks):")
        for task in completed_today[:5]:
            if task.description and task.description.strip():
                context.append(f"- {task.title}: {task.description}")
            else:
                context.append(f"- {task.title}")
    
    return "\n".join(context) if context else "No tasks currently in the system."


def _build_conversation_context(conversation_history):
    """Build conversation context from history"""
    context = []
    for msg in conversation_history[-6:]:  # Last 6 messages for context
        role = "Human" if msg['type'] == 'user' else "Assistant"
        context.append(f"{role}: {msg['content']}")
    return "\n".join(context)


def _get_coaching_system_prompt(task_context):
    """Get the system prompt for the coaching assistant"""
    return f"""You are Giscard, a productivity coach and personal assistant. You help users manage their tasks, stay motivated, and achieve their goals.

Your personality:
- Supportive and encouraging, but not overly cheerful
- Direct and practical in your advice
- Focused on productivity and getting things done
- Understanding of the challenges of task management

Current task context:
{task_context}

Guidelines:
- Keep responses concise and actionable
- Offer specific advice based on the user's tasks and their descriptions
- Use task descriptions to provide more targeted productivity advice
- Suggest prioritization, time management, and productivity techniques
- Be empathetic to productivity struggles
- Don't make assumptions about tasks you can't see
- If asked about tasks, refer to what you can see in the context above
- When multiple tasks have similar descriptions, suggest grouping or batching them

Remember: You now have access to both task titles AND descriptions, so you can provide much more personalized and specific advice based on the actual work content."""


def _send_to_ollama(system_prompt, user_input):
    """Send request to Ollama API"""
    ollama_url = "http://localhost:11434/api/generate"
    
    payload = {
        "model": "llama3.1:8b",
        "prompt": f"{system_prompt}\n\n{user_input}\n\nAssistant:",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 500
        }
    }
    
    try:
        response = requests.post(ollama_url, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        return result.get('response', 'Sorry, I had trouble generating a response.')
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to connect to Ollama: {str(e)}. Make sure Ollama is running with llama3.1:8b model.")
