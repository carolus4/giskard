"""
LangGraph-based orchestrator for Giskard agent
"""
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_ollama import OllamaLLM
import json
import logging
from .actions.actions import ActionExecutor

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    input_text: str
    session_id: Optional[str]
    domain: Optional[str]
    planner_output: Optional[Dict[str, Any]]
    actions_to_execute: List[Dict[str, Any]]
    action_results: List[Dict[str, Any]]
    final_message: Optional[str]


class LangGraphOrchestrator:
    """LangGraph-based orchestrator with proper state management"""
    
    def __init__(self):
        self.llm = OllamaLLM(model="gemma3:4b", base_url="http://localhost:11434")
        self.action_executor = ActionExecutor()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("ingest_user_input", self._ingest_user_input)
        workflow.add_node("planner_llm", self._planner_llm)
        workflow.add_node("action_exec", self._action_exec)
        workflow.add_node("synthesizer_llm", self._synthesizer_llm)
        
        # Define the flow
        workflow.set_entry_point("ingest_user_input")
        workflow.add_edge("ingest_user_input", "planner_llm")
        workflow.add_edge("planner_llm", "action_exec")
        workflow.add_edge("action_exec", "synthesizer_llm")
        workflow.add_edge("synthesizer_llm", END)
        
        return workflow.compile()
    
    def _ingest_user_input(self, state: AgentState) -> AgentState:
        """Node 1: Ingest user input"""
        logger.info(f"Processing input: {state['input_text']}")
        
        # Add user message to conversation
        state["messages"].append(HumanMessage(content=state["input_text"]))
        
        return state
    
    def _planner_llm(self, state: AgentState) -> AgentState:
        """Node 2: Plan actions using LLM"""
        try:
            # Load planner prompt
            with open('/Users/charlesdupont/Dev/giskard/prompts/planner_v1.0.txt', 'r') as f:
                planner_prompt = f.read()
            
            # Create system message with planner prompt
            system_msg = SystemMessage(content=planner_prompt)
            user_msg = HumanMessage(content=state["input_text"])
            
            # Call LLM
            messages = [system_msg, user_msg]
            response = self.llm.invoke(messages)
            
            # Add AI message to conversation
            state["messages"].append(AIMessage(content=response))
            
            # Parse JSON response
            try:
                # Clean response
                cleaned_response = response.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()
                
                planner_output = json.loads(cleaned_response)
                state["planner_output"] = planner_output
                state["actions_to_execute"] = planner_output.get("actions", [])
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse planner JSON: {str(e)}")
                logger.error(f"Response was: {response}")
                # Fallback
                state["planner_output"] = {
                    "assistant_text": "I'm sorry, I had trouble understanding your request.",
                    "actions": [{"name": "no_op", "args": {}}]
                }
                state["actions_to_execute"] = [{"name": "no_op", "args": {}}]
            
            return state
            
        except Exception as e:
            logger.error(f"Error in planner_llm: {str(e)}")
            # Fallback
            state["planner_output"] = {
                "assistant_text": "I'm sorry, I encountered an error processing your request.",
                "actions": [{"name": "no_op", "args": {}}]
            }
            state["actions_to_execute"] = [{"name": "no_op", "args": {}}]
            return state
    
    def _action_exec(self, state: AgentState) -> AgentState:
        """Node 3: Execute actions"""
        try:
            action_results = []
            
            for action in state["actions_to_execute"]:
                action_name = action.get("name", "no_op")
                action_args = action.get("args", {})
                
                logger.info(f"Executing action: {action_name} with args: {action_args}")
                
                # Execute the action
                success, result = self.action_executor.execute_action(action_name, action_args)
                
                # Store result
                action_results.append({
                    "name": action_name,
                    "ok": success,
                    "result": result if success else None,
                    "error": result.get("error") if not success else None
                })
            
            state["action_results"] = action_results
            return state
            
        except Exception as e:
            logger.error(f"Error in action_exec: {str(e)}")
            state["action_results"] = [{
                "name": "error",
                "ok": False,
                "result": None,
                "error": str(e)
            }]
            return state
    
    def _synthesizer_llm(self, state: AgentState) -> AgentState:
        """Node 4: Synthesize final response"""
        try:
            # Load synthesizer prompt
            with open('/Users/charlesdupont/Dev/giskard/prompts/synthesizer_v1.0.txt', 'r') as f:
                synthesizer_prompt = f.read()
            
            # Prepare context
            action_results_str = json.dumps(state["action_results"], indent=2)
            full_prompt = synthesizer_prompt.replace("{user_input}", state["input_text"])
            full_prompt = full_prompt.replace("{action_results}", action_results_str)
            
            # Create messages
            system_msg = SystemMessage(content=full_prompt)
            messages = [system_msg]
            
            # Call LLM
            response = self.llm.invoke(messages)
            
            # Add AI message to conversation
            state["messages"].append(AIMessage(content=response))
            state["final_message"] = response
            
            return state
            
        except Exception as e:
            logger.error(f"Error in synthesizer_llm: {str(e)}")
            fallback_response = "I'm sorry, I encountered an error processing your request. Please try again."
            state["final_message"] = fallback_response
            state["messages"].append(AIMessage(content=fallback_response))
            return state
    
    def run(self, input_text: str, session_id: str = None, domain: str = None) -> Dict[str, Any]:
        """Run the LangGraph workflow"""
        try:
            # Initialize state
            initial_state = AgentState(
                messages=[],
                input_text=input_text,
                session_id=session_id,
                domain=domain,
                planner_output=None,
                actions_to_execute=[],
                action_results=[],
                final_message=None
            )
            
            # Run the graph
            final_state = self.graph.invoke(initial_state)
            
            # Convert to response format
            return {
                "success": True,
                "message": "Agent step completed",
                "final_message": final_state["final_message"],
                "state_patch": {
                    "session_id": session_id,
                    "domain": domain,
                    "messages": [msg.content for msg in final_state["messages"]]
                }
            }
            
        except Exception as e:
            logger.error(f"LangGraph execution failed: {str(e)}")
            return {
                "success": False,
                "message": f"Agent step failed: {str(e)}",
                "final_message": "I'm sorry, I encountered an error processing your request. Please try again.",
                "state_patch": {
                    "session_id": session_id,
                    "domain": domain
                }
            }
