"""
Clean REST API routes for the todo application
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
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


def filter_tasks_by_completed_at(tasks: List[TaskDB], 
                                completed_at_gte: Optional[str] = None,
                                completed_at_lt: Optional[str] = None) -> List[TaskDB]:
    """Filter tasks by completed_at date range using ISO timestamp comparison"""
    from datetime import datetime
    
    # Parse filter dates - ISO timestamp format only
    filter_gte = None
    filter_lt = None
    
    if completed_at_gte:
        try:
            filter_gte = datetime.fromisoformat(completed_at_gte.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid date format: {completed_at_gte}. Use ISO format (e.g., 2025-09-29 or 2025-09-29T00:00:00)")
    
    if completed_at_lt:
        try:
            filter_lt = datetime.fromisoformat(completed_at_lt.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError(f"Invalid date format: {completed_at_lt}. Use ISO format (e.g., 2025-09-29 or 2025-09-29T00:00:00)")
    
    filtered_tasks = []
    
    for task in tasks:
        # Only apply filtering to completed tasks
        if task.status != 'done' or not task.completed_at:
            filtered_tasks.append(task)
            continue
        
        # Parse task completion date
        try:
            task_completed = datetime.fromisoformat(task.completed_at.replace('Z', '+00:00'))
        except ValueError:
            # If task completion date is invalid, include it (don't filter out)
            filtered_tasks.append(task)
            continue
            
        # Apply completed_at_gte filter (greater than or equal)
        if filter_gte and task_completed < filter_gte:
            continue
            
        # Apply completed_at_lt filter (less than)
        if filter_lt and task_completed >= filter_lt:
            continue
            
        filtered_tasks.append(task)
    
    return filtered_tasks


@api_v2.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks grouped by status with optional completed_at filtering
    
    Query Parameters:
        completed_at_gte: ISO date string (YYYY-MM-DD) - only include tasks completed on or after this date
        completed_at_lt: ISO date string (YYYY-MM-DD) - only include tasks completed before this date
    """
    try:
        # Get query parameters
        completed_at_gte = request.args.get('completed_at_gte')
        completed_at_lt = request.args.get('completed_at_lt')
        
        # Validate date formats if provided (ISO format)
        if completed_at_gte:
            try:
                datetime.fromisoformat(completed_at_gte.replace('Z', '+00:00'))
            except ValueError:
                return APIResponse.error("Invalid completed_at_gte format. Use ISO format (e.g., 2025-09-29 or 2025-09-29T00:00:00)", 400)
                
        if completed_at_lt:
            try:
                datetime.fromisoformat(completed_at_lt.replace('Z', '+00:00'))
            except ValueError:
                return APIResponse.error("Invalid completed_at_lt format. Use ISO format (e.g., 2025-09-29 or 2025-09-29T00:00:00)", 400)
        
        # Get all tasks
        open_tasks, in_progress_tasks, done_tasks = TaskDB.get_by_status()
        
        # Apply completed_at filtering to done tasks
        if completed_at_gte or completed_at_lt:
            done_tasks = filter_tasks_by_completed_at(done_tasks, completed_at_gte, completed_at_lt)
        
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
        
        # Build response
        response_data = {
            'tasks': ui_tasks,
            'counts': {
                'today': today_count,
                'completed_today': completed_today_count,
                'completed_yesterday': completed_yesterday_count
            },
            'today_date': datetime.now().strftime('Today - %A %b %d')
        }
        
        # Add filtering info to response if filters were applied
        if completed_at_gte or completed_at_lt:
            response_data['filters'] = {
                'completed_at_gte': completed_at_gte,
                'completed_at_lt': completed_at_lt,
                'filtered_done_count': len(done_tasks)
            }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Failed to load tasks: {str(e)}")
        return APIResponse.error(f"Failed to load tasks: {str(e)}", 500)


@api_v2.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        
        if not data or 'title' not in data:
            return APIResponse.error('Title is required', 400)
        
        title = data['title'].strip()
        if not title:
            return APIResponse.error('Title cannot be empty', 400)
        
        if len(title) > 200:
            return APIResponse.error('Title too long (max 200 characters)', 400)
        
        description = data.get('description', '').strip()
        project = data.get('project')
        categories = data.get('categories', [])
        
        # Validate categories
        if not isinstance(categories, list):
            return APIResponse.error('Categories must be a list', 400)
        
        # Create task
        task = TaskDB.create(title, description, project, categories)
        
        # Enqueue for classification
        from app import classification_manager
        classification_manager.enqueue_classification(task)
        
        return jsonify(APIResponse.success(f'Created: {title}', {'task': task.to_dict()}))
    
    except Exception as e:
        logger.error(f"Failed to create task: {str(e)}")
        return APIResponse.error(f"Failed to create task: {str(e)}", 500)


@api_v2.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task by ID"""
    try:
        task = TaskDB.get_by_id(task_id)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        return jsonify(task.to_dict())
    
    except Exception as e:
        logger.error(f"Failed to get task: {str(e)}")
        return APIResponse.error(f"Failed to get task: {str(e)}", 500)


@api_v2.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task"""
    try:
        task = TaskDB.get_by_id(task_id)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        data = request.get_json()
        
        if not data:
            return APIResponse.error('No data provided', 400)
        
        # Update fields
        if 'title' in data:
            title = data['title'].strip()
            if not title:
                return APIResponse.error('Title cannot be empty', 400)
            if len(title) > 200:
                return APIResponse.error('Title too long (max 200 characters)', 400)
            task.title = title
        
        if 'description' in data:
            task.description = data['description'].strip()
        
        if 'project' in data:
            task.project = data['project']
        
        if 'categories' in data:
            categories = data['categories']
            if not isinstance(categories, list):
                return APIResponse.error('Categories must be a list', 400)
            task.categories = categories
        
        # Save changes
        task.save()
        
        # Enqueue for classification if title or description changed
        if 'title' in data or 'description' in data:
            from app import classification_manager
            classification_manager.enqueue_classification(task)
        
        return jsonify(APIResponse.success('Task updated', {'task': task.to_dict()}))
    
    except Exception as e:
        logger.error(f"Failed to update task: {str(e)}")
        return APIResponse.error(f"Failed to update task: {str(e)}", 500)


@api_v2.route('/tasks/<int:task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    """Update task status"""
    try:
        task = TaskDB.get_by_id(task_id)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        data = request.get_json()
        
        if not data or 'status' not in data:
            return APIResponse.error('Status is required', 400)
        
        new_status = data['status']
        
        if new_status not in ['open', 'in_progress', 'done']:
            return APIResponse.error('Invalid status. Must be: open, in_progress, or done', 400)
        
        # Update status
        if new_status == 'done':
            task.mark_done()
        elif new_status == 'in_progress':
            task.mark_in_progress()
        elif new_status == 'open':
            task.mark_open()
        
        return jsonify(APIResponse.success(f'Status updated to {new_status}', {'task': task.to_dict()}))
    
    except Exception as e:
        logger.error(f"Failed to update task status: {str(e)}")
        return APIResponse.error(f"Failed to update task status: {str(e)}", 500)


@api_v2.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    try:
        task = TaskDB.get_by_id(task_id)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        task.delete()
        
        return jsonify(APIResponse.success('Task deleted'))
    
    except Exception as e:
        logger.error(f"Failed to delete task: {str(e)}")
        return APIResponse.error(f"Failed to delete task: {str(e)}", 500)
