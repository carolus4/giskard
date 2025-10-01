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
from utils.http_client import APIClient
from config.ollama_config import get_chat_config, REQUEST_TIMEOUT
from .agent_metrics import agent_metrics, RequestTimer

logger = logging.getLogger(__name__)

class AgentService:
    """Service for orchestrating agent operations with Ollama and Task API"""

    def __init__(self, api_base_url: str = "http://localhost:5001"):
        self.config = get_chat_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.api_client = APIClient(api_base_url)
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
                
                # Log the user request and prompt
                self._log_agent_interaction(messages, prompt, None, None, None, "prompt_sent")
                
                # Call Ollama with tool schema
                llm_response = self._call_ollama_with_tools(prompt)
                
                # Parse and validate tool calls
                tool_calls = self._parse_tool_calls(llm_response)
                
                # Log the LLM response and parsed tool calls
                self._log_agent_interaction(messages, prompt, llm_response, tool_calls, None, "llm_response")
                
                # Execute validated tool calls
                side_effects = []
                create_task_count = 0
                tool_call_details = []  # NEW: Track tool call details for UI
                
                for tool_call in tool_calls:
                    tool_name = tool_call['name']
                    arguments = tool_call['arguments']
                    
                    # Add tool call detail for UI display
                    tool_call_details.append({
                        'tool_name': tool_name,
                        'arguments': arguments,
                        'status': 'executing'
                    })
                    
                    if tool_name == 'create_task':
                        result = self._execute_create_task(arguments, undo_token)
                        side_effects.append(result)
                        create_task_count += 1
                    elif tool_name == 'get_tasks':
                        result = self._execute_get_tasks(arguments)
                        side_effects.append(result)
                    elif tool_name == 'update_task':
                        result = self._execute_update_task(arguments, undo_token)
                        side_effects.append(result)
                    elif tool_name == 'delete_task':
                        result = self._execute_delete_task(arguments, undo_token)
                        side_effects.append(result)
                    elif tool_name == 'update_task_status':
                        result = self._execute_update_task_status(arguments, undo_token)
                        side_effects.append(result)
                    else:
                        result = {
                            'success': False,
                            'error': f'Unknown tool: {tool_name}',
                            'action': tool_name
                        }
                        side_effects.append(result)
                    
                    # Update tool call detail with result
                    tool_call_details[-1]['result'] = result
                    tool_call_details[-1]['status'] = 'completed' if result.get('success') else 'failed'
                
                # Record metrics
                response_time = time.time() - timer.start_time if timer.start_time else 0
                agent_metrics.record_request(
                    success=True,
                    response_time=response_time,
                    tool_calls=len(tool_calls),
                    create_task_calls=create_task_count
                )
                
                # Generate assistant response text
                if tool_calls and side_effects:
                    # Send tool results back to LLM for intelligent analysis while preserving conversational context
                    assistant_text = self._generate_intelligent_response_with_context(llm_response, tool_calls, side_effects, messages)
                else:
                    # No tool calls, just filter the response
                    assistant_text = self._generate_assistant_response(llm_response, tool_calls, side_effects, messages)
                
                # Log the final response
                self._log_agent_interaction(messages, prompt, llm_response, tool_calls, side_effects, "final_response", assistant_text)
                
                return {
                    'assistant_text': assistant_text,
                    'side_effects': side_effects,
                    'tool_calls': tool_call_details,  # NEW: Include tool call details
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
                    'tool_calls': [],  # NEW: Empty tool calls on error
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
                action = undo_data['action']
                
                if action == 'create_task':
                    # Delete the created task via API
                    task_id = undo_data['task_id']
                    try:
                        self.api_client.delete_task(task_id)
                        del self._session_undo_tokens[undo_token]
                        agent_metrics.record_undo()
                        return {
                            'success': True,
                            'message': f'Undid creation of task: {undo_data.get("title", "Unknown")}',
                            'undone_task_id': task_id
                        }
                    except Exception as e:
                        return {
                            'success': False,
                            'message': f'Failed to undo task creation: {str(e)}'
                        }
                
                elif action == 'update_task':
                    # Restore original values via API
                    task_id = undo_data['task_id']
                    original_values = undo_data['original_values']
                    try:
                        self.api_client.update_task(
                            task_id,
                            title=original_values['title'],
                            description=original_values['description'],
                            project=original_values['project'],
                            categories=original_values['categories']
                        )
                        del self._session_undo_tokens[undo_token]
                        agent_metrics.record_undo()
                        return {
                            'success': True,
                            'message': f'Undid update of task: {original_values["title"]}',
                            'undone_task_id': task_id
                        }
                    except Exception as e:
                        return {
                            'success': False,
                            'message': f'Failed to undo task update: {str(e)}'
                        }
                
                elif action == 'delete_task':
                    # Recreate the deleted task via API
                    task_data = undo_data['task_data']
                    try:
                        response_data = self.api_client.create_task(
                            title=task_data['title'],
                            description=task_data['description'],
                            project=task_data['project'],
                            categories=task_data['categories']
                        )
                        restored_task = response_data.get('task', {})
                        restored_task_id = restored_task.get('id')

                        del self._session_undo_tokens[undo_token]
                        agent_metrics.record_undo()
                        return {
                            'success': True,
                            'message': f'Undid deletion of task: {task_data["title"]}',
                            'restored_task_id': restored_task_id
                        }
                    except Exception as e:
                        return {
                            'success': False,
                            'message': f'Failed to undo task deletion: {str(e)}'
                        }
                
                elif action == 'update_task_status':
                    # Restore original status via API
                    task_id = undo_data['task_id']
                    original_status = undo_data['original_status']
                    try:
                        self.api_client.update_task_status(task_id, original_status)
                        del self._session_undo_tokens[undo_token]
                        agent_metrics.record_undo()
                        return {
                            'success': True,
                            'message': f'Undid status change of task to {original_status}',
                            'undone_task_id': task_id
                        }
                    except Exception as e:
                        return {
                            'success': False,
                            'message': f'Failed to undo status change: {str(e)}'
                        }
                
                return {
                    'success': False,
                    'message': f'Undo operation not supported for action: {action}'
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
        from config.prompts import get_coaching_prompt
        task_context = ui_context.get("task_context", "")
        system_prompt = get_coaching_prompt(task_context)
        
        # Add tool schema
        tool_schema = """
You have access to the following tools:

1. create_task: Create a new task
   - title (string, required): The task title
   - description (string, optional): Task description
   - project (string, optional): Project name
   - categories (array of strings, optional): Task categories

2. get_tasks: Get all tasks (useful for checking current tasks)
   - status (string, optional): Filter by status (open, in_progress, done)

3. update_task: Update an existing task
   - task_id (integer, required): The task ID to update
   - title (string, optional): New task title
   - description (string, optional): New task description
   - project (string, optional): New project name
   - categories (array of strings, optional): New task categories
   - completed_at (string, optional): ISO 8601 timestamp for completion date (cannot be future, cannot be before created_at)

4. delete_task: Delete a task
   - task_id (integer, required): The task ID to delete

5. update_task_status: Change task status
   - task_id (integer, required): The task ID to update
   - status (string, required): New status (open, in_progress, done)

Examples:
TOOL_CALL: create_task
ARGUMENTS: {"title": "Task title", "description": "Optional description", "project": "Optional project", "categories": ["category1", "category2"]}

TOOL_CALL: get_tasks
ARGUMENTS: {"status": "open"}

TOOL_CALL: update_task
ARGUMENTS: {"task_id": 123, "title": "Updated title", "description": "Updated description", "completed_at": "2025-01-15T14:30:00"}

TOOL_CALL: delete_task
ARGUMENTS: {"task_id": 123}

TOOL_CALL: update_task_status
ARGUMENTS: {"task_id": 123, "status": "done"}

Current UI Context:
"""
        
        # Add UI context (limit size to prevent timeouts)
        if ui_context:
            # Limit context to prevent massive prompts
            limited_context = {}
            if 'tasks' in ui_context:
                # Only include task summaries, not full task data
                tasks = ui_context['tasks']
                if isinstance(tasks, dict):
                    limited_context['task_counts'] = {
                        'open': len(tasks.get('open', [])),
                        'in_progress': len(tasks.get('in_progress', [])),
                        'done': len(tasks.get('done', []))
                    }
                else:
                    limited_context['task_count'] = len(tasks) if tasks else 0
            
            # Include other lightweight context
            for key in ['current_date', 'user_preferences']:
                if key in ui_context:
                    limited_context[key] = ui_context[key]
            
            context_str = json.dumps(limited_context, indent=2)
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
            try:
                response_data = self.api_client.get_tasks()
                existing_tasks = []
                ui_tasks = response_data.get('tasks', {})
                existing_tasks.extend(ui_tasks.get('open', []))
                existing_tasks.extend(ui_tasks.get('in_progress', []))
                # Don't check done tasks for idempotency

                for task in existing_tasks:
                    if task.get('title', '').lower() == title.lower():
                        return {
                            'success': False,
                            'error': f'Task "{title}" already exists',
                            'action': 'create_task',
                            'existing_task_id': task.get('id')
                        }
            except Exception:
                # If we can't fetch tasks, continue with creation (idempotency check failed)
                pass

            # Create the task via API
            description = arguments.get('description', '').strip()
            project = arguments.get('project')
            categories = arguments.get('categories', [])

            response_data = self.api_client.create_task(title, description, project, categories)
            task_data = response_data.get('task', {})
            task_id = task_data.get('id')

            if not task_id:
                return {
                    'success': False,
                    'error': 'Failed to create task - no ID returned',
                    'action': 'create_task'
                }

            # Store undo information
            self._session_undo_tokens[undo_token] = {
                'action': 'create_task',
                'task_id': task_id,
                'title': title,
                'timestamp': datetime.now().isoformat()
            }

            # Enqueue for classification (create temporary TaskDB instance)
            from models.task_db import TaskDB
            task = TaskDB(
                id=task_id,
                title=task_data.get('title', title),
                description=task_data.get('description', description),
                project=task_data.get('project'),
                categories=task_data.get('categories', categories),
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

            return {
                'success': True,
                'action': 'create_task',
                'task_id': task_id,
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
    
    def _generate_assistant_response(self, llm_response: str, tool_calls: List[Dict[str, Any]], side_effects: List[Dict[str, Any]], original_messages: List[Dict[str, Any]] = None) -> str:
        """Generate the final assistant response text with preserved conversational context"""
        
        # Always preserve the original LLM response and just filter out technical tool call lines
        # This ensures the user sees the valuable conversational context and reasoning
        cleaned_response = llm_response
        lines = cleaned_response.split('\n')
        filtered_lines = []
        
        for line in lines:
            stripped_line = line.strip()
            # Only filter out the technical tool call markers
            if not (stripped_line.startswith('TOOL_CALL:') or stripped_line.startswith('ARGUMENTS:')):
                filtered_lines.append(line)  # Preserve original spacing/indentation
        
        return '\n'.join(filtered_lines).strip()
    
    def _generate_intelligent_response_with_context(self, original_llm_response: str, tool_calls: List[Dict[str, Any]], side_effects: List[Dict[str, Any]], original_messages: List[Dict[str, Any]]) -> str:
        """Send tool results back to LLM for intelligent analysis while preserving conversational context"""
        try:
            # Extract the conversational part from the original response
            conversational_response = self._generate_assistant_response(original_llm_response, tool_calls, side_effects, original_messages)
            
            # Build a prompt that includes the original conversational context and tool results
            analysis_prompt = self._build_analysis_prompt_with_context(conversational_response, tool_calls, side_effects, original_messages)
            
            # Call LLM with tool results for intelligent analysis
            llm_analysis_response = self._call_ollama_with_tools(analysis_prompt)
            
            # Clean up the response (remove any tool call markers)
            cleaned_response = llm_analysis_response
            lines = cleaned_response.split('\n')
            filtered_lines = []
            
            for line in lines:
                stripped_line = line.strip()
                if not (stripped_line.startswith('TOOL_CALL:') or stripped_line.startswith('ARGUMENTS:')):
                    filtered_lines.append(line)
            
            return '\n'.join(filtered_lines).strip()
            
        except Exception as e:
            logger.error(f"Intelligent response generation failed: {str(e)}")
            # Fallback to just the conversational response
            return self._generate_assistant_response(original_llm_response, tool_calls, side_effects, original_messages)
    
    def _build_analysis_prompt_with_context(self, conversational_response: str, tool_calls: List[Dict[str, Any]], side_effects: List[Dict[str, Any]], original_messages: List[Dict[str, Any]]) -> str:
        """Build a prompt that includes conversational context and tool results for LLM analysis"""
        
        # Start with the conversational response
        prompt_parts = [
            "You are a helpful productivity coach. You just provided this response to a user:",
            "",
            f'"{conversational_response}"',
            "",
            "You then executed these tools and got these results:",
            ""
        ]
        
        # Add tool execution results
        for i, (tool_call, side_effect) in enumerate(zip(tool_calls, side_effects)):
            prompt_parts.append(f"Tool {i+1}: {tool_call['name']}")
            prompt_parts.append(f"Arguments: {json.dumps(tool_call['arguments'], indent=2)}")
            prompt_parts.append(f"Result: {json.dumps(side_effect, indent=2)}")
            prompt_parts.append("")
        
        prompt_parts.extend([
            "Now provide a natural, helpful response that incorporates the tool results into your original response.",
            "Be conversational and explain what you found or what you did.",
            "Don't just list the raw data - make it useful and engaging for the user.",
            "",
            "Response:"
        ])
        
        return '\n'.join(prompt_parts)
    
    def _execute_get_tasks(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute get_tasks tool"""
        try:
            status_filter = arguments.get('status')

            # Use API client to get tasks
            response_data = self.api_client.get_tasks(status=status_filter)

            return {
                'success': True,
                'action': 'get_tasks',
                'tasks': response_data.get('tasks', {}),
                'message': f'Retrieved tasks{" with status " + status_filter if status_filter else ""}'
            }

        except Exception as e:
            logger.error(f"Get tasks execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'action': 'get_tasks'
            }
    
    def _execute_update_task(self, arguments: Dict[str, Any], undo_token: str) -> Dict[str, Any]:
        """Execute update_task tool with validation and undo support"""
        try:
            task_id = arguments.get('task_id')
            if not task_id:
                return {
                    'success': False,
                    'error': 'Task ID is required',
                    'action': 'update_task'
                }

            # Check if task exists
            try:
                current_task = self.api_client.get_task(task_id)
            except Exception:
                return {
                    'success': False,
                    'error': f'Task {task_id} not found',
                    'action': 'update_task'
                }

            # Store original values for undo
            original_values = {
                'title': current_task.get('title', ''),
                'description': current_task.get('description', ''),
                'project': current_task.get('project'),
                'categories': current_task.get('categories', [])
            }

            # Update fields if provided
            updated_fields = []
            update_data = {}

            if 'title' in arguments:
                title = arguments['title'].strip()
                if title:
                    update_data['title'] = title
                    updated_fields.append('title')
                else:
                    return {
                        'success': False,
                        'error': 'Task title cannot be empty',
                        'action': 'update_task'
                    }

            if 'description' in arguments:
                update_data['description'] = arguments['description'].strip()
                updated_fields.append('description')

            if 'project' in arguments:
                update_data['project'] = arguments['project']
                updated_fields.append('project')

            if 'categories' in arguments:
                update_data['categories'] = arguments['categories']
                updated_fields.append('categories')

            if not updated_fields:
                return {
                    'success': False,
                    'error': 'No fields to update',
                    'action': 'update_task'
                }

            # Update task via API
            response_data = self.api_client.update_task(task_id, **update_data)
            updated_task = response_data.get('task', {})

            # Store undo information
            self._session_undo_tokens[undo_token] = {
                'action': 'update_task',
                'task_id': task_id,
                'original_values': original_values,
                'updated_fields': updated_fields,
                'timestamp': datetime.now().isoformat()
            }

            # Enqueue for re-classification (create temporary TaskDB instance)
            from models.task_db import TaskDB
            task = TaskDB(
                id=task_id,
                title=updated_task.get('title', original_values['title']),
                description=updated_task.get('description', original_values['description']),
                project=updated_task.get('project', original_values['project']),
                categories=updated_task.get('categories', original_values['categories']),
                status=updated_task.get('status', current_task.get('status')),
                sort_key=updated_task.get('sort_key'),
                created_at=updated_task.get('created_at'),
                updated_at=updated_task.get('updated_at'),
                started_at=updated_task.get('started_at'),
                completed_at=updated_task.get('completed_at')
            )

            from app import classification_manager
            classification_manager.enqueue_classification(task)

            return {
                'success': True,
                'action': 'update_task',
                'task_id': task_id,
                'updated_fields': updated_fields,
                'message': f'Updated task: {updated_task.get("title", "Unknown")}'
            }

        except Exception as e:
            logger.error(f"Update task execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'action': 'update_task'
            }
    
    def _execute_delete_task(self, arguments: Dict[str, Any], undo_token: str) -> Dict[str, Any]:
        """Execute delete_task tool with undo support"""
        try:
            task_id = arguments.get('task_id')
            if not task_id:
                return {
                    'success': False,
                    'error': 'Task ID is required',
                    'action': 'delete_task'
                }

            # Get current task data for undo
            try:
                current_task = self.api_client.get_task(task_id)
                task_data = current_task
                task_title = current_task.get('title', 'Unknown')
            except Exception:
                return {
                    'success': False,
                    'error': f'Task {task_id} not found',
                    'action': 'delete_task'
                }

            # Delete task via API
            response_data = self.api_client.delete_task(task_id)

            # Store undo information
            self._session_undo_tokens[undo_token] = {
                'action': 'delete_task',
                'task_data': task_data,
                'timestamp': datetime.now().isoformat()
            }

            return {
                'success': True,
                'action': 'delete_task',
                'task_id': task_id,
                'message': f'Deleted task: {task_title}'
            }

        except Exception as e:
            logger.error(f"Delete task execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'action': 'delete_task'
            }
    
    def _execute_update_task_status(self, arguments: Dict[str, Any], undo_token: str) -> Dict[str, Any]:
        """Execute update_task_status tool with undo support"""
        try:
            task_id = arguments.get('task_id')
            new_status = arguments.get('status')

            if not task_id:
                return {
                    'success': False,
                    'error': 'Task ID is required',
                    'action': 'update_task_status'
                }

            if not new_status:
                return {
                    'success': False,
                    'error': 'Status is required',
                    'action': 'update_task_status'
                }

            if new_status not in ['open', 'in_progress', 'done']:
                return {
                    'success': False,
                    'error': 'Invalid status. Must be: open, in_progress, or done',
                    'action': 'update_task_status'
                }

            # Get current task data for undo
            try:
                current_task = self.api_client.get_task(task_id)
            except Exception:
                return {
                    'success': False,
                    'error': f'Task {task_id} not found',
                    'action': 'update_task_status'
                }

            # Store original status for undo
            original_status = current_task.get('status')
            original_started_at = current_task.get('started_at')
            original_completed_at = current_task.get('completed_at')

            # Update status via API
            response_data = self.api_client.update_task_status(task_id, new_status)
            updated_task = response_data.get('task', {})

            # Store undo information
            self._session_undo_tokens[undo_token] = {
                'action': 'update_task_status',
                'task_id': task_id,
                'original_status': original_status,
                'original_started_at': original_started_at,
                'original_completed_at': original_completed_at,
                'timestamp': datetime.now().isoformat()
            }

            return {
                'success': True,
                'action': 'update_task_status',
                'task_id': task_id,
                'old_status': original_status,
                'new_status': new_status,
                'message': f'Changed task status from {original_status} to {new_status}: {updated_task.get("title", "Unknown")}'
            }

        except Exception as e:
            logger.error(f"Update task status execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'action': 'update_task_status'
            }

    def _log_agent_interaction(self, messages, prompt, llm_response, tool_calls, side_effects, stage, assistant_text=None):
        """Log agent interactions for debugging (similar to classification_predictions_log.txt)"""
        try:
            from datetime import datetime
            
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "stage": stage,
                "user_message": messages[-1]['content'] if messages else "No message",
                "model": "gemma3:4b"
            }
            
            if stage == "prompt_sent":
                log_entry["prompt_length"] = len(prompt) if prompt else 0
                log_entry["prompt_preview"] = prompt[:200] + "..." if prompt and len(prompt) > 200 else prompt
                
            elif stage == "llm_response":
                log_entry["llm_response"] = llm_response
                log_entry["tool_calls_count"] = len(tool_calls) if tool_calls else 0
                log_entry["tool_calls"] = tool_calls
                
            elif stage == "final_response":
                log_entry["assistant_text"] = assistant_text
                log_entry["side_effects_count"] = len(side_effects) if side_effects else 0
                log_entry["side_effects"] = side_effects
            
            # Write to agent interactions log file
            with open("data/agent_interactions_log.txt", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            logger.error(f"Failed to log agent interaction: {str(e)}")

    def is_ollama_available(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
