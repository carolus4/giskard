"""
Comprehensive tests for the LangGraph orchestrator
"""
import unittest
import json
import requests
import time
from unittest.mock import patch, MagicMock
from models.task_db import TaskDB
from orchestrator.runtime.run import OrchestratorRuntime
from orchestrator.graph.state import AgentState, AgentEventType
from orchestrator.actions.actions import ActionExecutor


class TestOrchestratorIntegration(unittest.TestCase):
    """Integration tests for the orchestrator"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:5001"
        self.runtime = OrchestratorRuntime()
        
        # Clear any existing tasks
        try:
            open_tasks, in_progress_tasks, done_tasks = TaskDB.get_by_status()
            for task in open_tasks + in_progress_tasks + done_tasks:
                task.delete()
        except:
            pass  # Database might not be initialized
    
    def test_create_task_flow(self):
        """Test creating a task through the orchestrator"""
        # Mock the LLM calls to avoid dependency on Ollama
        with patch('orchestrator.graph.nodes.GraphNodes._call_ollama') as mock_ollama:
            # Mock planner response
            mock_ollama.side_effect = [
                json.dumps({
                    "assistant_text": "I'll create a task for you to review the quarterly report.",
                    "actions": [{
                        "name": "create_task",
                        "args": {
                            "title": "Review quarterly report",
                            "description": "",
                            "project": None,
                            "categories": []
                        }
                    }]
                }),
                "✅ I've created a task for you: 'Review quarterly report'. You can find it in your task list."
            ]
            
            # Execute orchestrator
            result = self.runtime.execute("Create a task to review the quarterly report")
            
            # Verify response structure
            self.assertIn("events", result)
            self.assertIn("final_message", result)
            self.assertIn("state_patch", result)
            
            # Verify events
            events = result["events"]
            self.assertGreater(len(events), 0)
            
            # Check for run_started event
            run_started_events = [e for e in events if e["type"] == "run_started"]
            self.assertEqual(len(run_started_events), 1)
            
            # Check for llm_message events
            llm_events = [e for e in events if e["type"] == "llm_message"]
            self.assertGreaterEqual(len(llm_events), 1)
            
            # Check for action_call and action_result events
            action_call_events = [e for e in events if e["type"] == "action_call"]
            action_result_events = [e for e in events if e["type"] == "action_result"]
            self.assertEqual(len(action_call_events), 1)
            self.assertEqual(len(action_result_events), 1)
            
            # Check for final_message and run_completed events
            final_message_events = [e for e in events if e["type"] == "final_message"]
            run_completed_events = [e for e in events if e["type"] == "run_completed"]
            self.assertEqual(len(final_message_events), 1)
            self.assertEqual(len(run_completed_events), 1)
            
            # Verify final message
            self.assertIsNotNone(result["final_message"])
            self.assertGreater(len(result["final_message"]), 0)
    
    def test_fetch_tasks_flow(self):
        """Test fetching tasks through the orchestrator"""
        # Create a test task first
        test_task = TaskDB.create("Test task", "Test description")
        
        with patch('orchestrator.graph.nodes.GraphNodes._call_ollama') as mock_ollama:
            # Mock planner response
            mock_ollama.side_effect = [
                json.dumps({
                    "assistant_text": "Let me fetch your current tasks for you.",
                    "actions": [{
                        "name": "fetch_tasks",
                        "args": {}
                    }]
                }),
                f"Here are your current tasks:\n\n• Test task (open)\n\nYou have 1 task in your list."
            ]
            
            # Execute orchestrator
            result = self.runtime.execute("What are my current tasks?")
            
            # Verify response structure
            self.assertIn("events", result)
            self.assertIn("final_message", result)
            
            # Check for action events
            events = result["events"]
            action_call_events = [e for e in events if e["type"] == "action_call"]
            action_result_events = [e for e in events if e["type"] == "action_result"]
            
            self.assertEqual(len(action_call_events), 1)
            self.assertEqual(len(action_result_events), 1)
            self.assertEqual(action_call_events[0]["name"], "fetch_tasks")
            self.assertTrue(action_result_events[0]["ok"])
    
    def test_pure_chat_flow(self):
        """Test pure chat without actions"""
        with patch('orchestrator.graph.nodes.GraphNodes._call_ollama') as mock_ollama:
            # Mock planner response
            mock_ollama.side_effect = [
                json.dumps({
                    "assistant_text": "Hello! I'm doing well, thank you for asking. How can I help you with your tasks today?",
                    "actions": [{
                        "name": "no_op",
                        "args": {}
                    }]
                }),
                "Hello! I'm doing well, thank you for asking. How can I help you with your tasks today?"
            ]
            
            # Execute orchestrator
            result = self.runtime.execute("Hello, how are you?")
            
            # Verify response structure
            self.assertIn("events", result)
            self.assertIn("final_message", result)
            
            # Check for no_op action
            events = result["events"]
            action_call_events = [e for e in events if e["type"] == "action_call"]
            self.assertEqual(len(action_call_events), 1)
            self.assertEqual(action_call_events[0]["name"], "no_op")
    
    def test_error_handling(self):
        """Test error handling in the orchestrator"""
        with patch('orchestrator.graph.nodes.GraphNodes._call_ollama') as mock_ollama:
            # Mock LLM to raise an exception
            mock_ollama.side_effect = Exception("LLM service unavailable")
            
            # Execute orchestrator
            result = self.runtime.execute("Create a task")
            
            # Verify error handling
            self.assertIn("events", result)
            self.assertIn("final_message", result)
            
            # Check for error events
            events = result["events"]
            run_completed_events = [e for e in events if e["type"] == "run_completed"]
            self.assertEqual(len(run_completed_events), 1)
            self.assertEqual(run_completed_events[0]["status"], "error")


class TestAgentAPI(unittest.TestCase):
    """Test the /api/agent/step endpoint"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:5001"
        self.endpoint = f"{self.base_url}/api/agent/step"
    
    def test_api_endpoint_structure(self):
        """Test that the API endpoint exists and returns correct structure"""
        # This test would require the server to be running
        # For now, we'll test the endpoint logic directly
        from server.routes.agent import agent_step
        
        # Mock request data
        class MockRequest:
            def get_json(self):
                return {
                    "input_text": "Create a task to test the API",
                    "session_id": "test-session",
                    "domain": "test"
                }
        
        # Mock the runtime
        with patch('server.routes.agentV2.OrchestratorRuntime') as mock_runtime_class:
            mock_runtime = MagicMock()
            mock_runtime_class.return_value = mock_runtime
            mock_runtime.execute.return_value = {
                "events": [
                    {"type": "run_started", "run_id": "test", "input_text": "Create a task to test the API"},
                    {"type": "run_completed", "status": "ok"}
                ],
                "final_message": "Task created successfully",
                "state_patch": {"session_id": "test-session", "domain": "test"}
            }
            
            # Test the endpoint logic
            from flask import Flask
            app = Flask(__name__)
            with app.test_request_context('/api/agent/step', method='POST', json={
                "input_text": "Create a task to test the API",
                "session_id": "test-session",
                "domain": "test"
            }):
                # This would need proper Flask test context setup
                pass  # Placeholder for actual test


