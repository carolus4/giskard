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
        """Node 2: Call LLM to plan actions"""
        try:
            # Load planner prompt
            with open('/Users/charlesdupont/Dev/giskard/prompts/planner_v1.0.txt', 'r') as f:
                planner_prompt = f.read()
            
            # Prepare the prompt with user input
            full_prompt = f"{planner_prompt}\n\nUser: \"{state.input_text}\"\nResponse:"
            
            # Call Ollama
            response = self._call_ollama(full_prompt)
            
            # Emit llm_message event
            llm_event = LLMMessageEvent(
                type=AgentEventType.LLM_MESSAGE,
                node="planner",
                content=response
            )
            state.add_event(llm_event)
            
            # Parse the JSON response
            try:
                # Clean up the response - remove markdown code blocks if present
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]  # Remove ```
                cleaned_response = cleaned_response.strip()
                
                planner_output = json.loads(cleaned_response)
                state.planner_output = planner_output
                state.actions_to_execute = planner_output.get("actions", [])
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse planner JSON: {str(e)}")
                logger.error(f"Response was: {response}")
                # Fallback to no_op if parsing fails
                state.planner_output = {
                    "assistant_text": "I'm sorry, I had trouble understanding your request.",
                    "actions": [{"name": "no_op", "args": {}}]
                }
                state.actions_to_execute = [{"name": "no_op", "args": {}}]
            
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
        """Node 3: Execute actions"""
        try:
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
                
                # Execute the action
                success, result = self.action_executor.execute_action(action_name, action_args)
                
                # Emit action_result event
                action_result_event = ActionResultEvent(
                    type=AgentEventType.ACTION_RESULT,
                    name=action_name,
                    ok=success,
                    result=result if success else None,
                    error=result.get("error") if not success else None
                )
                state.add_event(action_result_event)
                
                # Store result
                action_results.append({
                    "name": action_name,
                    "ok": success,
                    "result": result if success else None,
                    "error": result.get("error") if not success else None
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
            # Load synthesizer prompt
            with open('/Users/charlesdupont/Dev/giskard/prompts/synthesizer_v1.0.txt', 'r') as f:
                synthesizer_prompt = f.read()
            
            # Prepare the prompt with context
            action_results_str = json.dumps(state.action_results, indent=2)
            # Use string replacement instead of format to avoid issues with quotes
            full_prompt = synthesizer_prompt.replace("{user_input}", state.input_text)
            full_prompt = full_prompt.replace("{action_results}", action_results_str)
            
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
