"""
Agent routes for the LangGraph orchestrator
"""
from flask import Blueprint, request, jsonify
import logging
from orchestrator.runtime.run import OrchestratorRuntime

logger = logging.getLogger(__name__)

# Create Blueprint
agent = Blueprint('agent', __name__, url_prefix='/api/agent')


class APIResponse:
    """Helper class for consistent API responses"""
    
    @staticmethod
    def success(message: str = "Success", data: dict = None) -> dict:
        response = {"success": True, "message": message}
        if data is not None:
            response.update(data)
        return response
    
    @staticmethod
    def error(message: str, status_code: int = 400) -> tuple:
        return jsonify({"error": message}), status_code


@agent.route('/step', methods=['POST'])
def agent_step():
    """Handle agent orchestration step with LangGraph-style flow"""
    try:
        data = request.get_json()
        input_text = data.get('input_text', '').strip()
        session_id = data.get('session_id')
        domain = data.get('domain')
        
        if not input_text:
            return APIResponse.error('input_text is required')
        
        # Create orchestrator runtime
        runtime = OrchestratorRuntime()
        
        # Execute the orchestrator
        result = runtime.execute(input_text, session_id, domain)
        
        # Log the request and response for observability
        logger.info(f"Agent step processed: input_text='{input_text[:50]}...', events_count={len(result.get('events', []))}")
        
        return jsonify(APIResponse.success('Agent step completed', result))
    
    except Exception as e:
        logger.error(f"Agent step failed: {str(e)}")
        return APIResponse.error(f"Agent step failed: {str(e)}", 500)