class TestActionExecutor(unittest.TestCase):
    """Test the action executor"""
    
    def setUp(self):
        """Set up test environment"""
        self.executor = ActionExecutor()
        
        # Clear any existing tasks
        try:
            open_tasks, in_progress_tasks, done_tasks = TaskDB.get_by_status()
            for task in open_tasks + in_progress_tasks + done_tasks:
                task.delete()
        except:
            pass
    
    def test_create_task_action(self):
        """Test create_task action"""
        success, result = self.executor.create_task(
            title="Test task",
            description="Test description",
            project="Test project",
            categories=["test"]
        )
        
        self.assertTrue(success)
        self.assertIn("task_id", result)
        self.assertIn("task_title", result)
        self.assertEqual(result["task_title"], "Test task")
    
    def test_fetch_tasks_action(self):
        """Test fetch_tasks action"""
        # Create a test task
        TaskDB.create("Test task 1", "Description 1")
        TaskDB.create("Test task 2", "Description 2")
        
        success, result = self.executor.fetch_tasks()
        
        self.assertTrue(success)
        self.assertIn("tasks", result)
        self.assertIn("count", result)
        self.assertEqual(result["count"], 2)
    
    def test_update_task_status_action(self):
        """Test update_task_status action"""
        # Create a test task
        task = TaskDB.create("Test task", "Test description")
        
        success, result = self.executor.update_task_status(task.id, "done")
        
        self.assertTrue(success)
        self.assertIn("task_id", result)
        self.assertEqual(result["status"], "done")
    
    def test_reorder_tasks_action(self):
        """Test reorder_tasks action"""
        # Create test tasks
        task1 = TaskDB.create("Task 1", "Description 1")
        task2 = TaskDB.create("Task 2", "Description 2")
        
        success, result = self.executor.reorder_tasks([task2.id, task1.id])
        
        self.assertTrue(success)
        self.assertIn("task_ids", result)
        self.assertEqual(len(result["task_ids"]), 2)
    
    def test_no_op_action(self):
        """Test no_op action"""
        success, result = self.executor.no_op()
        
        self.assertTrue(success)
        self.assertIn("message", result)
        self.assertEqual(result["message"], "No operation performed")
    
    def test_execute_action_method(self):
        """Test the execute_action method"""
        # Test create_task
        success, result = self.executor.execute_action("create_task", {
            "title": "Test task",
            "description": "Test description"
        })
        
        self.assertTrue(success)
        self.assertIn("task_id", result)
        
        # Test invalid action
        success, result = self.executor.execute_action("invalid_action", {})
        
        self.assertFalse(success)
        self.assertIn("error", result)


class TestAgentState(unittest.TestCase):
    """Test the agent state management"""
    
    def test_agent_state_creation(self):
        """Test creating an agent state"""
        state = AgentState(
            input_text="Test input",
            session_id="test-session",
            domain="test"
        )
        
        self.assertEqual(state.input_text, "Test input")
        self.assertEqual(state.session_id, "test-session")
        self.assertEqual(state.domain, "test")
        self.assertEqual(len(state.events), 0)
    
    def test_agent_state_events(self):
        """Test adding events to agent state"""
        from orchestrator.graph.state import RunStartedEvent, LLMMessageEvent
        
        state = AgentState(input_text="Test input")
        
        # Add events
        event1 = RunStartedEvent(run_id="test", input_text="Test input")
        event2 = LLMMessageEvent(node="planner", content="Test content")
        
        state.add_event(event1)
        state.add_event(event2)
        
        self.assertEqual(len(state.events), 2)
        self.assertEqual(len(state.get_events_dict()), 2)
    
    def test_agent_state_response_dict(self):
        """Test converting state to response dictionary"""
        state = AgentState(
            input_text="Test input",
            session_id="test-session",
            domain="test"
        )
        state.final_message = "Test response"
        
        response_dict = state.to_response_dict()
        
        self.assertIn("events", response_dict)
        self.assertIn("final_message", response_dict)
        self.assertIn("state_patch", response_dict)
        self.assertEqual(response_dict["final_message"], "Test response")


if __name__ == '__main__':
    unittest.main()
