"""
LangGraph-based agent API endpoints
"""
from flask import Blueprint, request, jsonify
import logging
import time
import json
from datetime import datetime
from orchestrator.langgraph_orchestrator import LangGraphOrchestrator
from models.task_db import AgentStepDB
from models.session_db import SessionDB, TraceDB
from database import get_connection
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)

# Create blueprint
agent = Blueprint('agent', __name__)


def convert_conversation_context_to_messages(conversation_context):
    """Convert conversation context from frontend to LangChain messages"""
    messages = []
    for msg in conversation_context:
        if msg.get('type') == 'user':
            messages.append(HumanMessage(content=msg.get('content', '')))
        elif msg.get('type') == 'bot':
            messages.append(AIMessage(content=msg.get('content', '')))
    return messages

# Initialize orchestrator
orchestrator = LangGraphOrchestrator()


class APIResponse:
    """Standardized API response format"""
    
    @staticmethod
    def success(message: str, data: dict = None) -> tuple:
        response = {"success": True, "message": message}
        if data:
            response.update(data)
        return jsonify(response), 200
    
    @staticmethod
    def error(message: str, status_code: int = 400) -> tuple:
        return jsonify({"error": message}), status_code


@agent.route('/step', methods=['POST'])
def agent_step():
    """Handle agent orchestration step with LangGraph"""
    try:
        data = request.get_json()
        input_text = data.get('input_text', '').strip()
        session_id = data.get('session_id')
        domain = data.get('domain')
        
        if not input_text:
            return APIResponse.error('input_text is required')
        
        # Execute the LangGraph orchestrator
        result = orchestrator.run(input_text, session_id, domain)
        
        # Log the request and response for observability
        logger.info(f"LangGraph agent step processed: input_text='{input_text[:50]}...', success={result.get('success')}")
        
        return APIResponse.success('LangGraph agent step completed', result)
    
    except Exception as e:
        logger.error(f"LangGraph agent step failed: {str(e)}")
        return APIResponse.error(f"LangGraph agent step failed: {str(e)}", 500)


@agent.route('/graph/visualize', methods=['GET'])
def visualize_graph():
    """Return graph structure for visualization"""
    try:
        # Get the graph structure
        graph_info = {
            "nodes": [
                {"id": "planner_llm", "label": "Planner LLM", "type": "llm"},
                {"id": "action_exec", "label": "Action Execution", "type": "action"},
                {"id": "synthesizer_llm", "label": "Synthesizer LLM", "type": "llm"}
            ],
            "edges": [
                {"from": "planner_llm", "to": "action_exec"},
                {"from": "action_exec", "to": "synthesizer_llm"},
                {"from": "synthesizer_llm", "to": "END"}
            ],
            "description": "LangGraph-based agent workflow with 3 sequential nodes"
        }
        
        return APIResponse.success('Graph structure retrieved', graph_info)
    
    except Exception as e:
        logger.error(f"Graph visualization failed: {str(e)}")
        return APIResponse.error(f"Graph visualization failed: {str(e)}", 500)


@agent.route('/sessions', methods=['GET'])
def get_sessions():
    """Get all conversation sessions"""
    try:
        # Get all sessions
        sessions = SessionDB.get_all()
        
        # Convert to API format
        sessions_data = []
        for session in sessions:
            # Get trace count for this session
            traces = TraceDB.get_by_session_id(session.id)
            sessions_data.append({
                "session_id": session.id,
                "user_id": session.user_id,
                "created_at": session.created_at,
                "updated_at": session.updated_at,
                "trace_count": len(traces),
                "metadata": session.metadata
            })

        return APIResponse.success('Sessions retrieved', {"sessions": sessions_data})

    except Exception as e:
        logger.error(f"Failed to retrieve sessions: {str(e)}")
        return APIResponse.error(f"Failed to retrieve sessions: {str(e)}", 500)


