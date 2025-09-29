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
        
        # Handle completed_at field with validation
        if 'completed_at' in data:
            completed_at = data['completed_at']
            
            # If completed_at is None or empty string, clear it
            if completed_at is None or completed_at == '':
                task.completed_at = None
            else:
                # Validate the timestamp format
                try:
                    from datetime import datetime
                    parsed_date = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                except (ValueError, AttributeError) as e:
                    return APIResponse.error(
                        f'Invalid completed_at format. Must be ISO 8601 timestamp (e.g., "2025-01-15T14:30:00"). Error: {str(e)}', 
                        400
                    )
                
                # Check if completion date is in the future
                now = datetime.now()
                if parsed_date > now:
                    return APIResponse.error(
                        f'Completion date cannot be in the future. Provided: {completed_at}, Current time: {now.isoformat()}', 
                        400
                    )
                
                # Check if completion date is before task creation
                try:
                    created_date = datetime.fromisoformat(task.created_at.replace('Z', '+00:00'))
                    if parsed_date < created_date:
                        return APIResponse.error(
                            f'Completion date cannot be before task creation. Provided: {completed_at}, Created: {task.created_at}', 
                            400
                        )
                except (ValueError, AttributeError):
                    # If we can't parse created_at, skip this validation
                    pass
                
                # Set the validated completion date
                task.completed_at = completed_at
        
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


