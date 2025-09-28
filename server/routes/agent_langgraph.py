"""
LangGraph-based agent API endpoints
"""
from flask import Blueprint, request, jsonify
import logging
from orchestrator.langgraph_orchestrator import LangGraphOrchestrator

logger = logging.getLogger(__name__)

# Create blueprint
agent_langgraph = Blueprint('agent_langgraph', __name__)

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
                {"id": "ingest_user_input", "label": "Ingest User Input", "type": "input"},
                {"id": "planner_llm", "label": "Planner LLM", "type": "llm"},
                {"id": "action_exec", "label": "Action Execution", "type": "action"},
                {"id": "synthesizer_llm", "label": "Synthesizer LLM", "type": "llm"}
            ],
            "edges": [
                {"from": "ingest_user_input", "to": "planner_llm"},
                {"from": "planner_llm", "to": "action_exec"},
                {"from": "action_exec", "to": "synthesizer_llm"},
                {"from": "synthesizer_llm", "to": "END"}
            ],
            "description": "LangGraph-based agent workflow with 4 sequential nodes"
        }
        
        return APIResponse.success('Graph structure retrieved', graph_info)
    
    except Exception as e:
        logger.error(f"Graph visualization failed: {str(e)}")
        return APIResponse.error(f"Graph visualization failed: {str(e)}", 500)