@agent.route('/sessions/<session_id>', methods=['GET'])
def get_session_traces(session_id):
    """Get all traces for a specific session"""
    try:
        # Get session
        session = SessionDB.get_by_id(session_id)
        if not session:
            return APIResponse.error('Session not found', 404)
        
        # Get all traces for this session
        traces = TraceDB.get_by_session_id(session_id)
        
        # Convert to API format
        traces_data = []
        for trace in traces:
            traces_data.append({
                'trace_id': trace.id,
                'user_message': trace.user_message,
                'assistant_response': trace.assistant_response,
                'created_at': trace.created_at,
                'completed_at': trace.completed_at,
                'status': trace.status,
                'metadata': trace.metadata
            })
        
        return APIResponse.success('Session traces retrieved', {
            'session_id': session_id,
            'traces': traces_data,
            'total_traces': len(traces_data)
        })
        
    except Exception as e:
        logger.error(f"Failed to retrieve session traces: {str(e)}")
        return APIResponse.error(f"Failed to retrieve session traces: {str(e)}", 500)


@agent.route('/conversation-test', methods=['POST'])
def conversation_test():
    """Test endpoint to isolate the issue"""
    try:
        data = request.get_json()
        input_text = data.get('input_text', '').strip()
        logger.info(f"Test endpoint received: {input_text}")
        
        if not input_text:
            return APIResponse.error('input_text is required')
        
        # Simple response without orchestrator
        return APIResponse.success('Test successful', {
            'message': f'Received: {input_text}',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Test endpoint error: {str(e)}")
        return APIResponse.error(f"Test endpoint error: {str(e)}", 500)

@agent.route('/conversation', methods=['POST'])
def conversation_stream():
    """Handle step-by-step conversation with real-time updates"""
    try:
        data = request.get_json()
        input_text = data.get('input_text', '').strip()
        session_id = data.get('session_id')
        domain = data.get('domain', 'chat')
        conversation_context = data.get('conversation_context', [])
        trace_id = data.get('trace_id')

        # Debug logging
        logger.info(f"Received conversation request: input_text='{input_text}', session_id='{session_id}', domain='{domain}'")

        if not input_text:
            logger.error("Missing input_text in request")
            return APIResponse.error('input_text is required')

        # Handle session management
        logger.info("Starting session management")
        if not session_id:
            # Create new session
            logger.info("Creating new session")
            session = SessionDB.create(user_id=None, metadata={"domain": domain})
            session_id = session.id
            logger.info(f"Created new session: {session_id}")
        else:
            # Get existing session
            logger.info(f"Getting existing session: {session_id}")
            session = SessionDB.get_by_id(session_id)
            if not session:
                # If session not found, check if it's a frontend-generated session ID
                # Frontend generates IDs like "session-1759943624203-1pjd5m9my"
                if session_id.startswith('session-'):
                    logger.info(f"Frontend session ID not found, creating new session: {session_id}")
                    session = SessionDB.create(user_id=None, metadata={"domain": domain})
                    session_id = session.id
                    logger.info(f"Created new session: {session_id}")
                else:
                    logger.error(f"Session not found: {session_id}")
                    return APIResponse.error('Invalid session_id')
            else:
                # Update session timestamp
                session.save()
                logger.info(f"Updated existing session: {session_id}")

        # Generate trace_id if not provided (Langfuse requires 32 lowercase hex chars)
        logger.info("Generating trace_id")
        if not trace_id:
            import hashlib
            trace_id = hashlib.md5(f"trace-{int(time.time())}".encode()).hexdigest()
        logger.info(f"Using trace_id: {trace_id}")

        # Create trace for this conversation
        logger.info("Creating trace")
        trace = TraceDB.create(
            session_id=session_id,
            user_message=input_text,
            metadata={"domain": domain, "conversation_context": conversation_context}
        )
        logger.info(f"Created trace: {trace.id}")

        # Create Langfuse trace context for the entire conversation
        from config.langfuse_config import langfuse_config
        langfuse_trace_context = langfuse_config.create_trace_context(
            name="chat.turn",
            trace_id=trace_id,
            user_id=session_id,
            input_data={"input_text": input_text, "session_id": session_id, "domain": domain}
        )

        # Get the orchestrator to run step by step
        logger.info("Getting orchestrator for step-by-step execution")
        steps_data = []

        # Create initial state
        initial_state = {
            'messages': [],
            'input_text': input_text,
            'session_id': session_id,
            'domain': domain,
            'trace_id': trace_id,
            'current_step': AgentStepDB.get_next_step_number(trace_id),
            'planner_output': None,
            'actions_to_execute': [],
            'action_results': [],
            'final_message': None
        }

        # Step 1: Planner LLM (thinking/planning phase)
        initial_state['current_step'] += 1

        # Load planner prompt using new prompt management system
        from config.prompt_manager import get_prompt, get_compiled_prompt
        
        # Get the prompt (tries Langfuse first, falls back to local)
        prompt_data = get_prompt("planner", label="production")
        langfuse_prompt = prompt_data.get("langfuse_prompt")  # Get the actual Langfuse prompt object
        
        # Compile the prompt with template variables
        # Get tool descriptions for the planner
        from orchestrator.tools.tool_registry import ToolRegistry
        tool_registry = ToolRegistry("http://localhost:5001")
        tool_descriptions = tool_registry.get_tool_descriptions()
        
        compiled_prompt = get_compiled_prompt(
            "planner", 
            label="production",
            tool_descriptions=tool_descriptions
        )

        # Create messages for LLM with conversation context
        system_msg = SystemMessage(content=compiled_prompt)
        user_msg = HumanMessage(content=input_text)
        
        # Include conversation context if available
        context_messages = convert_conversation_context_to_messages(conversation_context)
        messages = [system_msg] + context_messages + [user_msg]

        # Call LLM for planning with Langfuse tracing
        from config.langfuse_config import langfuse_config
        if not langfuse_config.enabled:
            # Handle case where Langfuse is not configured
            logger.warning("Langfuse not configured, skipping tracing")
            client = None
        else:
            client = langfuse_config.client
        
        # Create root span for the entire chat turn
        root_span = None
        if client and langfuse_trace_context:
            try:
                root_span = client.start_span(
                    trace_context=langfuse_trace_context,
                    name="chat.turn",
                    input={"input_text": input_text, "session_id": session_id, "domain": domain}
                )
            except Exception as e:
                logger.warning(f"Failed to create Langfuse root span: {e}")
                root_span = None

        # Create planner span with proper prompt integration
        planner_span = None
        planner_generation = None
        if client and root_span:
            try:
                planner_span = client.start_span(
                    trace_context=langfuse_trace_context,
                    name="plan",
                    input={"input_text": input_text, "messages_count": len(messages)}
                )
                
                # Create planner generation with prompt reference
                planner_generation = planner_span.start_observation(
                    name="planner.llm",
                    as_type="generation",
                    input={"messages": [{"type": msg.__class__.__name__, "content": msg.content} for msg in messages]},
                    prompt=langfuse_prompt  # Pass the actual Langfuse prompt object
                )
            except Exception as e:
                logger.warning(f"Failed to create Langfuse planner span: {e}")
                planner_span = None
                planner_generation = None
        
        # Call LLM for planning
        logger.info("Calling LLM for planning")
        response = orchestrator.llm.invoke(messages)
        logger.info("LLM planning response received")
        
        # Update generation with output
        if planner_generation:
            try:
                planner_generation.update(output=response)
            except Exception as e:
                logger.warning(f"Failed to update Langfuse planner generation: {e}")
        if planner_generation:
            try:
                planner_generation.end()
            except Exception as e:
                logger.warning(f"Failed to end Langfuse planner generation: {e}")
        if planner_span:
            try:
                planner_span.end()
            except Exception as e:
                logger.warning(f"Failed to end Langfuse planner span: {e}")

        # Parse response
        try:
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            planner_output = json.loads(cleaned_response)
            initial_state['planner_output'] = planner_output
            initial_state['actions_to_execute'] = planner_output.get("actions", [])

        except json.JSONDecodeError:
            planner_output = {
                "assistant_text": "I'm sorry, I had trouble understanding your request.",
                "actions": [{"name": "no_op", "args": {}}]
            }
            initial_state['actions_to_execute'] = [{"name": "no_op", "args": {}}]

        # Log planner step
        AgentStepDB.create(
            session_id=session_id,
            trace_id=trace_id,
            step_number=initial_state['current_step'],
            step_type='planner_llm',
            input_data={'input_text': input_text, 'messages_count': len(messages), 'conversation_context_length': len(conversation_context)},
            output_data={'llm_response': response, 'planner_output': planner_output, 'actions_to_execute': initial_state['actions_to_execute']},
            rendered_prompt=compiled_prompt,
            llm_input={'messages': [{'type': msg.__class__.__name__, 'content': msg.content} for msg in messages]},
            llm_model='gemma3:4b',
            llm_output=response
        )

        # Get the assistant text for display
        assistant_text = planner_output.get('assistant_text', '')
        display_content = assistant_text if assistant_text else f"🤔 Planning actions based on: '{input_text}'"
        
        steps_data.append({
            'step_number': initial_state['current_step'],
            'step_type': 'planner_llm',
            'status': 'completed',
            'content': display_content,
            'details': {
                'assistant_text': assistant_text,
                'actions_count': len(initial_state['actions_to_execute'])
            },
            'timestamp': datetime.now().isoformat()
        })

        # Step 2: Execute actions
        if initial_state['actions_to_execute']:
            initial_state['current_step'] += 1

            action_results = []
            for action in initial_state['actions_to_execute']:
                action_name = action.get("name", "no_op")
                action_args = action.get("args", {})

                # Create individual tool execution span for each action
                tool_span = None
                if client and root_span:
                    try:
                        tool_span = client.start_span(
                            trace_context=langfuse_trace_context,
                            name=f"tool.execute.{action_name}",
                            input={"tool_name": action_name, "tool_args": action_args}
                        )
                        
                        # Add tool request event
                        tool_span.create_event(
                            name="tool.request",
                            input={"tool_name": action_name, "tool_args": action_args}
                        )
                    except Exception as e:
                        logger.warning(f"Failed to create Langfuse tool span for {action_name}: {e}")
                        tool_span = None

                # Execute the action
                success, result = orchestrator.action_executor.execute_action(action_name, action_args)

                # Add tool response event and end span
                if tool_span:
                    try:
                        tool_span.create_event(
                            name="tool.response",
                            input={"success": success, "result": result if success else None, "error": result.get("error") if not success else None}
                        )
                        tool_span.update(output={"success": success, "result": result if success else None})
                        tool_span.end()
                    except Exception as e:
                        logger.warning(f"Failed to update Langfuse tool span for {action_name}: {e}")

                action_results.append({
                    "name": action_name,
                    "ok": success,
                    "result": result if success else None,
                    "error": result.get("error") if not success else None
                })

            initial_state['action_results'] = action_results

            # Log action execution
            AgentStepDB.create(
                session_id=session_id,
                trace_id=trace_id,
                step_number=initial_state['current_step'],
                step_type='action_exec',
                input_data={'actions_to_execute': initial_state['actions_to_execute']},
                output_data={'action_results': action_results, 'actions_executed': len(action_results)}
            )

            steps_data.append({
                'step_number': initial_state['current_step'],
                'step_type': 'action_exec',
                'status': 'completed',
                'content': f"⚡ Executed {len(action_results)} actions",
                'details': {
                    'successful_actions': len([r for r in action_results if r["ok"]]),
                    'failed_actions': len([r for r in action_results if not r["ok"]])
                },
                'timestamp': datetime.now().isoformat()
            })

        # Step 3: Synthesize final response
        initial_state['current_step'] += 1

        # Load synthesizer prompt using new prompt management system
        from config.prompt_manager import get_prompt, get_compiled_prompt
        
        # Get the prompt (tries Langfuse first, falls back to local)
        synthesizer_prompt_data = get_prompt("synthesizer", label="production")
        synthesizer_langfuse_prompt = synthesizer_prompt_data.get("langfuse_prompt")  # Get the actual Langfuse prompt object
        
        # Compile the prompt with template variables
        action_results_str = json.dumps(initial_state['action_results'], indent=2)
        full_prompt = get_compiled_prompt(
            "synthesizer", 
            label="production",
            user_input=input_text,
            action_results=action_results_str
        )

        # Create messages for synthesis with conversation context
        system_msg = SystemMessage(content=full_prompt)
        user_msg = HumanMessage(content=input_text)
        
        # Include conversation context if available
        context_messages = convert_conversation_context_to_messages(conversation_context)
        messages = [system_msg] + context_messages + [user_msg]

        # Call LLM for final response with Langfuse tracing
        synthesizer_span = None
        synthesizer_generation = None
        if client and root_span:
            try:
                synthesizer_span = client.start_span(
                    trace_context=langfuse_trace_context,
                    name="synthesize",
                    input={"action_results": initial_state['action_results'], "input_text": input_text}
                )
                
                synthesizer_generation = synthesizer_span.start_observation(
                    name="synthesizer.llm",
                    as_type="generation",
                    input={"messages": [{"type": msg.__class__.__name__, "content": msg.content} for msg in messages]},
                    prompt=synthesizer_langfuse_prompt  # Pass the actual Langfuse prompt object
                )
            except Exception as e:
                logger.warning(f"Failed to create Langfuse synthesizer span: {e}")
                synthesizer_span = None
                synthesizer_generation = None
        
        # Call LLM for final response
        response = orchestrator.llm.invoke(messages)
        
        # Update generation with output
        if synthesizer_generation:
            try:
                synthesizer_generation.update(output=response)
            except Exception as e:
                logger.warning(f"Failed to update Langfuse synthesizer generation: {e}")
            try:
                synthesizer_generation.end()
            except Exception as e:
                logger.warning(f"Failed to end Langfuse synthesizer generation: {e}")
        if synthesizer_span:
            try:
                synthesizer_span.end()
            except Exception as e:
                logger.warning(f"Failed to end Langfuse synthesizer span: {e}")

        # Add to conversation history
        initial_state['messages'].append(AIMessage(content=response))
        initial_state['final_message'] = response

        # Log synthesizer step
        AgentStepDB.create(
            session_id=session_id,
            trace_id=trace_id,
            step_number=initial_state['current_step'],
            step_type='synthesizer_llm',
            input_data={'action_results': initial_state['action_results'], 'input_text': input_text, 'conversation_context_length': len(conversation_context)},
            output_data={'final_message': response, 'synthesis_success': True},
            rendered_prompt=full_prompt,
            llm_input={'messages': [{'type': msg.__class__.__name__, 'content': msg.content} for msg in messages]},
            llm_model='gemma3:4b',
            llm_output=response
        )

        steps_data.append({
            'step_number': initial_state['current_step'],
            'step_type': 'synthesizer_llm',
            'status': 'completed',
            'content': response,
            'details': {
                'is_final': True
            },
            'timestamp': datetime.now().isoformat()
        })

        # End root span
        if root_span:
            try:
                root_span.update(output={"final_message": response, "total_steps": len(steps_data)})
                root_span.end()
            except Exception as e:
                logger.warning(f"Failed to end Langfuse root span: {e}")

        # Complete the trace
        if langfuse_trace_context and client:
            try:
                client.update_current_trace(output={"final_message": response, "total_steps": len(steps_data)})
            except Exception as e:
                logger.warning(f"Failed to update Langfuse current trace: {e}")

        # Mark trace as completed
        trace.mark_completed(response)

        # Flush Langfuse events
        langfuse_config.flush()

        # Return all steps for the frontend to display progressively
        return APIResponse.success('Conversation completed', {
            'session_id': session_id,
            'trace_id': trace_id,
            'steps': steps_data,
            'final_message': response,
            'total_steps': len(steps_data)
        })

    except Exception as e:
        logger.error(f"Conversation failed: {str(e)}")
        return APIResponse.error(f"Conversation failed: {str(e)}", 500)
