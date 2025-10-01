"""
Action wrappers for existing services
"""
import logging
from typing import Dict, Any, Optional, Tuple, List, Union
from utils.http_client import APIClient

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes actions by calling existing services via HTTP API"""

    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.api_client = APIClient(base_url)
    
    def create_task(self, title: str, description: str = "", project: Optional[str] = None,
                   categories: Optional[List[str]] = None) -> Tuple[bool, Dict[str, Any]]:
        """Create a new task"""
        try:
            # Use HTTP API call instead of direct DB access
            response_data = self.api_client.create_task(title, description, project, categories or [])

            # Enqueue for classification using the returned task data
            task_data = response_data.get('task', {})
            task_id = task_data.get('id')

            if task_id:
                # Create a temporary TaskDB instance for classification (this will be refactored later)
                from models.task_db import TaskDB
                task = TaskDB(
                    id=task_id,
                    title=task_data.get('title', title),
                    description=task_data.get('description', description),
                    project=task_data.get('project'),
                    categories=task_data.get('categories', categories or []),
                    status=task_data.get('status', 'open'),
                    sort_key=task_data.get('sort_key'),
                    created_at=task_data.get('created_at'),
                    updated_at=task_data.get('updated_at'),
                    started_at=task_data.get('started_at'),
                    completed_at=task_data.get('completed_at')
                )

                # Enqueue for classification
                from app import classification_manager
                classification_manager.enqueue_classification(task)

            return True, {
                "task_id": task_id,
                "task_title": title,
                "message": f"Created task: {title}"
            }
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            return False, {"error": str(e)}
    
    def update_task_status(self, task_id: int, status: str) -> Tuple[bool, Dict[str, Any]]:
        """Update task status"""
        try:
            # Use HTTP API call instead of direct DB access
            response_data = self.api_client.update_task_status(task_id, status)

            return True, {
                "task_id": task_id,
                "status": status,
                "message": f"Updated task {task_id} status to {status}"
            }
        except Exception as e:
            logger.error(f"Failed to update task status: {str(e)}")
            return False, {"error": str(e)}
    
    def reorder_tasks(self, task_ids: List[int]) -> Tuple[bool, Dict[str, Any]]:
        """Reorder tasks"""
        try:
            # Use HTTP API call instead of direct DB access
            response_data = self.api_client.reorder_tasks(task_ids)

            return True, {
                "task_ids": task_ids,
                "message": f"Reordered {len(task_ids)} tasks"
            }
        except Exception as e:
            logger.error(f"Failed to reorder tasks: {str(e)}")
            return False, {"error": str(e)}
    
    def fetch_tasks(self, status: Optional[Union[str, List[str]]] = None,
                   completed_at_gte: Optional[str] = None,
                   completed_at_lt: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Fetch tasks with optional status and completion date filtering

        Args:
            status: Single status string, list of statuses, or None for all tasks
                   Valid statuses: 'open', 'in_progress', 'done'
            completed_at_gte: ISO date string (YYYY-MM-DD) to filter tasks completed since this date
            completed_at_lt: ISO date string (YYYY-MM-DD) to filter tasks completed before this date
        """
        try:
            # Use HTTP API call instead of direct DB access
            response_data = self.api_client.get_tasks(status, completed_at_gte, completed_at_lt)

            # Extract tasks from the response format
            ui_tasks = response_data.get('tasks', {})
            all_tasks = []
            all_tasks.extend(ui_tasks.get('open', []))
            all_tasks.extend(ui_tasks.get('in_progress', []))
            all_tasks.extend(ui_tasks.get('done', []))

            return True, {
                "tasks": all_tasks,
                "count": len(all_tasks),
                "message": f"Fetched {len(all_tasks)} tasks"
            }
        except Exception as e:
            logger.error(f"Failed to fetch tasks: {str(e)}")
            return False, {"error": str(e)}
    
    def update_task(self, task_id: int, title: Optional[str] = None,
                   description: Optional[str] = None, project: Optional[str] = None,
                   categories: Optional[List[str]] = None, completed_at: Optional[str] = None,
                   started_at: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Update task properties including completion and start dates

        Args:
            task_id: ID of the task to update
            title: New task title (optional)
            description: New task description (optional)
            project: New project name (optional)
            categories: New categories list (optional)
            completed_at: ISO timestamp for completion date (optional)
            started_at: ISO timestamp for start date (optional)
        """
        try:
            # Use HTTP API call - now supports updating completion/start dates directly
            response_data = self.api_client.update_task(
                task_id, title, description, project, categories, completed_at, started_at
            )

            return True, {
                "task_id": task_id,
                "task": response_data.get('task', {}),
                "message": f"Updated task {task_id}"
            }
        except Exception as e:
            logger.error(f"Failed to update task: {str(e)}")
            return False, {"error": str(e)}
    
    def no_op(self) -> Tuple[bool, Dict[str, Any]]:
        """No operation - does nothing"""
        return True, {"message": "No operation performed"}
    
    def execute_action(self, action_name: str, args: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Execute an action by name with arguments"""
        try:
            if action_name == "create_task":
                return self.create_task(
                    title=args.get("title", ""),
                    description=args.get("description", ""),
                    project=args.get("project"),
                    categories=args.get("categories", [])
                )
            elif action_name == "update_task_status":
                return self.update_task_status(
                    task_id=args.get("task_id"),
                    status=args.get("status")
                )
            elif action_name == "reorder_tasks":
                return self.reorder_tasks(
                    task_ids=args.get("task_ids", [])
                )
            elif action_name == "fetch_tasks":
                return self.fetch_tasks(
                    status=args.get("status"),
                    completed_at_gte=args.get("completed_at_gte"),
                    completed_at_lt=args.get("completed_at_lt")
                )
            elif action_name == "update_task":
                return self.update_task(
                    task_id=args.get("task_id"),
                    title=args.get("title"),
                    description=args.get("description"),
                    project=args.get("project"),
                    categories=args.get("categories"),
                    completed_at=args.get("completed_at"),
                    started_at=args.get("started_at")
                )
            elif action_name == "no_op":
                return self.no_op()
            else:
                return False, {"error": f"Unknown action: {action_name}"}
        except Exception as e:
            logger.error(f"Failed to execute action {action_name}: {str(e)}")
            return False, {"error": str(e)}
