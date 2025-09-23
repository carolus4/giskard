"""
Integration tests for the agent orchestration layer
"""
import unittest
import json
import requests
import time
from unittest.mock import patch, MagicMock
from models.task_db import TaskDB
from utils.agent_service import AgentService
from utils.agent_metrics import agent_metrics

class TestAgentIntegration(unittest.TestCase):
    """Integration tests for agent orchestration"""
    
    def setUp(self):
        """Set up test environment"""
        self.agent_service = AgentService()
        agent_metrics.reset_metrics()
    
    def tearDown(self):
        """Clean up after tests"""
        # Clean up any test tasks
        tasks = TaskDB.get_all()
        for task in tasks:
            if 'test' in task.title.lower():
                task.delete()
    
    @patch('utils.agent_service.requests.post')
    def test_agent_step_with_create_task(self, mock_post):
        """Test agent step that creates a task"""
        # Mock Ollama response with tool call
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': '''I'll help you create that task.

TOOL_CALL: create_task
ARGUMENTS: {"title": "Test task", "description": "A test task for integration testing", "project": "Testing", "categories": ["test", "integration"]}'''
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test data
        messages = [
            {'type': 'user', 'content': 'Create a test task for integration testing'}
        ]
        ui_context = {'current_tasks': []}
        
        # Execute agent step
        result = self.agent_service.process_step(messages, ui_context)
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertIn('undo_token', result)
        self.assertIn('side_effects', result)
        self.assertIn('assistant_text', result)
        
        # Verify task was created
        tasks = TaskDB.get_all()
        test_tasks = [t for t in tasks if 'test' in t.title.lower()]
        self.assertEqual(len(test_tasks), 1)
        self.assertEqual(test_tasks[0].title, 'Test task')
        self.assertEqual(test_tasks[0].description, 'A test task for integration testing')
        self.assertEqual(test_tasks[0].project, 'Testing')
        self.assertIn('test', test_tasks[0].categories)
        self.assertIn('integration', test_tasks[0].categories)
    
    @patch('utils.agent_service.requests.post')
    def test_agent_step_idempotency(self, mock_post):
        """Test that creating the same task twice is prevented"""
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': '''I'll create that task.

TOOL_CALL: create_task
ARGUMENTS: {"title": "Duplicate test task", "description": "This should not be created twice"}'''
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        messages = [
            {'type': 'user', 'content': 'Create a duplicate test task'}
        ]
        
        # First creation
        result1 = self.agent_service.process_step(messages, {})
        self.assertTrue(result1['success'])
        
        # Second creation (should be prevented)
        result2 = self.agent_service.process_step(messages, {})
        self.assertTrue(result2['success'])
        
        # Check that only one task was created
        tasks = TaskDB.get_all()
        duplicate_tasks = [t for t in tasks if 'duplicate' in t.title.lower()]
        self.assertEqual(len(duplicate_tasks), 1)
    
    @patch('utils.agent_service.requests.post')
    def test_agent_step_undo_functionality(self, mock_post):
        """Test undo functionality"""
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': '''I'll create that task.

TOOL_CALL: create_task
ARGUMENTS: {"title": "Undo test task", "description": "This task will be undone"}'''
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        messages = [
            {'type': 'user', 'content': 'Create a task that I will undo'}
        ]
        
        # Create task
        result = self.agent_service.process_step(messages, {})
        self.assertTrue(result['success'])
        
        undo_token = result['undo_token']
        task_id = result['side_effects'][0]['task_id']
        
        # Verify task exists
        task = TaskDB.get_by_id(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task.title, 'Undo test task')
        
        # Undo the task
        undo_result = self.agent_service.undo_last_mutation(undo_token)
        self.assertTrue(undo_result['success'])
        
        # Verify task was deleted
        deleted_task = TaskDB.get_by_id(task_id)
        self.assertIsNone(deleted_task)
    
    @patch('utils.agent_service.requests.post')
    def test_agent_step_no_tool_calls(self, mock_post):
        """Test agent step with no tool calls"""
        # Mock Ollama response without tool calls
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': 'I understand you want to discuss your tasks. How can I help you organize them better?'
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        messages = [
            {'type': 'user', 'content': 'Tell me about productivity tips'}
        ]
        
        result = self.agent_service.process_step(messages, {})
        
        # Verify result
        self.assertTrue(result['success'])
        self.assertIn('assistant_text', result)
        self.assertEqual(len(result['side_effects']), 0)
        self.assertIn('productivity', result['assistant_text'].lower())
    
    @patch('utils.agent_service.requests.post')
    def test_agent_step_invalid_tool_call(self, mock_post):
        """Test agent step with invalid tool call"""
        # Mock Ollama response with invalid tool call
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': '''I'll try to create a task.

