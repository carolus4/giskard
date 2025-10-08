"""
Idiomatic LangGraph orchestrator using proper LCEL patterns and structured output
"""
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableParallel
import json
import logging
from datetime import datetime

from .tools.router import Router
from .tools.tool_registry import ToolRegistry
from .config.router_config import RouterConfigManager
from models.task_db import AgentStepDB

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the LangGraph agent"""
    messages: Annotated[List[BaseMessage], add_messages]
    input_text: str
    session_id: Optional[str]
    domain: Optional[str]
    trace_id: Optional[str]
    current_step: int
    router_output: Optional[Dict[str, Any]]
    tool_name: Optional[str]
    tool_args: Optional[Dict[str, Any]]
    tool_result: Optional[str]
    final_message: Optional[str]


class Orchestrator:
    """
    LangGraph orchestrator using proper LCEL patterns,
    structured output, and LangChain best practices
    """
    
    def __init__(self, config_manager: Optional[RouterConfigManager] = None):
        """
        Initialize the orchestrator with proper dependency injection
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager or RouterConfigManager.from_env()
        
        # Initialize components with configuration
        model_config = self.config_manager.get_model_config()
        api_config = self.config_manager.get_api_config()
        router_config = self.config_manager.get_router_config()
        
        self.router = Router(
            model_name=model_config["model_name"],
            base_url=model_config["base_url"],
            api_base_url=api_config["base_url"],
            prompt_file=router_config["prompt_file"]
        )
        
        self.tool_registry = ToolRegistry(api_config["base_url"])
        self.tools = self.tool_registry.get_tools()
        self.tool_node = ToolNode(self.tools)
        
        # Build the graph
        self.graph = self._build_graph()
        
        # Get configuration values
        router_config = self.config_manager.get_router_config()
        self.workflow_timeout = router_config["timeout_seconds"]
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow using proper LCEL patterns"""
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes using LCEL patterns
        workflow.add_node("ingest_user_input", self._create_ingest_chain())
        workflow.add_node("router_llm", self._create_router_chain())
        workflow.add_node("tool_exec", self._create_tool_execution_chain())
        workflow.add_node("synthesizer_llm", self._create_synthesizer_chain())
        
        # Define the flow
        workflow.set_entry_point("ingest_user_input")
        workflow.add_edge("ingest_user_input", "router_llm")
        workflow.add_edge("router_llm", "tool_exec")
        workflow.add_edge("tool_exec", "synthesizer_llm")
        workflow.add_edge("synthesizer_llm", END)
        
        return workflow.compile()
    
    def _create_ingest_chain(self):
        """Create the ingest chain using LCEL"""
        def ingest_user_input(state: AgentState) -> AgentState:
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
        
        return RunnableLambda(ingest_user_input)
    
    def _create_router_chain(self):
        """Create the router chain using LCEL"""
        def router_llm(state: AgentState) -> AgentState:
            """Node 2: Route to appropriate tool using structured router"""
            # Increment step counter
            state["current_step"] += 1

            input_data = {
                "input_text": state["input_text"],
                "messages_count": len(state["messages"])
            }

            try:
                # Use the idiomatic router to get tool decision
                router_output = self.router.plan_actions(state["input_text"])
                
                # Store router output in state
                state["router_output"] = router_output
                state["tool_name"] = router_output["tool_name"]
                state["tool_args"] = router_output["tool_args"]

                # Add assistant message to conversation
                state["messages"].append(AIMessage(content=router_output["assistant_text"]))

                output_data = {
                    "router_output": router_output,
                    "tool_name": state["tool_name"],
                    "tool_args": state["tool_args"],
                    "routing_success": True
                }

                self._log_node(state, "router_llm", input_data, output_data)
                return state

            except Exception as e:
                logger.error(f"Error in router_llm: {str(e)}")
                # Fallback
                state["router_output"] = {
                    "assistant_text": "I'm sorry, I encountered an error processing your request.",
                    "tool_name": "no_op",
                    "tool_args": {}
                }
                state["tool_name"] = "no_op"
                state["tool_args"] = {}

                output_data = {
                    "error": str(e),
                    "fallback_used": True
                }

                self._log_node(state, "router_llm", input_data, output_data, error=str(e))
                return state
        
        return RunnableLambda(router_llm)
    
    def _create_tool_execution_chain(self):
        """Create the tool execution chain using LCEL"""
        def tool_exec(state: AgentState) -> AgentState:
            """Node 3: Execute tool using proper error handling"""
            # Increment step counter
            state["current_step"] += 1

            input_data = {
                "tool_name": state["tool_name"],
                "tool_args": state["tool_args"]
            }

            try:
                # Execute the tool using the router's execute_tool method
                tool_result = self.router.execute_tool(state["tool_name"], state["tool_args"])
                state["tool_result"] = tool_result

                # Add tool result to conversation
                state["messages"].append(AIMessage(content=tool_result))

                output_data = {
                    "tool_name": state["tool_name"],
                    "tool_args": state["tool_args"],
                    "tool_result": tool_result,
                    "execution_success": True
                }

                self._log_node(state, "tool_exec", input_data, output_data)
                return state

            except Exception as e:
                logger.error(f"Error in tool_exec: {str(e)}")
                error_msg = f"❌ Error executing {state['tool_name']}: {str(e)}"
                state["tool_result"] = error_msg
                state["messages"].append(AIMessage(content=error_msg))

                output_data = {
                    "error": str(e),
                    "tool_result": error_msg,
                    "execution_success": False
                }

                self._log_node(state, "tool_exec", input_data, output_data, error=str(e))
                return state
        
        return RunnableLambda(tool_exec)
    
    def _create_synthesizer_chain(self):
        """Create the synthesizer chain using LCEL"""
        def synthesizer_llm(state: AgentState) -> AgentState:
            """Node 4: Synthesize final response"""
            # Increment step counter
            state["current_step"] += 1

            input_data = {
                "tool_result": state.get("tool_result"),
                "router_output": state.get("router_output"),
                "input_text": state["input_text"]
            }

            try:
                # Load synthesizer prompt from registry
                from config.prompts import get_synthesizer_prompt
                tool_result_str = state.get("tool_result", "No result")
                full_prompt = get_synthesizer_prompt(state["input_text"], tool_result_str)

                # Create messages
                system_msg = SystemMessage(content=full_prompt)
                messages = [system_msg]

                # Call LLM using the router's LLM instance
                response = self.router.llm.invoke(messages)

                # Add AI message to conversation
                state["messages"].append(AIMessage(content=response))
                state["final_message"] = response

                output_data = {
                    "final_message": response,
                    "messages_count": len(state["messages"]),
                    "synthesis_success": True
                }

                self._log_node(state, "synthesizer_llm", input_data, output_data,
                              rendered_prompt=full_prompt, 
                              llm_input={"messages": [{"type": msg.__class__.__name__, "content": msg.content} for msg in messages]},
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
        
        return RunnableLambda(synthesizer_llm)
    
    def _log_node(self, state: AgentState, step_type: str, input_data: Dict[str, Any],
                  output_data: Dict[str, Any] = None, rendered_prompt: str = None,
                  llm_input: Dict[str, Any] = None, llm_output: str = None, error: str = None):
        """Log each node execution to database"""
        # Ensure trace_id and step_number are set
        trace_id = state.get("trace_id") or state.get("session_id") or "default-trace"
        step_number = state.get("current_step", 1)

        # Create database entry
        AgentStepDB.create(
            trace_id=trace_id,
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
        logger.info(f"[{step_type}] Trace: {trace_id}, Step: {step_number}")
        if output_data:
            logger.info(f"[{step_type}] Output: {json.dumps(output_data, indent=2)}")
        if error:
            logger.error(f"[{step_type}] Error: {error}")
    
    def run(self, input_text: str, session_id: str = None, domain: str = None) -> Dict[str, Any]:
        """Run the LangGraph workflow with proper timeout handling"""
        import threading
        import time

        # Generate trace_id if not provided
        trace_id = session_id or f"chat-{int(time.time())}"

        # Get next step number for this trace
        next_step = AgentStepDB.get_next_step_number(trace_id)

        # Log workflow start
        initial_state = AgentState(
            messages=[],
            input_text=input_text,
            session_id=session_id,
            domain=domain,
            trace_id=trace_id,
            current_step=next_step,
            router_output=None,
            tool_name=None,
            tool_args=None,
            tool_result=None,
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
                    "trace_id": trace_id,
                    "state_patch": {
                        "session_id": session_id,
                        "domain": domain,
                        "trace_id": trace_id,
                        "current_step": next_step
                    }
                }
            
            # Success - convert to response format
            final_state = result["final_state"]

            return {
                "success": True,
                "message": "Agent step completed",
                "final_message": final_state["final_message"],
                "trace_id": final_state["trace_id"],
                "current_step": final_state["current_step"],
                "state_patch": {
                    "session_id": session_id,
                    "domain": domain,
                    "trace_id": final_state["trace_id"],
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
                "trace_id": trace_id,
                "state_patch": {
                    "session_id": session_id,
                    "domain": domain,
                    "trace_id": trace_id,
                    "current_step": next_step
                }
            }
    
    def create_workflow_chain(self):
        """
        Create a complete workflow chain using LCEL patterns
        
        Returns:
            Complete workflow chain
        """
        return self.router.create_complete_workflow()
    
    def get_router_info(self) -> Dict[str, Any]:
        """Get information about the router configuration"""
        return {
            "available_tools": self.router.get_available_tools(),
            "tool_descriptions": self.router.get_tool_descriptions(),
            "model_name": self.router.model_name,
            "base_url": self.router.base_url
        }
