"""
Idiomatic LangChain router using proper LCEL patterns and structured output
"""
import logging
import os
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableParallel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_ollama import OllamaLLM
from .tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class RouterDecision(BaseModel):
    """Structured output for router decisions"""
    assistant_text: str = Field(description="Response to the user")
    tool_name: str = Field(description="Name of the tool to execute")
    tool_args: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool")


class IdiomaticRouter:
    """
    Idiomatic LangChain router using proper LCEL patterns, structured output,
    and LangChain best practices
    """
    
    def __init__(self, 
                 model_name: str = "gemma3:4b",
                 base_url: str = "http://localhost:11434",
                 api_base_url: str = "http://localhost:5001",
                 prompt_file: str = "prompts/router_v1.1.txt"):
        """
        Initialize the router with proper dependency injection
        
        Args:
            model_name: Ollama model name
            base_url: Ollama base URL
            api_base_url: API base URL for tool registry
            prompt_file: Path to the prompt template file
        """
        self.model_name = model_name
        self.base_url = base_url
        self.api_base_url = api_base_url
        self.prompt_file = prompt_file
        
        # Initialize components
        self.llm = OllamaLLM(model=model_name, base_url=base_url)
        self.tool_registry = ToolRegistry(api_base_url)
        self.tools = self.tool_registry.get_tools()
        
        # Setup the router chain
        self._setup_router_chain()
    
    def _setup_router_chain(self):
        """Setup the router using proper LCEL patterns"""
        # Load and format the prompt template
        self.prompt_template = self._load_prompt_template()
        
        # Create the prompt with proper formatting
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self.prompt_template),
            ("human", "{input}")
        ])
        
        # Create the parser for structured output
        self.parser = PydanticOutputParser(pydantic_object=RouterDecision)
        
        # Build the router chain using LCEL
        self.router_chain = (
            self.prompt
            | self.llm
            | RunnableLambda(self._parse_llm_response)
            | RunnableLambda(self._validate_router_decision)
        )
    
    def _load_prompt_template(self) -> str:
        """Load and format the router prompt template"""
        prompt_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            self.prompt_file
        )
        
        try:
            with open(prompt_file, 'r') as f:
                template = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Router prompt file not found at: {prompt_file}")
        
        # Format the template with current context
        current_datetime = datetime.now().isoformat()
        tool_descriptions = self.tool_registry.get_tool_descriptions()
        
        return template.format(
            current_datetime=current_datetime,
            tool_descriptions=tool_descriptions
        )
    
    def _parse_llm_response(self, response: Union[str, AIMessage]) -> Dict[str, Any]:
        """
        Parse LLM response with proper error handling
        
        Args:
            response: LLM response (string or AIMessage)
            
        Returns:
            Parsed response dictionary
        """
        try:
            # Extract content from response
            if hasattr(response, 'content'):
                content = response.content
            else:
                content = str(response)
            
            # Clean the response
            cleaned_content = self._clean_json_response(content)
            
            # Parse JSON
            parsed_data = json.loads(cleaned_content)
            
            # Validate required fields
            required_fields = ["assistant_text", "tool_name", "tool_args"]
            if not all(field in parsed_data for field in required_fields):
                raise ValueError(f"Missing required fields. Expected: {required_fields}")
            
            return parsed_data
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            logger.error(f"Response content: {content}")
            raise ValueError(f"Failed to parse router response: {str(e)}")
    
    def _clean_json_response(self, content: str) -> str:
        """Clean JSON response by removing markdown code blocks"""
        cleaned = content.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        return cleaned.strip()
    
    def _validate_router_decision(self, decision_data: Dict[str, Any]) -> RouterDecision:
        """
        Validate and create RouterDecision object
        
        Args:
            decision_data: Parsed decision data
            
        Returns:
            Validated RouterDecision object
        """
        try:
            # Validate that the tool exists
            tool = self.tool_registry.get_tool_by_name(decision_data["tool_name"])
            if not tool:
                logger.warning(f"Unknown tool: {decision_data['tool_name']}, falling back to no_op")
                return RouterDecision(
                    assistant_text="I'm sorry, I had trouble understanding your request.",
                    tool_name="no_op",
                    tool_args={}
                )
            
            # Create and validate the decision object
            decision = RouterDecision(**decision_data)
            return decision
            
        except Exception as e:
            logger.error(f"Error validating router decision: {str(e)}")
            # Return fallback decision
            return RouterDecision(
                assistant_text="I'm sorry, I encountered an error processing your request.",
                tool_name="no_op",
                tool_args={}
            )
    
    def plan_actions(self, user_input: str) -> Dict[str, Any]:
        """
        Plan actions using the idiomatic router approach
        
        Args:
            user_input: The user's input text
            
        Returns:
            Dictionary with assistant_text, tool_name, and tool_args
        """
        try:
            # Execute the router chain
            decision = self.router_chain.invoke({"input": user_input})
            
            # Convert to dictionary format for compatibility
            return {
                "assistant_text": decision.assistant_text,
                "tool_name": decision.tool_name,
                "tool_args": decision.tool_args
            }
            
        except Exception as e:
            logger.error(f"Error in router planning: {str(e)}")
            # Return fallback decision
            return {
                "assistant_text": "I'm sorry, I encountered an error processing your request.",
                "tool_name": "no_op",
                "tool_args": {}
            }
    
    def execute_tool(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """
        Execute a tool with the given arguments using proper error handling
        
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
            
            # Execute the tool using LangChain's invoke method
            # The tool expects the arguments to be passed as a dictionary
            result = tool.invoke(tool_args)
            return result
            
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {str(e)}")
            return f"❌ Error executing {tool_name}: {str(e)}"
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names"""
        return [tool.name for tool in self.tools]
    
    def get_tool_descriptions(self) -> str:
        """Get formatted tool descriptions"""
        return self.tool_registry.get_tool_descriptions()
    
    def create_router_chain_with_fallback(self):
        """
        Create a router chain with proper fallback handling using LCEL
        
        Returns:
            Runnable chain with fallback handling
        """
        def handle_router_error(inputs: Dict[str, Any]) -> RouterDecision:
            """Handle router errors with fallback"""
            try:
                return self.router_chain.invoke(inputs)
            except Exception as e:
                logger.error(f"Router chain error: {str(e)}")
                return RouterDecision(
                    assistant_text="I'm sorry, I encountered an error processing your request.",
                    tool_name="no_op",
                    tool_args={}
                )
        
        return RunnableLambda(handle_router_error)
    
    def create_tool_execution_chain(self):
        """
        Create a tool execution chain using LCEL
        
        Returns:
            Runnable chain for tool execution
        """
        def execute_tool_with_fallback(inputs: Dict[str, Any]) -> str:
            """Execute tool with proper error handling"""
            try:
                tool_name = inputs.get("tool_name")
                tool_args = inputs.get("tool_args", {})
                return self.execute_tool(tool_name, tool_args)
            except Exception as e:
                logger.error(f"Tool execution error: {str(e)}")
                return f"❌ Error executing tool: {str(e)}"
        
        return RunnableLambda(execute_tool_with_fallback)
    
    def create_complete_workflow(self):
        """
        Create a complete workflow chain using LCEL patterns
        
        Returns:
            Complete workflow chain
        """
        # Create the complete workflow
        workflow = RunnableParallel({
            "router_decision": self.router_chain,
            "original_input": RunnablePassthrough()
        }) | RunnableLambda(self._combine_router_and_execution)
        
        return workflow
    
    def _combine_router_and_execution(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine router decision with tool execution
        
        Args:
            inputs: Dictionary containing router_decision and original_input
            
        Returns:
            Combined result dictionary
        """
        try:
            decision = inputs["router_decision"]
            user_input = inputs["original_input"]["input"]
            
            # Execute the tool
            tool_result = self.execute_tool(decision.tool_name, decision.tool_args)
            
            return {
                "assistant_text": decision.assistant_text,
                "tool_name": decision.tool_name,
                "tool_args": decision.tool_args,
                "tool_result": tool_result,
                "user_input": user_input
            }
            
        except Exception as e:
            logger.error(f"Error in workflow combination: {str(e)}")
            return {
                "assistant_text": "I'm sorry, I encountered an error processing your request.",
                "tool_name": "no_op",
                "tool_args": {},
                "tool_result": f"❌ Error: {str(e)}",
                "user_input": inputs.get("original_input", {}).get("input", "")
            }
