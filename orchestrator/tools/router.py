"""
Router-based planner using LangChain tools
"""
import logging
import json
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import Tool
from langchain_ollama import OllamaLLM
from .tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class RouterPlanner:
    """Router-based planner that uses LangChain tools for action selection"""
    
    def __init__(self, base_url: str = "http://localhost:5001"):
        self.llm = OllamaLLM(model="gemma3:4b", base_url="http://localhost:11434")
        self.tool_registry = ToolRegistry(base_url)
        self.tools = self.tool_registry.get_tools()
    
    def get_router_prompt(self) -> str:
        """Get the router prompt with current datetime context"""
        from datetime import datetime
        import os
        
        # Get current datetime in ISO format
        current_datetime = datetime.now().isoformat()
        
        # Get tool descriptions
        tool_descriptions = self.tool_registry.get_tool_descriptions()
        
        # Load prompt from file
        prompt_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "prompts", "router_v1.0.txt")
        
        try:
            with open(prompt_file, 'r') as f:
                prompt_template = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Router prompt file not found at: {prompt_file}. Please ensure the prompt file exists.")
        
        # Format the prompt with current datetime and tool descriptions
        return prompt_template.format(
            current_datetime=current_datetime,
            tool_descriptions=tool_descriptions
        )
    
    def plan_actions(self, user_input: str) -> Dict[str, Any]:
        """
        Plan actions using the router approach
        
        Args:
            user_input: The user's input text
            
        Returns:
            Dictionary with assistant_text, tool_name, and tool_args
        """
        try:
            # Get the router prompt
            router_prompt = self.get_router_prompt()
            
            # Create messages for the LLM
            system_msg = SystemMessage(content=router_prompt)
            user_msg = HumanMessage(content=user_input)
            messages = [system_msg, user_msg]
            
            # Call the LLM
            response = self.llm.invoke(messages)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse the JSON response
            try:
                # Clean up the response - remove markdown code blocks if present
                cleaned_response = response_text.strip()
                if cleaned_response.startswith("```json"):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.endswith("```"):
                    cleaned_response = cleaned_response[:-3]  # Remove ```
                cleaned_response = cleaned_response.strip()
                
                router_output = json.loads(cleaned_response)
                
                # Validate the response format
                if not all(key in router_output for key in ["assistant_text", "tool_name", "tool_args"]):
                    raise ValueError("Missing required fields in router output")
                
                # Validate that the tool exists
                tool = self.tool_registry.get_tool_by_name(router_output["tool_name"])
                if not tool:
                    raise ValueError(f"Unknown tool: {router_output['tool_name']}")
                
                return router_output
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse router JSON: {str(e)}")
                logger.error(f"Response was: {response_text}")
                # Fallback to no_op
                return {
                    "assistant_text": "I'm sorry, I had trouble understanding your request.",
                    "tool_name": "no_op",
                    "tool_args": {}
                }
            except ValueError as e:
                logger.error(f"Router validation error: {str(e)}")
                # Fallback to no_op
                return {
                    "assistant_text": "I'm sorry, I had trouble understanding your request.",
                    "tool_name": "no_op",
                    "tool_args": {}
                }
                
        except FileNotFoundError:
            # Re-raise FileNotFoundError as it indicates a configuration issue
            raise
        except Exception as e:
            logger.error(f"Error in router planning: {str(e)}")
            # Fallback to no_op
            return {
                "assistant_text": "I'm sorry, I encountered an error processing your request.",
                "tool_name": "no_op",
                "tool_args": {}
            }
    
    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Execute a tool with the given arguments
        
        Args:
            tool_name: Name of the tool to execute
            tool_args: Arguments for the tool
            
        Returns:
            Result string from the tool execution
        """
        try:
            tool = self.tool_registry.get_tool_by_name(tool_name)
            if not tool:
                return f"❌ Error: Unknown tool '{tool_name}'"
            
            # Execute the tool
            result = tool.func(**tool_args)
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return f"❌ Error executing {tool_name}: {str(e)}"