TOOL_CALL: create_task
ARGUMENTS: {"invalid": "json"}'''
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        messages = [
            {'type': 'user', 'content': 'Create a task with invalid arguments'}
        ]
        
        result = self.agent_service.process_step(messages, {})
        
        # Should still succeed but with no side effects
        self.assertTrue(result['success'])
        self.assertEqual(len(result['side_effects']), 0)
    
    def test_agent_metrics(self):
        """Test agent metrics collection"""
        # Reset metrics
        agent_metrics.reset_metrics()
        
        # Record some test metrics
        agent_metrics.record_request(success=True, response_time=1.5, tool_calls=1, create_task_calls=1)
        agent_metrics.record_request(success=False, response_time=0.8, error_type='ConnectionError')
        agent_metrics.record_undo()
        
        # Get metrics
        metrics = agent_metrics.get_metrics()
        
        # Verify metrics
        self.assertEqual(metrics['requests_total'], 2)
        self.assertEqual(metrics['requests_successful'], 1)
        self.assertEqual(metrics['requests_failed'], 1)
        self.assertEqual(metrics['tool_calls_total'], 1)
        self.assertEqual(metrics['create_task_calls'], 1)
        self.assertEqual(metrics['undo_operations'], 1)
        self.assertIn('ConnectionError', metrics['error_counts'])
    
    def test_agent_service_ollama_availability(self):
        """Test Ollama availability check"""
        # This test will depend on whether Ollama is actually running
        # We'll just test that the method exists and returns a boolean
        result = self.agent_service.is_ollama_available()
        self.assertIsInstance(result, bool)

class TestAgentAPIEndpoints(unittest.TestCase):
    """Test the agent API endpoints"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:5001/api"
        agent_metrics.reset_metrics()
    
    def tearDown(self):
        """Clean up after tests"""
        # Clean up any test tasks
        tasks = TaskDB.get_all()
        for task in tasks:
            if 'test' in task.title.lower():
                task.delete()
    
    @patch('utils.agent_service.requests.post')
    def test_agent_step_endpoint(self, mock_post):
        """Test the /agent/step endpoint"""
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': '''I'll create that task.

TOOL_CALL: create_task
ARGUMENTS: {"title": "API test task", "description": "Created via API test"}'''
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        # Test data
        data = {
            'messages': [
                {'type': 'user', 'content': 'Create an API test task'}
            ],
            'ui_context': {'current_tasks': []}
        }
        
        # Make request (this would require the server to be running)
        # For now, we'll test the service directly
        from utils.agent_service import AgentService
        agent_service = AgentService()
        result = agent_service.process_step(data['messages'], data['ui_context'])
        
        self.assertTrue(result['success'])
        self.assertIn('undo_token', result)
    
    def test_agent_undo_endpoint(self):
        """Test the /agent/undo endpoint"""
        # This would test the actual HTTP endpoint
        # For now, we'll test the service directly
        from utils.agent_service import AgentService
        agent_service = AgentService()
        
        # Test with invalid token
        result = agent_service.undo_last_mutation('invalid-token')
        self.assertFalse(result['success'])
        self.assertIn('Invalid undo token', result['message'])
    
    def test_agent_metrics_endpoint(self):
        """Test the /agent/metrics endpoint"""
        # Test metrics collection
        agent_metrics.record_request(success=True, response_time=1.0, tool_calls=1)
        metrics = agent_metrics.get_metrics()
        
        self.assertIn('requests_total', metrics)
        self.assertIn('requests_successful', metrics)
        self.assertIn('average_response_time', metrics)

if __name__ == '__main__':
    unittest.main()
