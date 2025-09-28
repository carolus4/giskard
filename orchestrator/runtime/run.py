"""
Runtime for executing the orchestrator graph
"""
import logging
from typing import Dict, Any
from ..graph.buildGraph import OrchestratorGraph

logger = logging.getLogger(__name__)


class OrchestratorRuntime:
    """Runtime for executing the orchestrator graph"""
    
    def __init__(self):
        self.graph = OrchestratorGraph()
    
    def execute(self, input_text: str, session_id: str = None, domain: str = None) -> Dict[str, Any]:
        """
        Execute the orchestrator with the given input
        
        Args:
            input_text: User input text
            session_id: Optional session ID
            domain: Optional domain context
            
        Returns:
            Dictionary with events, final_message, and state_patch
        """
        try:
            logger.info(f"Executing orchestrator with input: {input_text[:100]}...")
            
            # Run the graph
            result = self.graph.run(input_text, session_id, domain)
            
            logger.info(f"Orchestrator completed with {len(result.get('events', []))} events")
            return result
            
        except Exception as e:
            logger.error(f"Orchestrator execution failed: {str(e)}")
            # Return error response
            return {
                "events": [
                    {
                        "type": "run_started",
                        "run_id": "error",
                        "input_text": input_text
                    },
                    {
                        "type": "run_completed",
                        "status": "error",
                        "error": str(e)
                    }
                ],
                "final_message": "I'm sorry, I encountered an error processing your request. Please try again.",
                "state_patch": {
                    "session_id": session_id,
                    "domain": domain
                }
            }
