"""
Action wrappers for existing services
"""
import logging
from typing import Dict, Any, Optional, Tuple, List, Union
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
            if status:
                # Get all tasks first
                open_tasks, in_progress_tasks, done_tasks = TaskDB.get_by_status()
                
                # Handle single status
                if isinstance(status, str):
                    if status == 'open':
                        tasks = open_tasks
                    elif status == 'in_progress':
                        tasks = in_progress_tasks
                    elif status == 'done':
                        tasks = done_tasks
                    else:
                        return False, {"error": f"Invalid status filter: {status}. Valid options: open, in_progress, done"}
                
                # Handle multiple statuses
                elif isinstance(status, list):
                    tasks = []
                    for s in status:
                        if s == 'open':
                            tasks.extend(open_tasks)
                        elif s == 'in_progress':
                            tasks.extend(in_progress_tasks)
                        elif s == 'done':
                            tasks.extend(done_tasks)
                        else:
                            return False, {"error": f"Invalid status filter: {s}. Valid options: open, in_progress, done"}
                    
                    # Remove duplicates while preserving order
                    seen = set()
                    unique_tasks = []
                    for task in tasks:
                        if task.id not in seen:
                            seen.add(task.id)
                            unique_tasks.append(task)
                    tasks = unique_tasks
                else:
                    return False, {"error": "Status must be a string, list of strings, or None"}
            else:
                # Get all tasks
                open_tasks, in_progress_tasks, done_tasks = TaskDB.get_by_status()
                tasks = open_tasks + in_progress_tasks + done_tasks
            
            # Apply completed_at filtering if specified
            if completed_at_gte or completed_at_lt:
                from datetime import datetime
                try:
                    # Parse filter dates - ISO timestamp format only
                    filter_gte = None
                    filter_lt = None
                    
                    if completed_at_gte:
                        try:
                            filter_gte = datetime.fromisoformat(completed_at_gte.replace('Z', '+00:00'))
                        except ValueError:
                            return False, {"error": f"Invalid date format: {completed_at_gte}. Use ISO format (e.g., 2025-09-29 or 2025-09-29T00:00:00)"}
                    
                    if completed_at_lt:
                        try:
                            filter_lt = datetime.fromisoformat(completed_at_lt.replace('Z', '+00:00'))
                        except ValueError:
                            return False, {"error": f"Invalid date format: {completed_at_lt}. Use ISO format (e.g., 2025-09-29 or 2025-09-29T00:00:00)"}
                    
                    # Filter tasks
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
                    
                    tasks = filtered_tasks
                    
                except Exception as e:
                    return False, {"error": f"Date filtering error: {str(e)}"}
            
            return True, {
                "tasks": [task.to_dict() for task in tasks],
                "count": len(tasks),
                "message": f"Fetched {len(tasks)} tasks"
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
            task = TaskDB.get_by_id(task_id)
            if not task:
                return False, {"error": "Task not found"}
            
            # Update provided fields
            if title is not None:
                task.title = title
            if description is not None:
                task.description = description
            if project is not None:
                task.project = project
            if categories is not None:
                task.categories = categories
            
            # Handle date updates with validation
            if completed_at is not None:
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
                        return False, {"error": f"Invalid completed_at format: {completed_at}. Use ISO format (e.g., 2025-01-15T14:30:00)"}
            
            if started_at is not None:
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
                        return False, {"error": f"Invalid started_at format: {started_at}. Use ISO format (e.g., 2025-01-15T14:30:00)"}
            
            # Save the updated task
            task.save()
            
            return True, {
                "task_id": task.id,
                "task": task.to_dict(),
                "message": f"Updated task {task.id}"
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
