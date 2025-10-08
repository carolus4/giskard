"""
Tool registry using LangChain Tool abstraction
"""
import logging
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool
from orchestrator.actions.actions import ActionExecutor

logger = logging.getLogger(__name__)


# Pydantic models for tool arguments
class CreateTaskArgs(BaseModel):
    title: str = Field(description="The task title")
    description: str = Field(default="", description="Task description")
    project: Optional[str] = Field(default=None, description="Project name")
    categories: Optional[List[str]] = Field(default=None, description="Task categories")


class UpdateTaskStatusArgs(BaseModel):
    task_id: int = Field(description="The task ID to update")
    status: str = Field(description="New status (open, in_progress, done)")


class UpdateTaskArgs(BaseModel):
    task_id: int = Field(description="The task ID to update")
    title: Optional[str] = Field(default=None, description="New task title")
    description: Optional[str] = Field(default=None, description="New task description")
    project: Optional[str] = Field(default=None, description="New project name")
    categories: Optional[List[str]] = Field(default=None, description="New categories list")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp for completion date")
    started_at: Optional[str] = Field(default=None, description="ISO timestamp for start date")


class ReorderTasksArgs(BaseModel):
    task_ids: List[int] = Field(description="List of task IDs in desired order")


class FetchTasksArgs(BaseModel):
    status: Optional[str] = Field(default=None, description="Filter by status (open, in_progress, done)")
    completed_at_gte: Optional[str] = Field(default=None, description="ISO date to filter tasks completed since this date")
    completed_at_lt: Optional[str] = Field(default=None, description="ISO date to filter tasks completed before this date")


class ToolRegistry:
    """Registry for LangChain tools that wrap existing actions"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.action_executor = ActionExecutor(base_url)
        self._tools = self._create_tools()
    
    def _create_tools(self) -> List[StructuredTool]:
        """Create LangChain StructuredTool objects for each action"""
        return [
            StructuredTool.from_function(
                name="create_task",
                description="Create a new task with title, description, project, and categories",
                func=self._create_task_wrapper,
            ),
            StructuredTool.from_function(
                name="update_task_status",
                description="Change task status to open, in_progress, or done",
                func=self._update_task_status_wrapper,
            ),
            StructuredTool.from_function(
                name="update_task",
                description="Update task properties including title, description, project, categories, and dates",
                func=self._update_task_wrapper,
            ),
            StructuredTool.from_function(
                name="reorder_tasks",
                description="Reorder tasks by providing a list of task IDs in the desired order",
                func=self._reorder_tasks_wrapper,
            ),
            StructuredTool.from_function(
                name="fetch_tasks",
                description= """
Get tasks with optional filtering

Args:
    status: Filter by status ("open", "in_progress", "done")
    completed_at_gte: Filter tasks completed on or after this date (ISO format)
    completed_at_lt: Filter tasks completed before this date (ISO format)
                """,
                func=self._fetch_tasks_wrapper,
            ),
            StructuredTool.from_function(
                name="no_op",
                description="No operation - does nothing (for pure chat)",
                func=self._no_op_wrapper,
            )
        ]
    
    def get_tools(self) -> List[StructuredTool]:
        """Get all registered tools"""
        return self._tools
    
    def get_tool_by_name(self, name: str) -> Optional[StructuredTool]:
        """Get a specific tool by name"""
        for tool in self._tools:
            if tool.name == name:
                return tool
        return None
    
    def get_tool_descriptions(self) -> str:
        """Get formatted descriptions of all tools for the LLM"""
        descriptions = []
        for tool in self._tools:
            descriptions.append(f"- {tool.name}: {tool.description}")
        return "\n".join(descriptions)
    
    # Tool wrapper methods
    def _create_task_wrapper(self, title: str, description: str = "", project: str = None, categories: List[str] = None) -> str:
        """Wrapper for create_task action"""
        success, result = self.action_executor.create_task(
            title, description, project, categories
        )
        if success:
            return f"✅ {result.get('message', 'Task created successfully')}"
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}"
    
    def _update_task_status_wrapper(self, task_id: int, status: str) -> str:
        """Wrapper for update_task_status action"""
        success, result = self.action_executor.update_task_status(task_id, status)
        if success:
            return f"✅ {result.get('message', 'Task status updated successfully')}"
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}"
    
    def _update_task_wrapper(self, task_id: int, title: str = None, description: str = None, project: str = None, categories: List[str] = None, completed_at: str = None, started_at: str = None) -> str:
        """Wrapper for update_task action"""
        success, result = self.action_executor.update_task(
            task_id, title, description, project, 
            categories, completed_at, started_at
        )
        if success:
            return f"✅ {result.get('message', 'Task updated successfully')}"
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}"
    
    def _reorder_tasks_wrapper(self, task_ids: List[int]) -> str:
        """Wrapper for reorder_tasks action"""
        success, result = self.action_executor.reorder_tasks(task_ids)
        if success:
            return f"✅ {result.get('message', 'Tasks reordered successfully')}"
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}"
    
    def _fetch_tasks_wrapper(self, status: str = None, completed_at_gte: str = None, completed_at_lt: str = None) -> str:
        """Wrapper for fetch_tasks action"""
        success, result = self.action_executor.fetch_tasks(
            status, completed_at_gte, completed_at_lt
        )
        if success:
            tasks = result.get('tasks', [])
            if not tasks:
                return "📝 No tasks found matching your criteria."
            
            # Format tasks for display
            task_list = []
            for task in tasks:
                status_emoji = {"open": "📋", "in_progress": "🔄", "done": "✅"}.get(task.get('status', 'open'), "📋")
                task_list.append(f"{status_emoji} [{task.get('id')}] {task.get('title', 'Untitled')}")
            
            return f"📋 Found {len(tasks)} tasks:\n" + "\n".join(task_list)
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}"
    
    def _no_op_wrapper(self) -> str:
        """Wrapper for no_op action"""
        success, result = self.action_executor.no_op()
        if success:
            return "💬 Chat response - no action needed"
        else:
            return f"❌ Error: {result.get('error', 'Unknown error')}"
