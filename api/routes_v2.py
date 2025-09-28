"""
Clean REST API routes for the todo application
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from models.task_db import TaskDB
# from utils.classification_manager import ClassificationManager

logger = logging.getLogger(__name__)


# Create Blueprint
api_v2 = Blueprint('api', __name__, url_prefix='/api')


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


@api_v2.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks grouped by status"""
    try:
        open_tasks, in_progress_tasks, done_tasks = TaskDB.get_by_status()
        
        # Convert to UI format
        ui_tasks = {
            'in_progress': [task.to_dict() for task in in_progress_tasks],
            'open': [task.to_dict() for task in open_tasks],
            'done': [task.to_dict() for task in done_tasks]
        }
        
        # Calculate counts for sidebar
        today_count = len(in_progress_tasks) + len(open_tasks)
        
        # Count completed tasks for today and yesterday
        today_date = datetime.now().strftime('%Y-%m-%d')
        yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        completed_today_count = sum(1 for task in done_tasks if task.completed_at and task.completed_at.startswith(today_date))
        completed_yesterday_count = sum(1 for task in done_tasks if task.completed_at and task.completed_at.startswith(yesterday_date))
        
        return jsonify({
            'tasks': ui_tasks,
            'counts': {
                'today': today_count,
                'completed_today': completed_today_count,
                'completed_yesterday': completed_yesterday_count
            },
            'today_date': datetime.now().strftime('Today - %A %b %d')
        })
        
    except Exception as e:
        return APIResponse.error(f"Failed to load tasks: {str(e)}", 500)


@api_v2.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        project = data.get('project')
        categories = data.get('categories', [])
        
        if not title:
            return APIResponse.error('Task title is required')
        
        task = TaskDB.create(title, description, project, categories)
        
        # Enqueue for classification
        from app import classification_manager
        classification_manager.enqueue_classification(task)
        
        return jsonify(APIResponse.success(f'Created: {title}', {'task': task.to_dict()}))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api_v2.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task by ID"""
    try:
        task = TaskDB.get_by_id(task_id)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        return jsonify(task.to_dict())
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api_v2.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a specific task"""
    try:
        task = TaskDB.get_by_id(task_id)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        data = request.get_json()
        
        # Update fields if provided
        if 'title' in data:
            task.title = data['title'].strip()
        if 'description' in data:
            task.description = data['description'].strip()
        if 'project' in data:
            task.project = data['project']
        if 'categories' in data:
            task.categories = data['categories']
        
        if not task.title:
            return APIResponse.error('Task title cannot be empty')
        
        task.save()
        
        # Enqueue for re-classification
        from app import classification_manager
        classification_manager.enqueue_classification(task)
        
        return jsonify(APIResponse.success('Task updated', {'task': task.to_dict()}))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api_v2.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a specific task"""
    try:
        task = TaskDB.get_by_id(task_id)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        task_title = task.title
        task.delete()
        
        return jsonify(APIResponse.success(f'Deleted: {task_title}'))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api_v2.route('/tasks/<int:task_id>/status', methods=['PATCH'])
def update_task_status(task_id):
    """Update task status (open, in_progress, done)"""
    try:
        task = TaskDB.get_by_id(task_id)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        data = request.get_json()
        new_status = data.get('status')
        
        if new_status not in ['open', 'in_progress', 'done']:
            return APIResponse.error('Invalid status. Must be: open, in_progress, or done')
        
        # Update status using appropriate method
        if new_status == 'done':
            task.mark_done()
        elif new_status == 'in_progress':
            task.mark_in_progress()
        elif new_status == 'open':
            task.mark_open()
        
        return jsonify(APIResponse.success(f'Status updated to {new_status}', {'task': task.to_dict()}))
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api_v2.route('/tasks/reorder', methods=['POST'])
def reorder_tasks():
    """Reorder tasks by providing a list of task IDs in desired order"""
    try:
        data = request.get_json()
        task_ids = data.get('task_ids', [])
        
        if not task_ids:
            return APIResponse.error('task_ids array is required')
        
        if not isinstance(task_ids, list):
            return APIResponse.error('task_ids must be an array')
        
        # Validate that all task IDs exist
        for task_id in task_ids:
            if not isinstance(task_id, int) or task_id <= 0:
                return APIResponse.error('All task_ids must be positive integers')
            
            if not TaskDB.get_by_id(task_id):
                return APIResponse.error(f'Task with ID {task_id} not found')
        
        success = TaskDB.reorder_tasks(task_ids)
        
        if success:
            return jsonify(APIResponse.success('Tasks reordered successfully'))
        else:
            return APIResponse.error('Failed to reorder tasks', 500)
    
    except Exception as e:
        return APIResponse.error(str(e), 500)


@api_v2.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages with Ollama"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        conversation_history = data.get('conversation_history', [])
        
        if not message:
            return APIResponse.error('Message is required')
        
        # Import chat service
        from utils.chat_service import ChatService
        
        # Create chat service instance
        chat_service = ChatService()
        
        # Get response from Ollama
        response = chat_service.send_message(message, conversation_history)
        
        return jsonify(APIResponse.success('Chat response generated', {'response': response}))
    
    except Exception as e:
        return APIResponse.error(f"Chat failed: {str(e)}", 500)


@api_v2.route('/agent/undo', methods=['POST'])
def agent_undo():
    """Undo the last agent mutation
    
    DEPRECATED: This endpoint is deprecated with the V2 orchestrator.
    Undo functionality is not yet implemented in the V2 orchestrator.
    This endpoint will be removed in a future version.
    """
    try:
        # Log deprecation warning
        logger.warning("DEPRECATED: /api/agent/undo endpoint is deprecated. V2 orchestrator does not support undo functionality yet.")
        
        data = request.get_json()
        undo_token = data.get('undo_token')
        
        if not undo_token:
            return APIResponse.error('undo_token is required')
        
        # Return error indicating undo is not supported in V2
        return APIResponse.error('Undo functionality is not available in V2 orchestrator. Please use the V2 endpoint for new operations.', 501)
    
    except Exception as e:
        logger.error(f"Undo operation failed: {str(e)}")
        return APIResponse.error(f"Undo failed: {str(e)}", 500)


@api_v2.route('/agent/metrics', methods=['GET'])
def get_agent_metrics():
    """Get agent metrics and observability data"""
    try:
        from utils.agent_metrics import agent_metrics as metrics_collector
        
        metrics = metrics_collector.get_metrics()
        
        return jsonify(APIResponse.success('Metrics retrieved', {'metrics': metrics}))
    
    except Exception as e:
        logger.error(f"Failed to get metrics: {str(e)}")
        return APIResponse.error(f"Failed to get metrics: {str(e)}", 500)


