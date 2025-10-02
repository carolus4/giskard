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
from datetime import datetime
from .actions.actions import ActionExecutor
from models.task_db import AgentStepDB

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    input_text: str
    session_id: Optional[str]
    domain: Optional[str]
    thread_id: Optional[str]
    current_step: int
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
        # Set a reasonable timeout for the entire workflow (90 seconds)
        self.workflow_timeout = 90
    
    def _log_node(self, state: AgentState, step_type: str, input_data: Dict[str, Any],
                  output_data: Dict[str, Any] = None, rendered_prompt: str = None,
                  llm_input: Dict[str, Any] = None, llm_output: str = None, error: str = None):
        """Log each node execution to database"""
        # Ensure thread_id and step_number are set
        thread_id = state.get("thread_id") or state.get("session_id") or "default-thread"
        step_number = state.get("current_step", 1)

        # Create database entry
        AgentStepDB.create(
            thread_id=thread_id,
            step_number=step_number,
            step_type=step_type,
            input_data=input_data,
            output_data=output_data or {},
            rendered_prompt=rendered_prompt,
            llm_input=llm_input or {},
            llm_output=llm_output,
            error=error
        )

        # Also log to console for debugging
        logger.info(f"[{step_type}] Thread: {thread_id}, Step: {step_number}")
        if output_data:
            logger.info(f"[{step_type}] Output: {json.dumps(output_data, indent=2)}")
        if error:
            logger.error(f"[{step_type}] Error: {error}")
    
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
        input_data = {
            "input_text": state["input_text"],
            "session_id": state.get("session_id"),
            "domain": state.get("domain")
        }

        logger.info(f"Processing input: {state['input_text']}")

        # Add user message to conversation
        state["messages"].append(HumanMessage(content=state["input_text"]))

        output_data = {
            "messages_count": len(state["messages"]),
            "user_message_added": True
        }

        self._log_node(state, "ingest_user_input", input_data, output_data)
        return state
    
    def _planner_llm(self, state: AgentState) -> AgentState:
        """Node 2: Plan actions using LLM"""
        # Increment step counter
        state["current_step"] += 1

        input_data = {
            "input_text": state["input_text"],
            "messages_count": len(state["messages"])
        }

        try:
            # Load planner prompt from registry
            from config.prompts import get_planner_prompt
            planner_prompt = get_planner_prompt()

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

                output_data = {
                    "llm_response": response,
                    "planner_output": planner_output,
                    "actions_to_execute": state["actions_to_execute"],
                    "parsing_success": True
                }

            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse planner JSON: {str(e)}")
                logger.error(f"Response was: {response}")
                # Fallback
                state["planner_output"] = {
                    "assistant_text": "I'm sorry, I had trouble understanding your request.",
                    "actions": [{"name": "no_op", "args": {}}]
                }
                state["actions_to_execute"] = [{"name": "no_op", "args": {}}]

                output_data = {
                    "llm_response": response,
                    "parsing_success": False,
                    "error": str(e),
                    "fallback_used": True
                }

            self._log_node(state, "planner_llm", input_data, output_data,
                          rendered_prompt=planner_prompt, llm_input={"messages": [msg.content for msg in messages]},
                          llm_output=response)
            return state

        except Exception as e:
            logger.error(f"Error in planner_llm: {str(e)}")
            # Fallback
            state["planner_output"] = {
                "assistant_text": "I'm sorry, I encountered an error processing your request.",
                "actions": [{"name": "no_op", "args": {}}]
            }
            state["actions_to_execute"] = [{"name": "no_op", "args": {}}]

            output_data = {
                "error": str(e),
                "fallback_used": True
            }

            self._log_node(state, "planner_llm", input_data, output_data,
                          error=str(e))
            return state
    
    def _action_exec(self, state: AgentState) -> AgentState:
        """Node 3: Execute actions"""
        # Increment step counter
        state["current_step"] += 1

        input_data = {
            "actions_to_execute": state["actions_to_execute"]
        }

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

            output_data = {
                "action_results": action_results,
                "actions_executed": len(action_results),
                "successful_actions": len([r for r in action_results if r["ok"]]),
                "failed_actions": len([r for r in action_results if not r["ok"]])
            }

            self._log_node(state, "action_exec", input_data, output_data)
            return state

        except Exception as e:
            logger.error(f"Error in action_exec: {str(e)}")
            state["action_results"] = [{
                "name": "error",
                "ok": False,
                "result": None,
                "error": str(e)
            }]

            output_data = {
                "error": str(e),
                "action_results": state["action_results"]
            }

            self._log_node(state, "action_exec", input_data, output_data, error=str(e))
            return state
    
    def _synthesizer_llm(self, state: AgentState) -> AgentState:
        """Node 4: Synthesize final response"""
        # Increment step counter
        state["current_step"] += 1

        input_data = {
            "action_results": state["action_results"],
            "planner_output": state.get("planner_output"),
            "input_text": state["input_text"]
        }

        try:
            # Load synthesizer prompt from registry
            from config.prompts import get_synthesizer_prompt
            action_results_str = json.dumps(state["action_results"], indent=2)
            full_prompt = get_synthesizer_prompt(state["input_text"], action_results_str)

            # Create messages
            system_msg = SystemMessage(content=full_prompt)
            messages = [system_msg]

            # Call LLM
            response = self.llm.invoke(messages)

            # Add AI message to conversation
            state["messages"].append(AIMessage(content=response))
            state["final_message"] = response

            output_data = {
                "final_message": response,
                "messages_count": len(state["messages"]),
                "synthesis_success": True
            }

            self._log_node(state, "synthesizer_llm", input_data, output_data,
                          rendered_prompt=full_prompt, llm_input={"messages": [msg.content for msg in messages]},
                          llm_output=response)
            return state

        except Exception as e:
            logger.error(f"Error in synthesizer_llm: {str(e)}")
            fallback_response = "I'm sorry, I encountered an error processing your request. Please try again."
            state["final_message"] = fallback_response
            state["messages"].append(AIMessage(content=fallback_response))

            output_data = {
                "error": str(e),
                "fallback_response": fallback_response,
                "synthesis_success": False
            }

            self._log_node(state, "synthesizer_llm", input_data, output_data, error=str(e))
            return state
    
    def run(self, input_text: str, session_id: str = None, domain: str = None) -> Dict[str, Any]:
        """Run the LangGraph workflow with timeout handling"""
        import threading
        import time

        # Generate thread_id if not provided
        thread_id = session_id or f"chat-{int(time.time())}"

        # Get next step number for this thread
        next_step = AgentStepDB.get_next_step_number(thread_id)

        # Log workflow start
        initial_state = AgentState(
            messages=[],
            input_text=input_text,
            session_id=session_id,
            domain=domain,
            thread_id=thread_id,
            current_step=next_step,
            planner_output=None,
            actions_to_execute=[],
            action_results=[],
            final_message=None
        )

        self._log_node(initial_state, "workflow_start", {
            "input_text": input_text,
            "session_id": session_id,
            "domain": domain
        })

        try:
            
            # Run the graph with timeout using threading
            result = {"success": False, "final_state": None, "error": None}
            
            def run_graph():
                try:
                    final_state = self.graph.invoke(initial_state)
                    result["success"] = True
                    result["final_state"] = final_state
                except Exception as e:
                    result["error"] = str(e)
            
            # Start the graph execution in a thread
            thread = threading.Thread(target=run_graph)
            thread.daemon = True
            thread.start()
            
            # Wait for completion with timeout
            thread.join(timeout=self.workflow_timeout)
            
            if thread.is_alive():
                # Timeout occurred
                logger.error("LangGraph execution timed out")
                return {
                    "success": False,
                    "message": "Agent step timed out",
                    "final_message": "I'm taking longer than expected to process your request. Please try with a simpler request or try again later.",
                    "state_patch": {
                        "session_id": session_id,
                        "domain": domain
                    }
                }
            
            if not result["success"]:
                # Error occurred during execution
                logger.error(f"LangGraph execution failed: {result['error']}")
                return {
                    "success": False,
                    "message": f"Agent step failed: {result['error']}",
                    "final_message": "I'm sorry, I encountered an error processing your request. Please try again.",
                    "thread_id": thread_id,
                    "state_patch": {
                        "session_id": session_id,
                        "domain": domain,
                        "thread_id": thread_id,
                        "current_step": next_step
                    }
                }
            
            # Success - convert to response format
            final_state = result["final_state"]

            return {
                "success": True,
                "message": "Agent step completed",
                "final_message": final_state["final_message"],
                "thread_id": final_state["thread_id"],
                "current_step": final_state["current_step"],
                "state_patch": {
                    "session_id": session_id,
                    "domain": domain,
                    "thread_id": final_state["thread_id"],
                    "current_step": final_state["current_step"],
                    "messages": [msg.content for msg in final_state["messages"]]
                }
            }
            
        except Exception as e:
            logger.error(f"LangGraph execution failed: {str(e)}")
            return {
                "success": False,
                "message": f"Agent step failed: {str(e)}",
                "final_message": "I'm sorry, I encountered an error processing your request. Please try again.",
                "thread_id": thread_id,
                "state_patch": {
                    "session_id": session_id,
                    "domain": domain,
                    "thread_id": thread_id,
                    "current_step": next_step
                }
            }
