"""
HTTP client utility for making API calls from agent/orchestrator services
"""
import json
import logging
import requests
from typing import Dict, Any, List, Optional, Union
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class APIClient:
    """HTTP client for making API calls to the Giskard backend"""

    def __init__(self, base_url: str = "http://localhost:5001"):
        """
        Initialize the API client

        Args:
            base_url: Base URL for the API (e.g., "http://localhost:5001")
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Giskard-API-Client/1.0'
        })

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make an HTTP request to the API

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/api/tasks")
            **kwargs: Additional request parameters

        Returns:
            Response object

        Raises:
            requests.RequestException: If the request fails
        """
        url = urljoin(self.base_url, endpoint)

        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {url} - {str(e)}")
            raise

    def get_tasks(self, status: Optional[Union[str, List[str]]] = None,
                  completed_at_gte: Optional[str] = None,
                  completed_at_lt: Optional[str] = None,
                  completed_at_period: Optional[str] = None) -> Dict[str, Any]:
        """
        Get tasks with optional filtering

        Args:
            status: Filter by status (single status or list of statuses)
            completed_at_gte: Filter tasks completed on or after this date (ISO format)
            completed_at_lt: Filter tasks completed before this date (ISO format)
            completed_at_period: Filter by completion period (this_week, this_month, etc.)

        Returns:
            API response data
        """
        params = {}

        if status:
            if isinstance(status, list):
                params['status'] = ','.join(status)
            else:
                params['status'] = status

        if completed_at_gte:
            params['completed_at_gte'] = completed_at_gte

        if completed_at_lt:
            params['completed_at_lt'] = completed_at_lt

        if completed_at_period:
            params['completed_at_period'] = completed_at_period

        response = self._make_request('GET', '/api/tasks', params=params)
        return response.json()

    def get_task(self, task_id: int) -> Dict[str, Any]:
        """
        Get a specific task by ID

        Args:
            task_id: Task ID

        Returns:
            Task data
        """
        response = self._make_request('GET', f'/api/tasks/{task_id}')
        return response.json()

    def create_task(self, title: str, description: str = "",
                   project: Optional[str] = None,
                   categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new task

        Args:
            title: Task title
            description: Task description
            project: Project name
            categories: List of categories

        Returns:
            Created task data
        """
        data = {
            'title': title,
            'description': description
        }

        if project is not None:
            data['project'] = project

        if categories is not None:
            data['categories'] = categories

        response = self._make_request('POST', '/api/tasks', json=data)
        return response.json()

    def update_task(self, task_id: int, title: Optional[str] = None,
                   description: Optional[str] = None,
                   project: Optional[str] = None,
                   categories: Optional[List[str]] = None,
                   completed_at: Optional[str] = None,
                   started_at: Optional[str] = None) -> Dict[str, Any]:
        """
        Update a task

        Args:
            task_id: Task ID
            title: New title
            description: New description
            project: New project
            categories: New categories
            completed_at: ISO timestamp for completion date
            started_at: ISO timestamp for start date

        Returns:
            Updated task data
        """
        data = {}

        if title is not None:
            data['title'] = title

        if description is not None:
            data['description'] = description

        if project is not None:
            data['project'] = project

        if categories is not None:
            data['categories'] = categories

        if completed_at is not None:
            data['completed_at'] = completed_at

        if started_at is not None:
            data['started_at'] = started_at

        response = self._make_request('PUT', f'/api/tasks/{task_id}', json=data)
        return response.json()

    def update_task_status(self, task_id: int, status: str) -> Dict[str, Any]:
        """
        Update task status

        Args:
            task_id: Task ID
            status: New status (open, in_progress, done)

        Returns:
            Updated task data
        """
        data = {'status': status}

        response = self._make_request('PUT', f'/api/tasks/{task_id}/status', json=data)
        return response.json()

    def delete_task(self, task_id: int) -> Dict[str, Any]:
        """
        Delete a task

        Args:
            task_id: Task ID

        Returns:
            Deletion confirmation
        """
        response = self._make_request('DELETE', f'/api/tasks/{task_id}')
        return response.json()

    def reorder_tasks(self, task_ids: List[int]) -> Dict[str, Any]:
        """
        Reorder tasks

        Args:
            task_ids: List of task IDs in the desired order

        Returns:
            Reorder confirmation
        """
        data = {'task_ids': task_ids}

        response = self._make_request('POST', '/api/tasks/reorder', json=data)
        return response.json()

    def health_check(self) -> bool:
        """
        Check if the API is available

        Returns:
            True if API is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
