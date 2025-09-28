"""
Action wrappers for existing services
"""
import requests
import logging
from typing import Dict, Any, Optional, Tuple, List
from models.task_db import TaskDB

logger = logging.getLogger(__name__)


class ActionExecutor:
    """Executes actions by calling existing services"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
    
    def create_task(self, title: str, description: str = "", project: Optional[str] = None, 
                   categories: Optional[List[str]] = None) -> Tuple[bool, Dict[str, Any]]:
        """Create a new task"""
        try:
            # Use direct TaskDB.create instead of HTTP call for efficiency
            task = TaskDB.create(title, description, project, categories or [])
            
            # Enqueue for classification
            from app import classification_manager
            classification_manager.enqueue_classification(task)
            
            return True, {
                "task_id": task.id,
                "task_title": task.title,
                "message": f"Created task: {task.title}"
            }
        except Exception as e:
            logger.error(f"Failed to create task: {str(e)}")
            return False, {"error": str(e)}
    
    def update_task_status(self, task_id: int, status: str) -> Tuple[bool, Dict[str, Any]]:
        """Update task status"""
        try:
            task = TaskDB.get_by_id(task_id)
            if not task:
                return False, {"error": "Task not found"}
            
            # Update status using appropriate method
            if status == 'done':
                task.mark_done()
            elif status == 'in_progress':
                task.mark_in_progress()
            elif status == 'open':
                task.mark_open()
            else:
                return False, {"error": "Invalid status"}
            
            return True, {
                "task_id": task.id,
                "status": status,
                "message": f"Updated task {task.id} status to {status}"
            }
        except Exception as e:
            logger.error(f"Failed to update task status: {str(e)}")
            return False, {"error": str(e)}
    
    def reorder_tasks(self, task_ids: List[int]) -> Tuple[bool, Dict[str, Any]]:
        """Reorder tasks"""
        try:
            success = TaskDB.reorder_tasks(task_ids)
            if success:
                return True, {
                    "task_ids": task_ids,
                    "message": f"Reordered {len(task_ids)} tasks"
                }
            else:
                return False, {"error": "Failed to reorder tasks"}
        except Exception as e:
            logger.error(f"Failed to reorder tasks: {str(e)}")
            return False, {"error": str(e)}
    
    def fetch_tasks(self, status: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """Fetch tasks"""
        try:
            if status:
                # Filter by status
                if status == 'open':
                    tasks, _, _ = TaskDB.get_by_status()
                elif status == 'in_progress':
                    _, tasks, _ = TaskDB.get_by_status()
                elif status == 'done':
                    _, _, tasks = TaskDB.get_by_status()
                else:
                    return False, {"error": "Invalid status filter"}
            else:
                # Get all tasks
                open_tasks, in_progress_tasks, done_tasks = TaskDB.get_by_status()
                tasks = open_tasks + in_progress_tasks + done_tasks
            
            return True, {
                "tasks": [task.to_dict() for task in tasks],
                "count": len(tasks),
                "message": f"Fetched {len(tasks)} tasks"
            }
        except Exception as e:
            logger.error(f"Failed to fetch tasks: {str(e)}")
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
                    status=args.get("status")
                )
            elif action_name == "no_op":
                return self.no_op()
            else:
                return False, {"error": f"Unknown action: {action_name}"}
        except Exception as e:
            logger.error(f"Failed to execute action {action_name}: {str(e)}")
            return False, {"error": str(e)}
