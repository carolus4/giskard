"""
Agent orchestration service for handling chat UI task operations
"""
import json
import logging
import requests
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from models.task_db import TaskDB
from config.ollama_config import get_chat_config, REQUEST_TIMEOUT
from .agent_metrics import agent_metrics, RequestTimer

logger = logging.getLogger(__name__)

class AgentService:
    """Service for orchestrating agent operations with Ollama and Task API"""
    
    def __init__(self):
        self.config = get_chat_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        # In-memory session storage for undo functionality (stateless per request)
        self._session_undo_tokens = {}
        
    def process_step(self, messages: List[Dict[str, Any]], ui_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a single agent step with chat messages and UI context
        
        Args:
            messages: List of chat messages (last N messages)
            ui_context: Lightweight UI context (current tasks, etc.)
            
        Returns:
            Result block with assistant text, side-effects, and undo token
        """
        with RequestTimer(agent_metrics) as timer:
            try:
                # Generate undo token for this session
                undo_token = str(uuid.uuid4())
                
                # Build the agent prompt with tool schema
                prompt = self._build_agent_prompt(messages, ui_context or {})
                
                # Call Ollama with tool schema
                llm_response = self._call_ollama_with_tools(prompt)
                
                # Parse and validate tool calls
                tool_calls = self._parse_tool_calls(llm_response)
                
                # Execute validated tool calls
                side_effects = []
                create_task_count = 0
                for tool_call in tool_calls:
                    if tool_call['name'] == 'create_task':
                        result = self._execute_create_task(tool_call['arguments'], undo_token)
                        side_effects.append(result)
                        create_task_count += 1
                
                # Record metrics
                response_time = time.time() - timer.start_time if timer.start_time else 0
                agent_metrics.record_request(
                    success=True,
                    response_time=response_time,
                    tool_calls=len(tool_calls),
                    create_task_calls=create_task_count
                )
                
                # Generate assistant response text
                assistant_text = self._generate_assistant_response(llm_response, tool_calls, side_effects)
                
                return {
                    'assistant_text': assistant_text,
                    'side_effects': side_effects,
                    'undo_token': undo_token,
                    'success': True
                }
                
            except Exception as e:
                logger.error(f"Agent step failed: {str(e)}")
                response_time = time.time() - timer.start_time if timer.start_time else 0
                agent_metrics.record_request(
                    success=False,
                    response_time=response_time,
                    error_type=type(e).__name__
                )
                return {
                    'assistant_text': f"I encountered an error: {str(e)}",
                    'side_effects': [],
                    'undo_token': None,
                    'success': False,
                    'error': str(e)
                }
    
    def undo_last_mutation(self, undo_token: str) -> Dict[str, Any]:
        """
        Undo the last mutation using the provided undo token
        
        Args:
            undo_token: Token from the last successful mutation
            
        Returns:
            Result of the undo operation
        """
        try:
            # For MVP, we'll implement a simple in-memory undo
            # In a production system, this would be more sophisticated
            if undo_token in self._session_undo_tokens:
                undo_data = self._session_undo_tokens[undo_token]
                
                if undo_data['action'] == 'create_task':
                    # Delete the created task
                    task_id = undo_data['task_id']
                    task = TaskDB.get_by_id(task_id)
                    if task:
                        task.delete()
                        del self._session_undo_tokens[undo_token]
                        agent_metrics.record_undo()
                        return {
                            'success': True,
                            'message': f'Undid creation of task: {undo_data.get("title", "Unknown")}',
                            'undone_task_id': task_id
                        }
                
                return {
                    'success': False,
                    'message': 'Undo operation not supported for this action'
                }
            else:
                return {
                    'success': False,
                    'message': 'Invalid undo token or token expired'
                }
                
        except Exception as e:
            logger.error(f"Undo operation failed: {str(e)}")
            return {
                'success': False,
                'message': f'Undo failed: {str(e)}'
            }
    
    def _build_agent_prompt(self, messages: List[Dict[str, Any]], ui_context: Dict[str, Any]) -> str:
        """Build the agent prompt with tool schema"""
        
        # Get the coaching system prompt
        from config.prompt_registry import prompt_registry
        coaching_prompt = prompt_registry.get_latest_prompt("coaching_system")
        
        if coaching_prompt:
            system_prompt = coaching_prompt.content
        else:
            system_prompt = """You are a helpful productivity coach. You help users organize their tasks, set priorities, and stay motivated. Be encouraging, practical, and focused on productivity."""
        
        # Add tool schema
        tool_schema = """
You have access to the following tools:

1. create_task: Create a new task
   - title (string, required): The task title
   - description (string, optional): Task description
   - project (string, optional): Project name
   - categories (array of strings, optional): Task categories

When you want to create a task, respond with:
TOOL_CALL: create_task
ARGUMENTS: {"title": "Task title", "description": "Optional description", "project": "Optional project", "categories": ["category1", "category2"]}

Current UI Context:
"""
        
        # Add UI context
        if ui_context:
            context_str = json.dumps(ui_context, indent=2)
        else:
            context_str = "No current context available"
        
        # Build conversation history
        conversation_context = ""
        if messages:
            for msg in messages[-6:]:  # Keep last 6 messages
                role = "User" if msg.get('type') == 'user' else "Assistant"
                content = msg.get('content', '')
                conversation_context += f"{role}: {content}\n"
        
        # Combine everything
        full_prompt = f"""{system_prompt}

{tool_schema}
{context_str}

Previous conversation:
{conversation_context}

User: {messages[-1]['content'] if messages else 'Hello'}
Assistant:"""
        
        return full_prompt
    
    def _call_ollama_with_tools(self, prompt: str) -> str:
        """Call Ollama with the agent prompt"""
        try:
            payload = {
                "model": self.config["model"],
                "prompt": prompt,
                "stream": self.config["stream"],
                "options": self.config["options"]
            }
            
            logger.info(f"🤖 Sending agent request to Ollama with model: {self.config['model']}")
            
            response = requests.post(
                self.ollama_url, 
                json=payload, 
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except requests.exceptions.Timeout:
            logger.error("⏰ Agent request timed out")
            raise Exception("Request timed out")
            
        except requests.exceptions.ConnectionError:
            logger.error("🔌 Failed to connect to Ollama")
            raise Exception("Failed to connect to Ollama")
            
        except Exception as e:
            logger.error(f"❌ Agent request failed: {str(e)}")
            raise Exception(f"Agent request failed: {str(e)}")
    
    def _parse_tool_calls(self, llm_response: str) -> List[Dict[str, Any]]:
        """Parse tool calls from LLM response"""
        tool_calls = []
        
        # Look for TOOL_CALL patterns in the response
        lines = llm_response.split('\n')
        current_tool = None
        current_args = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('TOOL_CALL:'):
                # Save previous tool if exists
                if current_tool and current_args:
                    try:
                        args = json.loads(current_args)
                        tool_calls.append({
                            'name': current_tool,
                            'arguments': args
                        })
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in tool arguments: {current_args}")
                
                # Start new tool
                current_tool = line.replace('TOOL_CALL:', '').strip()
                current_args = None
                
            elif line.startswith('ARGUMENTS:'):
                current_args = line.replace('ARGUMENTS:', '').strip()
        
        # Add the last tool if exists
        if current_tool and current_args:
            try:
                args = json.loads(current_args)
                tool_calls.append({
                    'name': current_tool,
                    'arguments': args
                })
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON in tool arguments: {current_args}")
        
        return tool_calls
    
    def _execute_create_task(self, arguments: Dict[str, Any], undo_token: str) -> Dict[str, Any]:
        """Execute create_task tool with validation and idempotency"""
        try:
            # Validate required fields
            title = arguments.get('title', '').strip()
            if not title:
                return {
                    'success': False,
                    'error': 'Task title is required',
                    'action': 'create_task'
                }
            
            # Check for idempotency (same task not re-added in session)
            # For MVP, we'll do a simple title-based check
            existing_tasks = TaskDB.get_all()
            for task in existing_tasks:
                if task.title.lower() == title.lower() and task.status != 'done':
                    return {
                        'success': False,
                        'error': f'Task "{title}" already exists',
                        'action': 'create_task',
                        'existing_task_id': task.id
                    }
            
            # Create the task
            description = arguments.get('description', '').strip()
            project = arguments.get('project')
            categories = arguments.get('categories', [])
            
            task = TaskDB.create(title, description, project, categories)
            
            # Store undo information
            self._session_undo_tokens[undo_token] = {
                'action': 'create_task',
                'task_id': task.id,
                'title': title,
                'timestamp': datetime.now().isoformat()
            }
            
            # Enqueue for classification
            from app import classification_manager
            classification_manager.enqueue_classification(task)
            
            return {
                'success': True,
                'action': 'create_task',
                'task_id': task.id,
                'task_title': title,
                'message': f'Created task: {title}'
            }
            
        except Exception as e:
            logger.error(f"Create task execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'action': 'create_task'
            }
    
    def _generate_assistant_response(self, llm_response: str, tool_calls: List[Dict[str, Any]], side_effects: List[Dict[str, Any]]) -> str:
        """Generate the final assistant response text"""
        
        # If there were tool calls, create a response based on the results
        if tool_calls and side_effects:
            responses = []
            for i, side_effect in enumerate(side_effects):
                if side_effect.get('success'):
                    if side_effect.get('action') == 'create_task':
                        responses.append(f"✅ {side_effect.get('message', 'Task created successfully')}")
                else:
                    responses.append(f"❌ {side_effect.get('error', 'Action failed')}")
            
            return '\n'.join(responses)
        
        # If no tool calls, return the LLM response (cleaned up)
        # Remove tool call markers from the response
        cleaned_response = llm_response
        lines = cleaned_response.split('\n')
        filtered_lines = []
        
        for line in lines:
            line = line.strip()
            if not (line.startswith('TOOL_CALL:') or line.startswith('ARGUMENTS:')):
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines).strip()
    
    def is_ollama_available(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
