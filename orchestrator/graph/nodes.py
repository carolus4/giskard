"""
Graph nodes for the LangGraph orchestrator
"""
import json
import logging
import requests
import uuid
from typing import Dict, Any
from .state import AgentState, RunStartedEvent, LLMMessageEvent, ActionCallEvent, ActionResultEvent, FinalMessageEvent, RunCompletedEvent, AgentEventType
from ..actions.actions import ActionExecutor
from config.ollama_config import get_chat_config

logger = logging.getLogger(__name__)


class GraphNodes:
    """Collection of graph nodes for the orchestrator"""
    
    def __init__(self):
        self.config = get_chat_config()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.action_executor = ActionExecutor()
    
    def ingest_user_input(self, state: AgentState) -> AgentState:
        """Node 1: Ingest user input and emit run_started event"""
        try:
            # Generate run ID
            state.run_id = str(uuid.uuid4())
            
            # Emit run_started event
            run_started_event = RunStartedEvent(
                type=AgentEventType.RUN_STARTED,
                run_id=state.run_id,
                input_text=state.input_text
            )
            state.add_event(run_started_event)
            
            logger.info(f"Run started: {state.run_id}")
            return state
            
        except Exception as e:
            logger.error(f"Error in ingest_user_input: {str(e)}")
            raise
    
    def planner_llm(self, state: AgentState) -> AgentState:
        """Node 2: Use router-based planner to select tool and arguments"""
        try:
            # Import the router planner
            from orchestrator.tools.router import RouterPlanner
            
            # Create router planner instance
            router_planner = RouterPlanner()
            
            # Plan actions using the router
            router_output = router_planner.plan_actions(state.input_text)
            
            # Emit llm_message event
            llm_event = LLMMessageEvent(
                type=AgentEventType.LLM_MESSAGE,
                node="planner",
                content=f"Router selected tool: {router_output.get('tool_name', 'unknown')}"
            )
            state.add_event(llm_event)
            
            # Store router output
            state.planner_output = router_output
            
            # Convert router output to actions format for compatibility
            # The router now returns a single tool call instead of multiple actions
            state.actions_to_execute = [{
                "name": router_output.get("tool_name", "no_op"),
                "args": router_output.get("tool_args", {})
            }]
            
            return state
            
        except Exception as e:
            logger.error(f"Error in planner_llm: {str(e)}")
            # Fallback to no_op on error
            state.planner_output = {
                "assistant_text": "I'm sorry, I encountered an error processing your request.",
                "actions": [{"name": "no_op", "args": {}}]
            }
            state.actions_to_execute = [{"name": "no_op", "args": {}}]
            return state
    
    def action_exec(self, state: AgentState) -> AgentState:
        """Node 3: Execute actions using tool-based approach"""
        try:
            from orchestrator.tools.router import RouterPlanner
            
            # Create router planner instance for tool execution
            router_planner = RouterPlanner()
            
            action_results = []
            
            for action in state.actions_to_execute:
                action_name = action.get("name", "no_op")
                action_args = action.get("args", {})
                
                # Emit action_call event
                action_call_event = ActionCallEvent(
                    type=AgentEventType.ACTION_CALL,
                    name=action_name,
                    args=action_args
                )
                state.add_event(action_call_event)
                
                # Execute the tool using the router planner
                tool_result = router_planner.execute_tool(action_name, action_args)
                
                # Determine success based on result content
                success = not tool_result.startswith("❌")
                
                # Emit action_result event
                action_result_event = ActionResultEvent(
                    type=AgentEventType.ACTION_RESULT,
                    name=action_name,
                    ok=success,
                    result={"message": tool_result} if success else None,
                    error=tool_result if not success else None
                )
                state.add_event(action_result_event)
                
                # Store result
                action_results.append({
                    "name": action_name,
                    "ok": success,
                    "result": {"message": tool_result} if success else None,
                    "error": tool_result if not success else None
                })
            
            state.action_results = action_results
            return state
            
        except Exception as e:
            logger.error(f"Error in action_exec: {str(e)}")
            # Add error result
            state.action_results = [{
                "name": "error",
                "ok": False,
                "result": None,
                "error": str(e)
            }]
            return state
    
    def synthesizer_llm(self, state: AgentState) -> AgentState:
        """Node 4: Synthesize final response"""
        try:
            # Load synthesizer prompt from registry
            from config.prompts import get_synthesizer_prompt
            action_results_str = json.dumps(state.action_results, indent=2)
            full_prompt = get_synthesizer_prompt(state.input_text, action_results_str)
            
            # Call Ollama
            response = self._call_ollama(full_prompt)
            
            # Emit llm_message event
            llm_event = LLMMessageEvent(
                type=AgentEventType.LLM_MESSAGE,
                node="synthesizer",
                content=response
            )
            state.add_event(llm_event)
            
            # Set final message
            state.final_message = response
            
            # Emit final_message event
            final_message_event = FinalMessageEvent(type=AgentEventType.FINAL_MESSAGE, content=response)
            state.add_event(final_message_event)
            
            # Emit run_completed event
            run_completed_event = RunCompletedEvent(type=AgentEventType.RUN_COMPLETED, status="ok")
            state.add_event(run_completed_event)
            
            return state
            
        except Exception as e:
            logger.error(f"Error in synthesizer_llm: {str(e)}")
            # Fallback response
            fallback_response = "I'm sorry, I encountered an error processing your request. Please try again."
            state.final_message = fallback_response
            
            # Emit events
            final_message_event = FinalMessageEvent(type=AgentEventType.FINAL_MESSAGE, content=fallback_response)
            state.add_event(final_message_event)
            
            run_completed_event = RunCompletedEvent(type=AgentEventType.RUN_COMPLETED, status="error", error=str(e))
            state.add_event(run_completed_event)
            
            return state
    
    def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API with the given prompt"""
        try:
            payload = {
                "model": self.config["model"],
                "prompt": prompt,
                "stream": False,
                "options": self.config.get("options", {})
            }
            
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except Exception as e:
            logger.error(f"Ollama API call failed: {str(e)}")
            raise
