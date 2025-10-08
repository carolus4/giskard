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
from database import get_connection
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

logger = logging.getLogger(__name__)

# Create blueprint
agent_langgraph = Blueprint('agent_langgraph', __name__)


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


@agent_langgraph.route('/step', methods=['POST'])
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


@agent_langgraph.route('/graph/visualize', methods=['GET'])
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


@agent_langgraph.route('/threads', methods=['GET'])
def get_threads():
    """Get all conversation threads"""
    try:
        # Get all unique trace_ids from the database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT DISTINCT trace_id, MIN(timestamp) as first_message, MAX(timestamp) as last_message, COUNT(*) as step_count
                FROM agent_steps
                GROUP BY trace_id
                ORDER BY last_message DESC
            ''')

            rows = cursor.fetchall()
            threads = []
            for row in rows:
                threads.append({
                    "trace_id": row[0],
                    "first_message": row[1],
                    "last_message": row[2],
                    "step_count": row[3]
                })

        return APIResponse.success('Threads retrieved', {"threads": threads})

    except Exception as e:
        logger.error(f"Failed to retrieve threads: {str(e)}")
        return APIResponse.error(f"Failed to retrieve threads: {str(e)}", 500)


@agent_langgraph.route('/threads/<trace_id>', methods=['GET'])
def get_thread_steps(trace_id):
    """Get all steps for a specific trace"""
    try:
        steps = AgentStepDB.get_by_trace_id(trace_id)
        if not steps:
            return APIResponse.error('Trace not found', 404)

        # Convert to dictionaries
        steps_data = [step.to_dict() for step in steps]

        return APIResponse.success('Thread steps retrieved', {"steps": steps_data})

    except Exception as e:
        logger.error(f"Failed to retrieve thread steps: {str(e)}")
        return APIResponse.error(f"Failed to retrieve thread steps: {str(e)}", 500)


@agent_langgraph.route('/steps', methods=['GET'])
def get_all_steps():
    """Get all agent steps (paginated)"""
    try:
        # Get pagination parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))
        offset = (page - 1) * per_page

        # Get total count
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM agent_steps')
            total = cursor.fetchone()[0]

        # Get paginated results
        cursor.execute('''
            SELECT id, trace_id, step_number, step_type, timestamp, input_data,
                   output_data, rendered_prompt, llm_input, llm_output, error
            FROM agent_steps
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        ''', (per_page, offset))

        rows = cursor.fetchall()
        steps = []
        for row in rows:
                steps.append({
                    "id": row[0],
                    "trace_id": row[1],
                "step_number": row[2],
                "step_type": row[3],
                "timestamp": row[4],
                "input_data": row[5] if row[5] else {},
                "output_data": row[6] if row[6] else {},
                "rendered_prompt": row[7],
                "llm_input": row[8] if row[8] else {},
                "llm_output": row[9],
                "error": row[10]
            })

        return APIResponse.success('Steps retrieved', {
            "steps": steps,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page
            }
        })

    except Exception as e:
        logger.error(f"Failed to retrieve steps: {str(e)}")
        return APIResponse.error(f"Failed to retrieve steps: {str(e)}", 500)


@agent_langgraph.route('/conversation', methods=['POST'])
def conversation_stream():
    """Handle step-by-step conversation with real-time updates"""
    try:
        data = request.get_json()
        input_text = data.get('input_text', '').strip()
        session_id = data.get('session_id')
        domain = data.get('domain', 'chat')
        conversation_context = data.get('conversation_context', [])
        trace_id = data.get('trace_id', session_id)

        if not input_text:
            return APIResponse.error('input_text is required')

        # Generate trace_id if not provided
        if not trace_id:
            trace_id = f"chat-{int(time.time())}"

        # Get the orchestrator to run step by step
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

        # Load planner prompt and create LLM input
        from config.prompts import get_planner_prompt
        planner_prompt = get_planner_prompt()

        # Create messages for LLM with conversation context
        system_msg = SystemMessage(content=planner_prompt)
        user_msg = HumanMessage(content=input_text)
        
        # Include conversation context if available
        context_messages = convert_conversation_context_to_messages(conversation_context)
        messages = [system_msg] + context_messages + [user_msg]

        # Call LLM for planning
        response = orchestrator.llm.invoke(messages)

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
            trace_id=trace_id,
            step_number=initial_state['current_step'],
            step_type='planner_llm',
            input_data={'input_text': input_text, 'messages_count': len(messages), 'conversation_context_length': len(conversation_context)},
            output_data={'llm_response': response, 'planner_output': planner_output, 'actions_to_execute': initial_state['actions_to_execute']},
            rendered_prompt=planner_prompt,
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

                success, result = orchestrator.action_executor.execute_action(action_name, action_args)

                action_results.append({
                    "name": action_name,
                    "ok": success,
                    "result": result if success else None,
                    "error": result.get("error") if not success else None
                })

            initial_state['action_results'] = action_results

            # Log action execution
            AgentStepDB.create(
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

        # Load synthesizer prompt
        from config.prompts import get_synthesizer_prompt
        action_results_str = json.dumps(initial_state['action_results'], indent=2)
        full_prompt = get_synthesizer_prompt(input_text, action_results_str)

        # Create messages for synthesis with conversation context
        system_msg = SystemMessage(content=full_prompt)
        user_msg = HumanMessage(content=input_text)
        
        # Include conversation context if available
        context_messages = convert_conversation_context_to_messages(conversation_context)
        messages = [system_msg] + context_messages + [user_msg]

        # Call LLM for final response
        response = orchestrator.llm.invoke(messages)

        # Add to conversation history
        initial_state['messages'].append(AIMessage(content=response))
        initial_state['final_message'] = response

        # Log synthesizer step
        AgentStepDB.create(
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

        # Return all steps for the frontend to display progressively
        return APIResponse.success('Conversation completed', {
            'trace_id': trace_id,
            'steps': steps_data,
            'final_message': response,
            'total_steps': len(steps_data)
        })

    except Exception as e:
        logger.error(f"Conversation failed: {str(e)}")
        return APIResponse.error(f"Conversation failed: {str(e)}", 500)
