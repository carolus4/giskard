"""
Clean REST API routes for the todo application
"""
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

from models.task_db import TaskDB
# from utils.classification_manager import ClassificationManager

logger = logging.getLogger(__name__)


# Create Blueprint
api = Blueprint('api', __name__, url_prefix='/api')


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
        # If filtering by completed_at, only include tasks that have been completed
        if filter_gte or filter_lt:
            # Only include completed tasks with valid completed_at
            if task.status != 'done' or not task.completed_at:
                continue  # Skip tasks that aren't completed or have null completed_at
            
            # Parse task completion date
            try:
                task_completed = datetime.fromisoformat(task.completed_at.replace('Z', '+00:00'))
            except ValueError:
                continue  # Skip tasks with invalid completed_at
                
            # Apply completed_at_gte filter (greater than or equal)
            if filter_gte and task_completed < filter_gte:
                continue
                
            # Apply completed_at_lt filter (less than)
            if filter_lt and task_completed >= filter_lt:
                continue
                
            filtered_tasks.append(task)
        else:
            # No completed_at filtering, include all tasks
            filtered_tasks.append(task)
    
    return filtered_tasks


def convert_period_to_date_range(period: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Convert a period string to date range (gte, lt)
    
    Args:
        period: Period string (this_week, this_month, last_week, last_month, last_7_days, last_30_days)
        
    Returns:
        Tuple of (completed_at_gte, completed_at_lt) ISO date strings
    """
    now = datetime.now()
    today = now.date()
    
    if period == "this_week":
        # Start of this week (Monday)
        days_since_monday = today.weekday()
        start_of_week = today - timedelta(days=days_since_monday)
        return start_of_week.isoformat(), None
    
    elif period == "this_month":
        # Start of this month
        start_of_month = today.replace(day=1)
        return start_of_month.isoformat(), None
    
    elif period == "last_week":
        # Start and end of last week
        days_since_monday = today.weekday()
        start_of_this_week = today - timedelta(days=days_since_monday)
        start_of_last_week = start_of_this_week - timedelta(days=7)
        end_of_last_week = start_of_this_week - timedelta(days=1)
        return start_of_last_week.isoformat(), end_of_last_week.isoformat()
    
    elif period == "last_month":
        # Start and end of last month
        if today.month == 1:
            start_of_last_month = today.replace(year=today.year - 1, month=12, day=1)
        else:
            start_of_last_month = today.replace(month=today.month - 1, day=1)
        
        start_of_this_month = today.replace(day=1)
        end_of_last_month = start_of_this_month - timedelta(days=1)
        return start_of_last_month.isoformat(), end_of_last_month.isoformat()
    
    elif period == "last_7_days":
        # 7 days ago to now
        seven_days_ago = today - timedelta(days=7)
        return seven_days_ago.isoformat(), None
    
    elif period == "last_30_days":
        # 30 days ago to now
        thirty_days_ago = today - timedelta(days=30)
        return thirty_days_ago.isoformat(), None
    
    elif period == "today":
        # Today only
        return today.isoformat(), (today + timedelta(days=1)).isoformat()
    
    elif period == "yesterday":
        # Yesterday only
        yesterday = today - timedelta(days=1)
        return yesterday.isoformat(), today.isoformat()
    
    else:
        raise ValueError(f"Invalid period: {period}. Valid options: this_week, this_month, last_week, last_month, last_7_days, last_30_days, today, yesterday")


@api.route('/tasks', methods=['GET'])
def get_tasks():
    """Get all tasks grouped by status with optional filtering

    Query Parameters:
        status: Filter by status (open, in_progress, done) - single status or comma-separated list
        completed_at_gte: ISO date string (YYYY-MM-DD) - only include tasks completed on or after this date
        completed_at_lt: ISO date string (YYYY-MM-DD) - only include tasks completed before this date
        completed_at_period: Period string (this_week, this_month, last_week, last_month, last_7_days, last_30_days, today, yesterday)
    """
    try:
        # Get query parameters
        status_filter = request.args.get('status')
        completed_at_gte = request.args.get('completed_at_gte')
        completed_at_lt = request.args.get('completed_at_lt')
        completed_at_period = request.args.get('completed_at_period')

        # Parse status filter
        status_filters = None
        if status_filter:
            if ',' in status_filter:
                status_filters = [s.strip() for s in status_filter.split(',')]
            else:
                status_filters = [status_filter.strip()]

            # Validate status filters
            valid_statuses = ['open', 'in_progress', 'done']
            for status in status_filters:
                if status not in valid_statuses:
                    return APIResponse.error(f"Invalid status filter: {status}. Valid options: {', '.join(valid_statuses)}", 400)
        
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
        
        # Handle completed_at_period parameter
        if completed_at_period:
            try:
                period_gte, period_lt = convert_period_to_date_range(completed_at_period)
                # Override any existing date filters with period-based ones
                completed_at_gte = period_gte
                completed_at_lt = period_lt
            except ValueError as e:
                return APIResponse.error(str(e), 400)
        
        # Get all tasks
        open_tasks, in_progress_tasks, done_tasks = TaskDB.get_by_status()

        # Apply status filtering if specified
        if status_filters:
            filtered_open = []
            filtered_in_progress = []
            filtered_done = []

            for status in status_filters:
                if status == 'open':
                    filtered_open.extend(open_tasks)
                elif status == 'in_progress':
                    filtered_in_progress.extend(in_progress_tasks)
                elif status == 'done':
                    filtered_done.extend(done_tasks)

            open_tasks = filtered_open
            in_progress_tasks = filtered_in_progress
            done_tasks = filtered_done

        # Apply completed_at filtering to done tasks
        if completed_at_gte or completed_at_lt:
            done_tasks = filter_tasks_by_completed_at(done_tasks, completed_at_gte, completed_at_lt)

            # If completed_at filtering is applied without status filter, only return done tasks
            if not status_filters:
                # Only return done tasks when completed_at filtering is applied without status filter
                in_progress_tasks = []
                open_tasks = []

        # Convert to UI format (exclude description for list view)
        def task_to_list_dict(task):
            """Convert task to dict format for list view (excluding description)"""
            return {
                'id': task.id,
                'title': task.title,
                'status': task.status,
                'sort_key': task.sort_key,
                'project': task.project,
                'categories': task.categories,
                'created_at': task.created_at,
                'updated_at': task.updated_at,
                'started_at': task.started_at,
                'completed_at': task.completed_at
                # Note: description is intentionally excluded for list view
            }

        ui_tasks = {
            'in_progress': [task_to_list_dict(task) for task in in_progress_tasks],
            'open': [task_to_list_dict(task) for task in open_tasks],
            'done': [task_to_list_dict(task) for task in done_tasks]
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
        
        return jsonify(APIResponse.success("Tasks loaded successfully", response_data))
        
    except Exception as e:
        logger.error(f"Failed to load tasks: {str(e)}")
        return APIResponse.error(f"Failed to load tasks: {str(e)}", 500)


@api.route('/tasks', methods=['POST'])
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


@api.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a specific task by ID"""
    try:
        task = TaskDB.get_by_id(task_id)
        
        if not task:
            return APIResponse.error('Task not found', 404)
        
        return jsonify(APIResponse.success("Task retrieved successfully", {'task': task.to_dict()}))
    
    except Exception as e:
        logger.error(f"Failed to get task: {str(e)}")
        return APIResponse.error(f"Failed to get task: {str(e)}", 500)


@api.route('/tasks/<int:task_id>', methods=['PUT'])
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

        # Handle date fields
        if 'completed_at' in data:
            completed_at = data['completed_at']
            if completed_at == "" or completed_at.lower() == "null":
                # Clear completion date
                task.completed_at = None
                if task.status == 'done':
                    task.status = 'open'  # Reset status if clearing completion
            else:
                # Validate and set completion date
                from datetime import datetime
                try:
                    # Parse the provided date
                    parsed_date = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    task.completed_at = parsed_date.isoformat()
                    # If setting completion date, mark as done
                    if task.status != 'done':
                        task.status = 'done'
                except ValueError:
                    return APIResponse.error(f"Invalid completed_at format: {completed_at}. Use ISO format (e.g., 2025-01-15T14:30:00)", 400)

        if 'started_at' in data:
            started_at = data['started_at']
            if started_at == "" or started_at.lower() == "null":
                # Clear start date
                task.started_at = None
            else:
                # Validate and set start date
                from datetime import datetime
                try:
                    # Parse the provided date
                    parsed_date = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                    task.started_at = parsed_date.isoformat()
                    # If setting start date, mark as in progress
                    if task.status == 'open':
                        task.status = 'in_progress'
                except ValueError:
                    return APIResponse.error(f"Invalid started_at format: {started_at}. Use ISO format (e.g., 2025-01-15T14:30:00)", 400)
        
        # Save changes
        task.save()

        # Enqueue for classification if title or description changed
        # But skip classification for debounced updates (real-time auto-saves)
        if ('title' in data or 'description' in data) and not data.get('_debounced', False):
            from app import classification_manager
            classification_manager.enqueue_classification(task)

        return jsonify(APIResponse.success('Task updated', {'task': task.to_dict()}))
    
    except Exception as e:
        logger.error(f"Failed to update task: {str(e)}")
        return APIResponse.error(f"Failed to update task: {str(e)}", 500)


@api.route('/tasks/<int:task_id>/status', methods=['PUT', 'PATCH'])
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


@api.route('/tasks/<int:task_id>', methods=['DELETE'])
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


@api.route('/tasks/reorder', methods=['POST'])
def reorder_tasks():
    """Reorder tasks by updating their sort_key values"""
    try:
        data = request.get_json()

        if not data or 'task_ids' not in data:
            return APIResponse.error('task_ids array is required', 400)

        task_ids = data['task_ids']

        if not isinstance(task_ids, list):
            return APIResponse.error('task_ids must be an array', 400)

        if not task_ids:
            return APIResponse.error('task_ids cannot be empty', 400)

        # Validate that all task IDs exist
        for task_id in task_ids:
            if not isinstance(task_id, int):
                return APIResponse.error(f'All task_ids must be integers, got {type(task_id)}', 400)

            task = TaskDB.get_by_id(task_id)
            if not task:
                return APIResponse.error(f'Task {task_id} not found', 404)

        # Reorder tasks using the database method
        success = TaskDB.reorder_tasks(task_ids)

        if not success:
            return APIResponse.error('Failed to reorder tasks', 500)

        return jsonify(APIResponse.success(f'Reordered {len(task_ids)} tasks'))

    except Exception as e:
        logger.error(f"Failed to reorder tasks: {str(e)}")
        return APIResponse.error(f"Failed to reorder tasks: {str(e)}", 500)
