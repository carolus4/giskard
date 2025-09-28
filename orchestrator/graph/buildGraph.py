"""
Build the LangGraph-style orchestrator graph
"""
from typing import Dict, Any
from .state import AgentState
from .nodes import GraphNodes


class OrchestratorGraph:
    """LangGraph-style orchestrator with 4 nodes"""
    
    def __init__(self):
        self.nodes = GraphNodes()
    
    def run(self, input_text: str, session_id: str = None, domain: str = None) -> Dict[str, Any]:
        """
        Run the orchestrator graph with the given input
        
        Args:
            input_text: User input text
            session_id: Optional session ID
            domain: Optional domain context
            
        Returns:
            Dictionary with events, final_message, and state_patch
        """
        # Initialize state
        state = AgentState(
            input_text=input_text,
            session_id=session_id,
            domain=domain
        )
        
        try:
            # Execute the 4 nodes in sequence
            state = self.nodes.ingest_user_input(state)
            state = self.nodes.planner_llm(state)
            state = self.nodes.action_exec(state)
            state = self.nodes.synthesizer_llm(state)
            
            # Return response
            return state.to_response_dict()
            
        except Exception as e:
            # Handle any errors in the graph execution
            from .state import RunCompletedEvent, AgentEventType
            error_event = RunCompletedEvent(type=AgentEventType.RUN_COMPLETED, status="error", error=str(e))
            state.add_event(error_event)
            
            # Set fallback final message
            if not state.final_message:
                state.final_message = "I'm sorry, I encountered an error processing your request. Please try again."
            
            return state.to_response_dict()
